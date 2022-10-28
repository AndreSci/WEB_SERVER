import requests


class SendSMS:
    """ Принимает словарь с настройками из settings.ini """
    def __init__(self, set_ini: dict):
        self.host = set_ini["sms_host"]
        self.port = set_ini["sms_port"]

    def send_sms(self, number, text):
        print("отправка смс")
        res = requests.post(f"http://{self.host}:{self.port}/send_ic/?fphone={str(number)}&fic={text}")
        print(res)
