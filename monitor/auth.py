import os
import httpx


class PassportMOEXAuth:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, username: str, password: str):
        self.auth_cert = None
        self.error_count = 0
        if not hasattr(self, 'initialized'):
            self.username = username
            self.password = password
            self.session = httpx.Client()
            self.authenticate()
            self.initialized = True

    def authenticate(self):
        AUTH_URL = 'https://passport.moex.com/authenticate'
        response = self.session.get(AUTH_URL, auth=(self.username, self.password))
        if response.status_code == 200:
            self.auth_cert = response.cookies.get('MicexPassportCert')
            self.error_count = 0
            return True
        else:
            return False

    def download_csv(self, url: str, filename: str):
        headers = {'Cookie': f'MicexPassportCert={self.auth_cert}', 'Cache-Control': 'no-cache'}
        response = self.session.get(url, headers=headers)
        if response.status_code == 200:
            with open(os.path.join('csv', filename), 'wb') as f:
                f.write(response.content)
            return filename
        elif response.status_code != 200:
            if self.error_count < 3:
                self.authenticate()
                self.error_count += 1
                return self.download_csv(url, filename)
            else:
                print("Error: Authentication token expired, and failed to refresh. "
                      "Stopping further requests.")
                return False
        else:
            print(f"Error: Unable to download CSV. Status Code: {response.status_code}")
            return False

    def delete_csv(self, filename: str):
        try:
            csv_path = os.path.join('csv', filename)
            os.remove(csv_path)
            print(f"Файл '{filename}' успешно удален.")
        except FileNotFoundError:
            print(f"Ошибка: Файл '{filename}' не найден.")
        except Exception as e:
            print(f"Ошибка при удалении файла '{filename}': {e}")


if __name__ == "__main__":
    pass
    # downloader1.download_csv(url="https://iss.moex.com/iss/datashop/algopack/eq/tradestats/sber.csv?from=2024-04-25&till=2024-04-25&iss.only=data", filename='test.csv')
