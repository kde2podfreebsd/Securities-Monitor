import pytest
import os
from dotenv import load_dotenv
from src.passport import PassportMOEXAuth

load_dotenv()
auth = PassportMOEXAuth(os.getenv('MOEX_PASSPORT_LOGIN'), os.getenv('MOEX_PASSPORT_PASSWORD'))

@pytest.mark.asyncio
async def test_authenticate():
    await auth.authenticate()
    assert auth.auth_cert

@pytest.mark.asyncio
async def test_auth_request():
    response = await auth.auth_request('https://iss.moex.com/iss/datashop/algopack/eq/tradestats.json')
    assert isinstance(response, dict)
