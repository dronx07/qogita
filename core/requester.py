# core/requester.py

from typing import Optional
import os
from dotenv import load_dotenv
from curl_cffi.requests import AsyncSession

load_dotenv()


class Requester:
    def __init__(self, url: str, referrer: str, cookie: Optional[str] = None, api: Optional[bool] = False):
        self.url = url
        self.session: Optional[AsyncSession] = None
        self.headers = {
            "Accept": "application/json" if api else "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Cookie": cookie if cookie else "",
            "Referer": referrer if referrer else "",
        }
        self.proxy = os.getenv("PROXY")

    async def __aenter__(self):
        self.session = AsyncSession(
            headers=self.headers,
            proxy=self.proxy,
            impersonate="chrome142",
            timeout=10,
            allow_redirects=True,
            http_version="v2"
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def fetch_get(self, retries: int = 3):
        for _ in range(retries):
            try:
                response = await self.session.get(self.url)
                return response
            except Exception:
                continue
        return None

    async def fetch_post(self, data: dict, retries: int = 3):
        for _ in range(retries):
            try:
                response = await self.session.post(self.url, json=data)
                return response
            except Exception:
                continue
        return None
