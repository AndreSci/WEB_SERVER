import requests
import unittest

REMOTE_ID = 249223
ACCOUNT_ID = 1419
FACE_STATION_ID_INPUT = 45
FACE_STATION_ID_OUTPUT = 46


JSON_GUEST = {
    "FAccountID": 1419,
    "FLastName": "Тест",
    "FFirstName": "Тест",
    "FDateFrom": "2023-10-04",
    "FDateTo": "2023-11-01",
    "FInviteCode": 123456,
    "FRemoteID": 249223,
    "FPhone": "+79661112233"
}


class TestRequestKus(unittest.TestCase):
    guest_fid = None
    person_id = None

    # СОЗДАЕМ И БЛОКИРУЕМ ЗАЯВКУ
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
        # print(f"\t{ret_value}\n")

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
        # print(f"\t{ret_value}\n")

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
        # print(f"\n{ret_value}\n")

        self.assertTrue(ret_value['RESULT'])

    # ДЕЛАЕМ ЗАЯВКУ АКТИВНОЙ, ИМИТИРУЕМ ВЫДАЧУ, БЛОКИРУЕМ
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

        # print(f"\t{ret_value}\n")
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

                        self.__class__.person_id = ret_value['DATA'].get('DATA').get("FID")
                else:
                    ret_value['DESC'] = f"Статус код: {result.status_code}"

            except Exception as ex:
                ret_value['DESC'] = str(ex)

        else:
            ret_value['DESC'] = f"Guest fid: {self.__class__.guest_fid}"
        # print(f"\t{ret_value}\n")

        self.assertTrue(ret_value['RESULT'])

    def test_006_block_guest_with_tperson(self):
        """ Заблокировать заявку на Гостя """

        self.test_003_block_guest()

    # ДЕЛАЕМ ЗАЯВКУ АКТИВНОЙ, ИМИТИРУЕМ ВЫДАЧУ и ВХОД, СТАВИМ БЛОК ПО ВЫХОДУ

    def test_007_del_new_guest(self):
        """ Удалить заявку и создать новую для Гостя """
        self.test_001_delete_guest()
        self.test_002_create_guest()

    def test_008_add_person(self):
        """ Имитация выданного пропуска """
        self.test_005_add_person()

    def test_009_add_tpasses(self, station_id=FACE_STATION_ID_INPUT):
        """ Имитация прохода вход """

        ret_value = {"RESULT": False, "DESC": '', 'DATA': None}

        url = f"http://127.0.0.1:8066/DoAddPassesGuest"

        if self.__class__.guest_fid:
            try:
                result = requests.post(url, timeout=5, json={"FPersonID": self.__class__.person_id,
                                                             "FStationID": station_id})

                if result.status_code == 200:
                    ret_value['DATA'] = result.json()

                    if ret_value['DATA'].get('RESULT') == 'SUCCESS':
                        ret_value['RESULT'] = True
                else:
                    ret_value['DESC'] = f"Статус код: {result.status_code}"

            except Exception as ex:
                ret_value['DESC'] = str(ex)

        else:
            ret_value['DESC'] = f"Guest fid: {self.__class__.guest_fid}"
        # print(f"\t{ret_value}\n")

        self.assertTrue(ret_value['RESULT'])

    def test_010_block_guest_with_tperson(self):
        """ Заблокировать заявку на Гостя """

        self.test_003_block_guest()

    # ДЕЛАЕМ ЗАЯВКУ АКТИВНОЙ, ИМИТИРУЕМ ВЫДАЧУ и ВХОД, СТАВИМ БЛОК ПО ВЫХОДУ

    def test_011_del_new_guest(self):
        """ Удалить заявку и создать новую для Гостя """
        self.test_001_delete_guest()
        self.test_002_create_guest()

    def test_012_add_person(self):
        """ Имитация выданного пропуска """
        self.test_005_add_person()

    def test_013_add_tpasses(self):
        """ Имитация прохода вход """

        self.test_009_add_tpasses()

    def test_014_add_tpasses(self):
        """ Имитация прохода выхода """

        self.test_009_add_tpasses(FACE_STATION_ID_OUTPUT)

    def test_015_block_guest_with_tperson(self):
        """ Заблокировать заявку на Гостя """

        self.test_003_block_guest()


if __name__ == '__main__':
    unittest.main()
