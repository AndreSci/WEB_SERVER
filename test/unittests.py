import requests
import unittest

REMOTE_ID = 11
ACCOUNT_ID = 1001

JSON_GUEST = {
    "FAccountID": 1001,
    "FLastName": "Тест",
    "FFirstName": "Тест",
    "FDateFrom": "2023-10-04",
    "FDateTo": "2023-11-01",
    "FInviteCode": 123456,
    "FRemoteID": 11,
    "FPhone": "+79661140411"
}


class TestRequestKus(unittest.TestCase):
    guest_fid = None
    person_id = None

    def test_001_delete_guest(self):
        """ Удаляем (если есть в БД) тестовую заявку на гостя."""

        ret_value = {"RESULT": False, "DESC": "", "DATA": None}

        url = f"http://127.0.0.1:8066/DoDeleteGuest"

        try:
            result = requests.post(url, timeout=5, json={"FAccountID": ACCOUNT_ID, "FID": REMOTE_ID})

            if result.status_code == 200:
                ret_value['DATA'] = result.json()
                ret_value['RESULT'] = True
            else:
                ret_value['DESC'] = f"Status code: {result.status_code}"

        except Exception as ex:
            ret_value['DESC'] = str(ex)

        print("TEST: 001")
        print(ret_value)
        self.assertTrue(ret_value['RESULT'])

    def test_002_create_guest(self):
        """ Создаем тестовую заявку на гостя."""

        ret_value = {"RESULT": False, "DESC": "", "DATA": None}

        url = f"http://127.0.0.1:8066/DoCreateGuest"

        try:
            result = requests.post(url, timeout=5, json=JSON_GUEST)

            if result.status_code == 200:
                ret_value['DATA'] = result.json()

                if ret_value['DATA'].get('RESULT') == 'SUCCESS':
                    ret_value['RESULT'] = True

                    self.__class__.guest_fid = ret_value['DATA'].get('DATA').get("FID")
            else:
                ret_value['DESC'] = f"Status code: {result.status_code}"

        except Exception as ex:
            ret_value['DESC'] = str(ex)
        print("TEST: 002")
        print(ret_value)
        self.assertTrue(ret_value['RESULT'])

    def test_003_block_guest(self):
        """ Заблокировать заявку на Гостя """

        ret_value = {"RESULT": False, "DESC": '', 'DATA': None}

        url = f"http://127.0.0.1:8066/DoBlockGuest"

        try:
            result = requests.post(url, timeout=5, json={"FAccountID": ACCOUNT_ID, "FID": REMOTE_ID})

            if result.status_code == 200:
                ret_value['DATA'] = result.json()

                if ret_value['DATA'].get('RESULT') == 'SUCCESS':
                    ret_value['RESULT'] = True
            else:
                ret_value['DESC'] = f"Статус код: {result.status_code}"

        except Exception as ex:
            ret_value['DESC'] = str(ex)

        print("TEST: 003")
        print(ret_value)

        self.assertTrue(ret_value['RESULT'])

    def test_004_unblock_guest(self):
        """ Разблокировать заявку на Гостя """

        ret_value = {"RESULT": False, "DESC": '', 'DATA': None}

        url = f"http://127.0.0.1:8066/DoUnBlockGuest"

        try:
            result = requests.post(url, timeout=5, json={"FAccountID": ACCOUNT_ID, "FID": REMOTE_ID})

            if result.status_code == 200:
                ret_value['DATA'] = result.json()

                if ret_value['DATA'].get('RESULT') == 'SUCCESS':
                    ret_value['RESULT'] = True
            else:
                ret_value['DESC'] = f"Статус код: {result.status_code}"

        except Exception as ex:
            ret_value['DESC'] = str(ex)

        print("TEST: 004")
        print(ret_value)

        self.assertTrue(ret_value['RESULT'])

    def test_005_add_person(self):
        """ Имитация выданного пропуска """

        ret_value = {"RESULT": False, "DESC": '', 'DATA': None}

        url = f"http://127.0.0.1:8066/DoAddPersonGuest"

        if self.__class__.guest_fid:
            try:
                result = requests.post(url, timeout=5, json={"FName": "Тест Тест", "FID": self.__class__.guest_fid})

                if result.status_code == 200:
                    ret_value['DATA'] = result.json()

                    if ret_value['DATA'].get('RESULT') == 'SUCCESS':
                        ret_value['RESULT'] = True

                        self.__class__.person_id = ret_value['DATA'].get("FID")
                else:
                    ret_value['DESC'] = f"Статус код: {result.status_code}"

            except Exception as ex:
                ret_value['DESC'] = str(ex)

        else:
            ret_value['DESC'] = f"Guest fid: {self.__class__.guest_fid}"

        print("TEST: 005")
        print(ret_value)

        self.assertTrue(ret_value['RESULT'])

    def test_006_block_guest(self):
        """ Заблокировать заявку на Гостя """

        ret_value = {"RESULT": False, "DESC": '', 'DATA': None}

        url = f"http://127.0.0.1:8066/DoBlockGuest"

        try:
            result = requests.post(url, timeout=5, json={"FAccountID": ACCOUNT_ID, "FID": REMOTE_ID})

            if result.status_code == 200:
                ret_value['DATA'] = result.json()

                if ret_value['DATA'].get('RESULT') == 'SUCCESS':
                    ret_value['RESULT'] = True
            else:
                ret_value['DESC'] = f"Статус код: {result.status_code}"

        except Exception as ex:
            ret_value['DESC'] = ex

        print("TEST: 006")
        print(ret_value)

        self.assertTrue(ret_value['RESULT'])


if __name__ == '__main__':
    unittest.main()

