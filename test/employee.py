""" Тесты для проверки запросов на ГОСТЯ """
import requests
import unittest


JSON_EMPLOYEE = {
    "inn": '7720275587',
    "Last_Name": "Тест_Фамилия",
    "First_Name": "Тест_Имя",
    "img64": '',
    "Middle_Name": '',
    "Car_Number": ""
}

class Employee(unittest.TestCase):
    def test_001_create_employee(self):
        """ Создаем тестового сотрудника."""

        ret_value = {"RESULT": False, "DESC": "", "DATA": None}

        url = f"http://127.0.0.1:8066/DoCreateCardHolder"

        try:
            result = requests.post(url, timeout=5, json=JSON_EMPLOYEE)

            if result.status_code == 200:
                ret_value['DATA'] = result.json()

                result_request = ret_value['DATA'].get('RESULT')

                if result_request == 'SUCCESS' or result_request == 'WARNING':
                    ret_value['RESULT'] = True

                    self.__class__.guest_fid = ret_value['DATA'].get('DATA').get("FID")
            else:
                ret_value['DESC'] = f"Status code: {result.status_code}"

        except Exception as ex:
            ret_value['DESC'] = str(ex)

        print(f"\t{ret_value}\n")

        self.assertTrue(ret_value['RESULT'])


if __name__ == "__main__":
    unittest.main()