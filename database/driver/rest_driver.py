import requests
import json
from misc.logger import Logger


class ConDriver:
    """ Соединение с драйвером посредником (Колин драйвер) """
    def __init__(self, set_ini):
        self.settings_ini = set_ini

    def send_photo(self, json_data: json, logger: Logger) -> str:

        try:
            result = requests.post(f"{self.settings_ini['dr_host']}:{self.settings_ini['dr_port']}", json=json_data)
        except Exception as ex:
            result = "ERROR"
            logger.add_log(f"ERROR\tОшибка связи с Драйвером - {ex}")

        return result
