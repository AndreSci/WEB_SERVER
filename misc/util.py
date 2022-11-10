import os
import configparser


class SettingsIni:

    def __init__(self):
        # general settings
        self.settings_ini = dict()
        self.settings_file = configparser.ConfigParser()

    def create_settings(self) -> dict:
        """ Функция получения настройки из файла settings.ini. """
        error_mess = 'Успешная загрузка данных из settings.ini'
        ret_value = dict()
        ret_value["result"] = False

        # проверяем файл settings.ini
        if os.path.isfile("settings.ini"):
            try:
                self.settings_file.read("settings.ini", encoding="utf-8")
                # general settings ----------------------------------------
                self.settings_ini["host"] = self.settings_file["GEN"]["HOST"]
                self.settings_ini["port"] = self.settings_file["GEN"]["PORT"]
                self.settings_ini["log_path"] = self.settings_file["GEN"]["LOG_PATH"]
                # sms settings---------------------------------------------
                self.settings_ini["sms_host"] = self.settings_file["SMS"]["HOST"]
                self.settings_ini["sms_port"] = self.settings_file["SMS"]["PORT"]
                # driver
                self.settings_ini["dr_host"] = self.settings_file["DRIVER"]["HOST"]
                self.settings_ini["dr_port"] = self.settings_file["DRIVER"]["PORT"]
                # helper
                self.settings_ini["hl_host"] = self.settings_file["HELPER"]["HOST"]
                self.settings_ini["hl_port"] = self.settings_file["HELPER"]["PORT"]

                ret_value["result"] = True

            except KeyError as ex:
                error_mess = f"Ошибка ключа - {ex}"

            except Exception as ex:
                error_mess = f"Общая ошибка - {ex}"
        else:
            error_mess = "Файл settings.ini не найден в корне проекта"

        ret_value["desc"] = error_mess

        return ret_value

    def take_settings(self):
        return self.settings_ini

    def take_log_path(self):
        return self.settings_ini["log_path"]
