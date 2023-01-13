import requests


class SendSMS:
    """ Класс предназначен для отправки sms сообщений содержащий шестизначный код """

    def __init__(self, set_ini: dict):
        """ Принимает словарь с настройками из settings.ini """
        self.host = set_ini["sms_host"]
        self.port = set_ini["sms_port"]

    def send_sms(self, number, text):
        res = requests.post(f"http://{self.host}:{self.port}/send_ic/?fphone={str(number)}&fic={text}")

        return res
