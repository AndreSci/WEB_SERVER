import requests
import datetime

import unittest


class TestRequestRum(unittest.TestCase):

    def test_delete_guest(self):
        """ Добавить номер автомобиля сотруднику, Номер может быть записан только на одного сотрудника """

        ret_value = {"RESULT": True, "DESC": '', 'DATA': None}

        fid = 24
        f_account_id = 1419

        url = f"http://127.0.0.1:8066/DoDeleteGuest"

        try:
            result = requests.post(url, timeout=5, json={"FAccountID": f_account_id, "FID": fid})

            if result.status_code == 200:

                ret_value['DATA'] = result.json()

                if ret_value['DATA'].get('RESULT') != 'SUCCESS':
                    ret_value['RESULT'] = False
            else:
                ret_value['RESULT'] = False
                ret_value['DESC'] = f"Статус код: {result.status_code}"

        except Exception as ex:
            ret_value['RESULT'] = False
            ret_value['DESC'] = ex

        print(ret_value)

        self.assertTrue(ret_value['RESULT'])


if __name__ == '__main__':
    unittest.main()
