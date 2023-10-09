import requests
import json
from misc.logger import Logger


class FaceDriver:
    """ Соединение с драйвером посредником (Колин драйвер) """
    def __init__(self, set_ini):
        self.settings_ini = set_ini

    def add_face(self, json_data: json, logger: Logger) -> dict:
        ret_value = {"RESULT": "ERROR", "DATA": dict(), "DESC": "Ошибка работы с драйвером"}

        try:
            result = requests.post(f"http://{self.settings_ini['dr_host']}:{self.settings_ini['dr_port']}/addFace",
                                   data=json_data, timeout=10)

            ret_value = result.json()

            if ret_value['RESULT'] == "ERROR":
                logger.add_log(f"ERROR\tFaceDriver.add_face\tОшибка на драйвере - {json_data['DATA']}")

        except Exception as ex:
            logger.exception(f"Исключение вызвало связь с Драйвером - {ex}")

        return ret_value

    def add_person(self, json_data: json, logger: Logger) -> str:
        ret_value = "ERROR"
        try:
            result = requests.post(f"http://{self.settings_ini['dr_host']}:{self.settings_ini['dr_port']}/addPerson",
                                   data=json_data)

            json_data = result.json()
            ret_value = json_data["RESULT"]

            if ret_value == "ERROR":
                logger.add_log(f"ERROR\tFaceDriver.add_person\tОшибка на драйвере: {json_data['DATA']}")

        except Exception as ex:
            logger.exception(f"Исключение вызвало связь с Драйвером: {ex}")

        return ret_value

    def add_person_with_face(self, json_data: json, logger: Logger) -> dict:
        ret_value = {"RESULT": "ERROR", "DATA": dict(), "DESC": "Ошибка работы с драйвером"}
        try:
            result = requests.post(f"http://{self.settings_ini['dr_host']}:"
                                   f"{self.settings_ini['dr_port']}/addPersonWithFace",
                                   data=json_data, timeout=10)

            ret_value = result.json()

            if ret_value["RESULT"] == "ERROR":
                logger.add_log(f"ERROR\tFaceDriver.add_person_with_face\tОшибка на драйвере: {ret_value.get('DATA')}")

        except Exception as ex:
            logger.exception(f"Исключение вызвало связь с Драйвером: {ex}")

        return ret_value

    def update_person(self, json_data: json, logger: Logger) -> str:
        ret_value = "ERROR"
        try:
            result = requests.post(f"http://{self.settings_ini['dr_host']}:"
                                   f"{self.settings_ini['dr_port']}/updatePerson",
                                   data=json_data)

            json_data = result.json()
            ret_value = json_data["RESULT"]

            if ret_value == "ERROR":
                logger.add_log(f"ERROR\tFaceDriver.update_person\tОшибка на драйвере: {json_data['DATA']}")

        except Exception as ex:
            logger.exception(f"Исключение вызвало связь с Драйвером: {ex}")

        return ret_value

    def delete_person(self, json_data: json, logger: Logger) -> dict:
        ret_value = {"RESULT": "ERROR", "DATA": dict(), "DESC": ""}
        try:
            result = requests.post(f"http://{self.settings_ini['dr_host']}:"
                                   f"{self.settings_ini['dr_port']}/deletePerson",
                                   data=json_data)

            json_data = result.json()
            ret_value['RESULT'] = json_data["RESULT"]

            if ret_value == "ERROR":
                logger.add_log(f"ERROR\tFaceDriver.delete_person\tОшибка на драйвере: {json_data.get('DATA')}")
                ret_value['DESC'] = json_data["DATA"]['msg']

        except Exception as ex:
            logger.exception(f"Исключение вызвало связь с Драйвером: {ex}")

        return ret_value
