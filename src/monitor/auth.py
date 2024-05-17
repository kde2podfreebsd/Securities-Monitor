import os
import httpx
from typing import Union, NoReturn
from src.logger import logger


class PassportMOEXAuth:
    _instance = None

    def __new__(cls, *args, **kwargs) -> object:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, username: str, password: str) -> NoReturn:
        self.auth_cert = None
        self.error_count = 0
        if not hasattr(self, 'initialized'):
            self.username = username
            self.password = password
            self.initialized = True
            logger.info(message="Init PassportMOEXAuth object")

    async def authenticate(self) -> bool:
        async with httpx.AsyncClient() as client:
            AUTH_URL = 'https://passport.moex.com/authenticate'
            response = await client.get(AUTH_URL, auth=(self.username, self.password))
            if response.status_code == 200:
                self.auth_cert = response.cookies.get('MicexPassportCert')
                self.error_count = 0
                logger.info(message="Success get CERT auth token in https://passport.moex.com/authenticate")
                return True
            else:
                logger.error(message="Failed to get CERT auth token in https://passport.moex.com/authenticate")
                return False

    async def download_csv(self, url: str, filename: str) -> Union[bool, str]:
        if self.auth_cert is None:
            await self.authenticate()

        async with httpx.AsyncClient() as client:
            headers = {'Cookie': f'MicexPassportCert={self.auth_cert}', 'Cache-Control': 'no-cache'}
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                    logger.info(message=f"Upload csv file in {filename}")
                return filename
            elif response.status_code != 200:
                if self.error_count < 3:
                    await self.authenticate()
                    self.error_count += 1
                    return await self.download_csv(url, filename)
                else:
                    logger.error(message="Error: Authentication token expired, and failed to refresh. Stopping further requests.")
                    return False
            else:
                logger.error(message=f"Error: Unable to download CSV. Status Code: {response.status_code}")
                return False

    @staticmethod
    def delete_csv(filename: str) -> bool:
        try:
            os.remove(filename)
            logger.info(message=f"File '{filename}' deleted.")
            return True
        except FileNotFoundError:
            logger.error(message=f"OS Error: File '{filename}' not found.")
            return False
        except Exception as e:
            logger.error(message=f"Ошибка при удалении файла '{filename}': {e}")
            return False


if __name__ == '__main__':
    import asyncio
    pm = PassportMOEXAuth(username="Ivan.Bogomolov2@moex.com", password="21Ivvaarnya26")
    print(asyncio.run(pm.authenticate()))
    print(asyncio.run(pm.download_csv(url="https://iss.moex.com/iss/datashop/algopack/eq/hi2/sber.csv?from=2024-05-07&till=2024-05-07&iss.only=data", filename='test.csv')))
