import argparse
import os
import sys
from typing import Optional

from auth_service import VorldAuthService


def positive_bool(value: str) -> bool:
    v = value.strip().lower()
    if v in ("1", "true", "yes", "y", "on"):
        return True
    if v in ("0", "false", "no", "n", "off"):
        return False
    raise argparse.ArgumentTypeError("Expected a boolean (true/false)")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run auth API tests against backend")
    parser.add_argument("--email", help="Email to login", default=os.getenv("TEST_EMAIL", ""))
    parser.add_argument("--password", help="Password to login", default=os.getenv("TEST_PASSWORD", ""))
    parser.add_argument("--base-url", help="Override base URL", default=os.getenv("NEXT_PUBLIC_AUTH_SERVER_URL"))
    parser.add_argument("--app-id", help="Override app id", default=os.getenv("NEXT_PUBLIC_VORLD_APP_ID"))
    parser.add_argument("--dry-run", type=positive_bool, default=False, help="Print actions without calling network")
    parser.add_argument("--debug", type=positive_bool, default=False, help="Enable debug logs")
    parser.add_argument("--no-hash", type=positive_bool, default=False, help="Send password in plaintext (no SHA-256)")

    args = parser.parse_args(argv)

    svc = VorldAuthService(base_url=args.base_url, app_id=args.app_id, debug=args.debug, hash_password=not args.no_hash)
    print("Config:")
    print("  base_url:", svc.base_url)
    print("  app_id  :", svc.app_id or "(empty)")

    if args.dry_run:
        print("Dry-run mode: not calling backend.")
        return 0

    if not args.email or not args.password:
        print("Missing --email/--password (or TEST_EMAIL/TEST_PASSWORD env).", file=sys.stderr)
        return 2

    print("\n1) Login with email/password...")
    login = svc.login_with_email(args.email, args.password)
    if login.success:
        print("   Login OK.")
        # Optionally print token or user info if backend returns it
        print("   Response keys:", list((login.data or {}).keys()))
    else:
        print("   Login failed:", login.error)
        return 1

    print("\n2) Get profile...")
    prof = svc.get_profile()
    if prof.success:
        print("   Profile OK. Keys:", list((prof.data or {}).keys()))
        print("   Sample:", (prof.data or {}))
    else:
        print("   Get profile failed:", prof.error)
        return 1

    print("\nAll API tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
