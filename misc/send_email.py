import requests
from requests.models import Response


class SendEMAIL:
    """ Класс предназначен для отправки email сообщений посетителю """

    def __init__(self, set_ini: dict):
        """ Принимает словарь с настройками из settings.ini """
        self.host = set_ini["sms_host"]
        self.port = set_ini["sms_port"]

    def send_sms(self, email_name, text) -> Response:

        res = requests.post(f"http://{self.host}:{self.port}/send_email/?femail={email_name}&ftext={text}",
                            timeout=10)

        return res
