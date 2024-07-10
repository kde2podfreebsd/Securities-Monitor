import logging
from httpx import AsyncClient, HTTPStatusError
from typing import Any, Dict, Optional


class PassportMOEXAuth:

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._auth_cert: Optional[str] = None
        self._error_count: int = 0

    @property
    def auth_cert(self) -> Optional[str]:
        return self._auth_cert

    async def _authenticate(self) -> None:
        async with AsyncClient() as client:
            AUTH_URL = 'https://passport.moex.com/authenticate'
            try:
                response = await client.get(
                    AUTH_URL,
                    auth=(self._username, self._password),
                    timeout=600
                )
                response.raise_for_status()
                self._auth_cert = response.cookies.get('MicexPassportCert')
                self._error_count = 0
            except HTTPStatusError as e:
                logging.error('Failed to authenticate: %s', e)
                raise

    async def authenticate(self) -> None:
        if not self._auth_cert:
            try:
                await self._authenticate()
            except Exception as e:
                logging.error('Failed to authenticate: %s', e)
                raise

    async def _auth_request(self, url: str) -> Dict[str, Any]:
        async with AsyncClient() as client:
            headers = {
                'Cookie': f'MicexPassportCert={self.auth_cert}',
                'Cache-Control': 'no-cache'
            }
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except HTTPStatusError as e:
                if self._error_count < 3:
                    await self._authenticate()
                    self._error_count += 1
                    return await self._auth_request(url=url)
                else:
                    logging.error('Error with Auth passport.moex.com: %s', e)
                    raise

    async def auth_request(self, url: str) -> Dict[str, Any]:
        await self.authenticate()
        return await self._auth_request(url=url)

