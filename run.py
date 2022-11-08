from misc.util import SettingsIni
from misc.logger import Logger
from flask_server import web_flask
import time
import ctypes


def main():

    # Подгружаем данные из settings.ini
    settings = SettingsIni()
    result = settings.create_settings()

    port = settings.settings_ini["port"]

    # Меняем имя терминала
    ctypes.windll.kernel32.SetConsoleTitleW(f"REST API interface port: {port}")

    # Обьявляем логирование
    logger = Logger(settings)

    # Проверка успешности загрузки данных
    if not result["result"]:
        print("Ошибка запуска сервиса - " + result["desc"] + "\nПрограмма закроется через 10 сек.")
        time.sleep(10)
        return

    web_flask(logger, settings)


if __name__ == '__main__':
    main()
