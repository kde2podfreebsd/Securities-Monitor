import httpx


def authenticate(username: str, password: str):
    session = httpx.Client()
    AUTH_URL = 'https://passport.moex.com/authenticate'
    response = session.get(AUTH_URL, auth=(username, password))
    if response.status_code == 200:
        AUTH_CERT = response.cookies.get('MicexPassportCert')
        return AUTH_CERT
    else:
        return None


def make_authenticated_request(url: str, cert: str):
    if cert is None:
        raise Exception("Unauthorized")

    session = httpx.Client()
    headers = {'Cookie': f'MicexPassportCert={cert}', 'Cache-Control': 'no-cache'}
    response = session.get(url, headers=headers)

    return response

# with open('example.csv', 'wb') as f:
#     f.write(response.content)
