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

GUEST_FID = None
PERSON_ID = None


class TestRequestKus(unittest.TestCase):

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

        print(ret_value)
        self.assertTrue(ret_value['RESULT'])

    def test_002_create_guest(self):
        """ Создаем тестовую заявку на гостя."""
        global GUEST_FID
        ret_value = {"RESULT": False, "DESC": "", "DATA": None}

        url = f"http://127.0.0.1:8066/DoCreateGuest"

        try:
            result = requests.post(url, timeout=5, json=JSON_GUEST)

            if result.status_code == 200:
                ret_value['DATA'] = result.json()

                if ret_value['DATA'].get('RESULT') == 'SUCCESS':
                    ret_value['RESULT'] = True
            else:
                ret_value['DESC'] = f"Status code: {result.status_code}"

            GUEST_FID = ret_value['DATA'].get("FID")

        except Exception as ex:
            ret_value['DESC'] = str(ex)

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

        print(ret_value)

        self.assertTrue(ret_value['RESULT'])

    def test_005_add_person(self):
        """ Имитация выданного пропуска """
        global PERSON_ID
        ret_value = {"RESULT": False, "DESC": '', 'DATA': None}

        url = f"http://127.0.0.1:8066/DoAddPersonGuest"

        if GUEST_FID:
            try:
                result = requests.post(url, timeout=5, json={"FName": "Тест Тест", "FID": GUEST_FID})

                if result.status_code == 200:
                    ret_value['DATA'] = result.json()

                    if ret_value['DATA'].get('RESULT') == 'SUCCESS':
                        ret_value['RESULT'] = True

                        PERSON_ID = ret_value['DATA'].get("FID")
                else:
                    ret_value['DESC'] = f"Статус код: {result.status_code}"

            except Exception as ex:
                ret_value['DESC'] = str(ex)

        else:
            ret_value['DESC'] = f"Guest fid: {GUEST_FID}"

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

        print(ret_value)

        self.assertTrue(ret_value['RESULT'])


if __name__ == '__main__':
    unittest.main()
