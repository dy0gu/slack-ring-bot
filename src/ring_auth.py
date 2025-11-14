import json
from pathlib import Path

from ring_doorbell import Auth, AuthenticationError, Requires2FAError

CACHE_DIR = Path(".cache")
TOKEN_CACHE_FILENAME = CACHE_DIR / "token.cache"


class RingAuthenticator:
    def __init__(
        self,
        username: str,
        password: str,
        user_agent: str,
        otp: str | None = None,
    ):
        self.username = username
        self.password = password
        self.otp = otp
        self.user_agent = user_agent
        self.cache_path = TOKEN_CACHE_FILENAME
        self.auth = None

    def _token_updated(self, token: dict) -> None:
        self.cache_path.write_text(json.dumps(token))
        print("🔄 Token updated and cached.")

    async def async_authenticate(self) -> Auth:
        if self.cache_path.is_file():
            print("⏳ Loading cached authentication token...")
            token = json.loads(self.cache_path.read_text())
            self.auth = Auth(self.user_agent, token, self._token_updated)

            try:
                return self.auth
            except AuthenticationError:
                print("⌛ Cached token expired, fetching new token...")

        self.auth = Auth(self.user_agent, None, self._token_updated)

        try:
            await self.auth.async_fetch_token(self.username, self.password)
        except Requires2FAError:
            await self.auth.async_fetch_token(
                self.username, self.password, self.otp
            )
        return self.auth

    async def async_close(self) -> None:
        if self.auth:
            await self.auth.async_close()
