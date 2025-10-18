from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any, Optional, Union

import requests
from dotenv import load_dotenv


DEFAULT_API_BASE_URL = "https://vorld-auth.onrender.com/api"

# Load .env if present (project root)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=False)


def _get_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


API_BASE_URL = _get_env("NEXT_PUBLIC_AUTH_SERVER_URL", DEFAULT_API_BASE_URL)
VORLD_APP_ID = _get_env("NEXT_PUBLIC_VORLD_APP_ID", "")


@dataclass
class ServiceResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class VorldAuthService:
    """Python port of the TypeScript VorldAuthService using requests.Session.

    - Uses SHA-256 to hash password before sending.
    - Sends 'x-vorld-app-id' header for app identification.
    - Maintains cookies via a persistent Session (withCredentials-like behavior).
    - Base URL and app id are read from env vars:
        * NEXT_PUBLIC_AUTH_SERVER_URL (default: http://localhost:3001/api)
        * NEXT_PUBLIC_VORLD_APP_ID (default: empty)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        app_id: Optional[str] = None,
        timeout: Union[int, float] = 15,
        *,
        debug: bool = False,
        hash_password: bool = True,
    ):
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.app_id = (app_id if app_id is not None else VORLD_APP_ID)
        self.timeout = timeout
        self.debug = debug
        self.hash_password = hash_password
        self.token: Optional[str] = None

        self.session = requests.Session()
        # Default headers for all requests
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "x-vorld-app-id": self.app_id,
            }
        )

    # Token helpers
    def set_bearer_token(self, token: Optional[str]) -> None:
        self.token = token
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        else:
            # remove header if token cleared
            self.session.headers.pop("Authorization", None)

    def _maybe_set_token_from_data(self, data: Any) -> None:
        if not isinstance(data, dict):
            return
        # Common token field names
        candidates = [
            "accessToken",
            "token",
            "access_token",
            "jwt",
            "idToken",
            "id_token",
        ]
        token = None
        for key in candidates:
            if key in data and isinstance(data[key], str) and data[key]:
                token = data[key]
                break
        if token is None and isinstance(data.get("data"), dict):
            inner = data["data"]
            for key in candidates:
                if key in inner and isinstance(inner[key], str) and inner[key]:
                    token = inner[key]
                    break
        if token:
            if self.debug:
                print("[auth] Detected bearer token in login response; setting Authorization header.")
            self.set_bearer_token(token)

    def _extract_error(self, resp: requests.Response, fallback: str) -> str:
        try:
            j = resp.json()
            msg = j.get("message") or j.get("error") or j.get("detail")
            if msg:
                return f"{msg} (status {resp.status_code})"
        except Exception:
            pass
        # fallback to text (truncate to avoid flooding logs)
        text = (resp.text or "").strip()
        if text:
            snippet = text if len(text) < 500 else text[:500] + "..."
            return f"{fallback} (status {resp.status_code}): {snippet}"
        return f"{fallback} (status {resp.status_code})"

    # Email/Password Authentication
    def login_with_email(self, email: str, password: str) -> ServiceResult:
        try:
            # Hash password with SHA-256 before sending to backend
            to_send = hashlib.sha256(password.encode("utf-8")).hexdigest() if self.hash_password else password

            if self.debug:
                print(f"[auth] POST {self.base_url}/auth/login")
            resp = self.session.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": to_send},
                timeout=self.timeout,
            )
            if resp.ok:
                data = None
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                # Auto-detect bearer token if provided by backend
                self._maybe_set_token_from_data(data)
                return ServiceResult(success=True, data=data)
            else:
                err = self._extract_error(resp, "Login failed")
                return ServiceResult(success=False, error=err)
        except requests.RequestException as exc:
            return ServiceResult(success=False, error=str(exc))

    def login_with_credentials(self, payload: dict, path: str = "/auth/login") -> ServiceResult:
        """Generic login method in case backend expects different field names.

        Example payloads:
        - {"username": "u", "password": "p"}
        - {"email": "e", "password": "p"}
        - {"identifier": "e or username", "password": "p"}
        - {"email": "e", "password": sha256(p)} if server expects client-side hashed
        """
        try:
            url = f"{self.base_url}{path}"
            if self.debug:
                print(f"[auth] POST {url}")
                print(f"[auth] Payload keys: {list(payload.keys())}")
            resp = self.session.post(url, json=payload, timeout=self.timeout)
            if resp.ok:
                data: Any
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                self._maybe_set_token_from_data(data)
                return ServiceResult(success=True, data=data)
            else:
                err = self._extract_error(resp, "Login failed")
                return ServiceResult(success=False, error=err)
        except requests.RequestException as exc:
            return ServiceResult(success=False, error=str(exc))

    def verify_otp(self, email: str, otp: str, path: str = "/auth/verify-otp") -> ServiceResult:
        """Verify an OTP code sent to the user's email. If a token is returned, set it.

        Args:
            email: The email used for login
            otp: One-time passcode (e.g., 6 digits)
            path: Endpoint path to verify OTP
        """
        try:
            url = f"{self.base_url}{path}"
            if self.debug:
                print(f"[auth] POST {url}")
            resp = self.session.post(url, json={"email": email, "otp": otp}, timeout=self.timeout)
            if resp.ok:
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                self._maybe_set_token_from_data(data)
                return ServiceResult(success=True, data=data)
            else:
                err = self._extract_error(resp, "OTP verification failed")
                return ServiceResult(success=False, error=err)
        except requests.RequestException as exc:
            return ServiceResult(success=False, error=str(exc))

    # Get User Profile
    def get_profile(self) -> ServiceResult:
        try:
            if self.debug:
                print(f"[auth] GET {self.base_url}/user/profile")
            resp = self.session.get(f"{self.base_url}/user/profile", timeout=self.timeout)
            if resp.ok:
                data = None
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                return ServiceResult(success=True, data=data)
            else:
                err = self._extract_error(resp, "Failed to get profile")
                return ServiceResult(success=False, error=err)
        except requests.RequestException as exc:
            return ServiceResult(success=False, error=str(exc))


__all__ = ["VorldAuthService", "ServiceResult"]
