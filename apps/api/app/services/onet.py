import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings


class OnetClient:
    def __init__(self) -> None:
        self.base_url = settings.onet_base_url.rstrip("/")
        self.auth = None
        if settings.onet_username and settings.onet_password:
            self.auth = (settings.onet_username, settings.onet_password)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=settings.request_timeout_s) as client:
            response = await client.get(f"{self.base_url}/{path.lstrip('/')}", params=params, auth=self.auth)
            response.raise_for_status()
            return response.json()
