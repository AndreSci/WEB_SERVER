import threading
import os
import configparser

from misc.logger import Logger


class AllowedIP:
    """ Класс configparser работает с str """

    def __init__(self):
        self.allow_ip = dict()
        self.TH_LOCK = threading.Lock()
        self.file = configparser.ConfigParser()

    def read_file(self, logger: Logger):
        """ Функция загрузки данных IP в словарь класса """

        with self.TH_LOCK:
            if os.path.isfile("allowed_ip.ini"):
                try:
                    # Загружаем данные из динамичного файла allowed_ip.ini
                    self.file.read("allowed_ip.ini", encoding="utf-8")

                    self.allow_ip = dict()  # Обнуляем словарь доступа

                    for key, val in self.file["CONNECTIONS"].items():
                        self.allow_ip[key] = int(val)

                except KeyError as ex:
                    logger.add_log(f"ERROR\tОшибка по ключу словаря - {ex}")
                except Exception as ex:
                    logger.add_log(f"ERROR\tException - {ex}")

    def find_ip(self, user_ip: str, logger: Logger, activity_lvl=1) -> bool:
        """ Функция поиска IP в словаре, если нет, \n
            вызывает функцию класса add_ip """
        ret_value = False

        self.read_file(logger)  # Подгружаем данные из файла

        if user_ip in self.allow_ip:
            if self.allow_ip[user_ip] >= activity_lvl:
                ret_value = True
        else:
            # Если нет IP добавляем его в файл и словарь класса
            self.add_ip(user_ip, logger)

        return ret_value

    def add_ip(self, new_ip: str, logger: Logger, activity=0) -> bool:
        """ Функция добавляет IP пользователя в файл со значением str(0)\n
            или если указан как allow_ip='1' """
        ret_value = False

        self.read_file(logger)  # Подгружаем данные из файла

        with self.TH_LOCK:  # Блокируем потоки

            self.file["CONNECTIONS"][new_ip] = str(activity)
            self.allow_ip[new_ip] = activity  # Обязательно должна быть строка

            if os.path.isfile("allowed_ip.ini"):
                try:
                    with open('allowed_ip.ini', 'w') as configfile:
                        self.file.write(configfile)

                    ret_value = True

                    logger.add_log(f"SUCCESS\tIP - {new_ip} добавлен в систему со значением {activity} ")
                except Exception as ex:
                    logger.add_log(f"ERROR\tОшибка открытия или записи в файл - {ex}")

        return ret_value
