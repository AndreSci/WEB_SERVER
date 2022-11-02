import requests
import json
from misc.logger import Logger


class ConDriver:
    """ Соединение с драйвером посредником (Колин драйвер) """
    def __init__(self, set_ini):
        self.settings_ini = set_ini

    def add_face(self, json_data: json, logger: Logger) -> str:
        ret_value = "ERROR"
        try:
            result = requests.post(f"http://{self.settings_ini['dr_host']}:{self.settings_ini['dr_port']}/addFace",
                                   data=json_data)

            json_data = result.json()
            ret_value = json_data["RESULT"]

            if ret_value == "ERROR":
                logger.add_log(f"ERROR\tОшибка на драйвере - {json_data['DATA']}")

        except Exception as ex:
            logger.add_log(f"ERROR\tИсключение вызвало связь с Драйвером - {ex}")

        return ret_value

    def add_person(self, json_data: json, logger: Logger) -> str:
        ret_value = "ERROR"
        try:
            result = requests.post(f"http://{self.settings_ini['dr_host']}:{self.settings_ini['dr_port']}/addPerson",
                                   data=json_data)

            json_data = result.json()
            ret_value = json_data["RESULT"]

            if ret_value == "ERROR":
                logger.add_log(f"ERROR\tОшибка на драйвере - {json_data['DATA']}")

        except Exception as ex:
            logger.add_log(f"ERROR\tИсключение вызвало связь с Драйвером - {ex}")

        return ret_value

    def add_person_with_face(self, json_data: json, logger: Logger) -> str:
        ret_value = "ERROR"
        try:
            result = requests.post(f"http://{self.settings_ini['dr_host']}:"
                                   f"{self.settings_ini['dr_port']}/addPersonWithFace",
                                   data=json_data)

            json_data = result.json()
            ret_value = json_data["RESULT"]

            if ret_value == "ERROR":
                logger.add_log(f"ERROR\tОшибка на драйвере - {json_data['DATA']}")

        except Exception as ex:
            logger.add_log(f"ERROR\tИсключение вызвало связь с Драйвером - {ex}")

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
                logger.add_log(f"ERROR\tОшибка на драйвере - {json_data['DATA']}")

        except Exception as ex:
            logger.add_log(f"ERROR\tИсключение вызвало связь с Драйвером - {ex}")

        return ret_value

    def delete_person(self, json_data: json, logger: Logger) -> str:
        ret_value = "ERROR"
        try:
            result = requests.post(f"http://{self.settings_ini['dr_host']}:"
                                   f"{self.settings_ini['dr_port']}/deletePerson",
                                   data=json_data)

            json_data = result.json()
            ret_value = json_data["RESULT"]

            if ret_value == "ERROR":
                logger.add_log(f"ERROR\tОшибка на драйвере - {json_data['DATA']}")

        except Exception as ex:
            logger.add_log(f"ERROR\tИсключение вызвало связь с Драйвером - {ex}")

        return ret_value
