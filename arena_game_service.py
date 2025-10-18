from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import requests
import socketio  # python-socketio client
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=False)

ARENA_SERVER_URL = os.getenv("NEXT_PUBLIC_ARENA_SERVER_URL", "wss://airdrop-arcade.onrender.com")
GAME_API_URL = os.getenv("NEXT_PUBLIC_GAME_API_URL", "https://arena.vorld.com/api")
VORLD_APP_ID = os.getenv("NEXT_PUBLIC_VORLD_APP_ID", "")
ARENA_GAME_ID = os.getenv("NEXT_PUBLIC_ARENA_GAME_ID", "")


@dataclass
class ServiceResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class ArenaGameService:
    def __init__(self, user_token: str = "", *, base_api_url: Optional[str] = None, socket_url: Optional[str] = None, debug: bool = False):
        self.user_token = user_token
        self.base_api_url = (base_api_url or GAME_API_URL).rstrip("/")
        self.socket_url = (socket_url or ARENA_SERVER_URL)
        self.debug = debug
        self.game_state: Optional[Dict[str, Any]] = None

        # HTTP client
        self.session = requests.Session()
        if self.user_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.user_token}",
            })
        self.session.headers.update({
            "X-Arena-Arcade-Game-ID": ARENA_GAME_ID,
            "X-Vorld-App-ID": VORLD_APP_ID,
            "Content-Type": "application/json",
        })

        # Socket.io client
        self.sio = socketio.Client(logger=self.debug, engineio_logger=self.debug)

        # Event callbacks (assign from outside as needed)
        self.on_arena_countdown_started: Optional[Callable[[Any], None]] = None
        self.on_countdown_update: Optional[Callable[[Any], None]] = None
        self.on_arena_begins: Optional[Callable[[Any], None]] = None
        self.on_player_boost_activated: Optional[Callable[[Any], None]] = None
        self.on_boost_cycle_update: Optional[Callable[[Any], None]] = None
        self.on_boost_cycle_complete: Optional[Callable[[Any], None]] = None
        self.on_package_drop: Optional[Callable[[Any], None]] = None
        self.on_immediate_item_drop: Optional[Callable[[Any], None]] = None
        self.on_event_triggered: Optional[Callable[[Any], None]] = None
        self.on_player_joined: Optional[Callable[[Any], None]] = None
        self.on_game_completed: Optional[Callable[[Any], None]] = None
        self.on_game_stopped: Optional[Callable[[Any], None]] = None

        # Wire socket event handlers
        self._wire_socket_handlers()

    def _wire_socket_handlers(self) -> None:
        @self.sio.event
        def connect():
            if self.debug:
                print("[arena] Connected to socket")

        @self.sio.event
        def connect_error(err):
            if self.debug:
                print("[arena] Connect error:", err)

        @self.sio.event
        def disconnect():
            if self.debug:
                print("[arena] Disconnected")

        # Arena events
        @self.sio.on("arena_countdown_started")
        def _arena_countdown_started(data):
            if self.on_arena_countdown_started:
                self.on_arena_countdown_started(data)

        @self.sio.on("countdown_update")
        def _countdown_update(data):
            if self.on_countdown_update:
                self.on_countdown_update(data)

        @self.sio.on("arena_begins")
        def _arena_begins(data):
            if self.on_arena_begins:
                self.on_arena_begins(data)

        # Boost events
        @self.sio.on("player_boost_activated")
        def _player_boost_activated(data):
            if self.on_player_boost_activated:
                self.on_player_boost_activated(data)

        @self.sio.on("boost_cycle_update")
        def _boost_cycle_update(data):
            if self.on_boost_cycle_update:
                self.on_boost_cycle_update(data)

        @self.sio.on("boost_cycle_complete")
        def _boost_cycle_complete(data):
            if self.on_boost_cycle_complete:
                self.on_boost_cycle_complete(data)

        # Package events
        @self.sio.on("package_drop")
        def _package_drop(data):
            if self.on_package_drop:
                self.on_package_drop(data)

        @self.sio.on("immediate_item_drop")
        def _immediate_item_drop(data):
            if self.on_immediate_item_drop:
                self.on_immediate_item_drop(data)

        # Game events
        @self.sio.on("event_triggered")
        def _event_triggered(data):
            if self.on_event_triggered:
                self.on_event_triggered(data)

        @self.sio.on("player_joined")
        def _player_joined(data):
            if self.on_player_joined:
                self.on_player_joined(data)

        @self.sio.on("game_completed")
        def _game_completed(data):
            if self.on_game_completed:
                self.on_game_completed(data)

        @self.sio.on("game_stopped")
        def _game_stopped(data):
            if self.on_game_stopped:
                self.on_game_stopped(data)

    # Helpers
    def _extract_error(self, resp: requests.Response, fallback: str) -> str:
        try:
            j = resp.json()
            msg = j.get("message") or j.get("error") or j.get("detail")
            if msg:
                return f"{msg} (status {resp.status_code})"
        except Exception:
            pass
        text = (resp.text or "").strip()
        if text:
            snippet = text if len(text) < 500 else text[:500] + "..."
            return f"{fallback} (status {resp.status_code}): {snippet}"
        return f"{fallback} (status {resp.status_code})"

    # Initialize game with stream URL
    def initialize_game(self, stream_url: str) -> ServiceResult:
        try:
            url = f"{self.base_api_url}/games/init"
            if self.debug:
                print(f"[arena] POST {url}")
            resp = self.session.post(url, json={"streamUrl": stream_url}, timeout=20)
            if resp.ok:
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                payload = data.get("data") if isinstance(data, dict) else None
                self.game_state = payload if isinstance(payload, dict) else None
                # Connect to websocket if provided
                if isinstance(self.game_state, dict) and self.game_state.get("websocketUrl"):
                    self.connect_websocket(self.game_state["websocketUrl"])
                return ServiceResult(True, self.game_state or data)
            else:
                return ServiceResult(False, error=self._extract_error(resp, "Failed to initialize game"))
        except requests.RequestException as exc:
            return ServiceResult(False, error=str(exc))

    # Connect to WebSocket
    def connect_websocket(self, ws_url: Optional[str] = None) -> bool:
        url = ws_url or self.socket_url
        if not url:
            if self.debug:
                print("[arena] Missing websocket URL")
            return False
        try:
            self.sio.connect(
                url,
                transports=["websocket"],
                auth={"token": self.user_token, "appId": VORLD_APP_ID},
            )
            return True
        except Exception as e:
            if self.debug:
                print("[arena] Socket connect failed:", e)
            return False

    # HTTP API wrappers
    def get_game_details(self, game_id: str) -> ServiceResult:
        try:
            url = f"{self.base_api_url}/games/{game_id}"
            if self.debug:
                print(f"[arena] GET {url}")
            resp = self.session.get(url, timeout=15)
            if resp.ok:
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                return ServiceResult(True, data.get("data") if isinstance(data, dict) else data)
            else:
                return ServiceResult(False, error=self._extract_error(resp, "Failed to get game details"))
        except requests.RequestException as exc:
            return ServiceResult(False, error=str(exc))

    def boost_player(self, game_id: str, player_id: str, amount: int, username: str) -> ServiceResult:
        try:
            url = f"{self.base_api_url}/games/boost/player/{game_id}/{player_id}"
            if self.debug:
                print(f"[arena] POST {url}")
            resp = self.session.post(url, json={"amount": amount, "username": username}, timeout=20)
            if resp.ok:
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                return ServiceResult(True, data.get("data") if isinstance(data, dict) else data)
            else:
                return ServiceResult(False, error=self._extract_error(resp, "Failed to boost player"))
        except requests.RequestException as exc:
            return ServiceResult(False, error=str(exc))

    def update_stream_url(self, game_id: str, stream_url: str, old_stream_url: str) -> ServiceResult:
        try:
            url = f"{self.base_api_url}/games/{game_id}/stream-url"
            if self.debug:
                print(f"[arena] PUT {url}")
            resp = self.session.put(url, json={"streamUrl": stream_url, "oldStreamUrl": old_stream_url}, timeout=20)
            if resp.ok:
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                return ServiceResult(True, data.get("data") if isinstance(data, dict) else data)
            else:
                return ServiceResult(False, error=self._extract_error(resp, "Failed to update stream URL"))
        except requests.RequestException as exc:
            return ServiceResult(False, error=str(exc))

    def get_items_catalog(self) -> ServiceResult:
        try:
            url = f"{self.base_api_url}/items/catalog"
            if self.debug:
                print(f"[arena] GET {url}")
            resp = self.session.get(url, timeout=15)
            if resp.ok:
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                return ServiceResult(True, data.get("data") if isinstance(data, dict) else data)
            else:
                return ServiceResult(False, error=self._extract_error(resp, "Failed to get items catalog"))
        except requests.RequestException as exc:
            return ServiceResult(False, error=str(exc))

    def drop_immediate_item(self, game_id: str, item_id: str, target_player: str) -> ServiceResult:
        try:
            url = f"{self.base_api_url}/items/drop/{game_id}"
            if self.debug:
                print(f"[arena] POST {url}")
            resp = self.session.post(url, json={"itemId": item_id, "targetPlayer": target_player}, timeout=20)
            if resp.ok:
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text}
                return ServiceResult(True, data.get("data") if isinstance(data, dict) else data)
            else:
                return ServiceResult(False, error=self._extract_error(resp, "Failed to drop item"))
        except requests.RequestException as exc:
            return ServiceResult(False, error=str(exc))

    # Control
    def disconnect(self) -> None:
        try:
            if self.sio.connected:
                self.sio.disconnect()
        finally:
            self.game_state = None

    def get_game_state(self) -> Optional[Dict[str, Any]]:
        return self.game_state
