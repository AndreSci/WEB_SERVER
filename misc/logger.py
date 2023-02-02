import threading
import os
import datetime
from misc.util import SettingsIni


class BColors:
    """ Класс вариантов цвета для текста в консоли """
    col_header = '\033[95m'
    col_okblue = '\033[94m'
    col_okcyan = '\033[96m'
    col_okgreen = '\033[92m'
    col_warning = '\033[93m'
    col_fail = '\033[91m'
    col_endc = '\033[0m'
    col_bold = '\033[1m'
    col_underline = '\033[4m'


def test_dir(log_path):
    ret_value = True

    try:
        if not os.path.exists(log_path):  # Если нет директории log_path пробуем её создать.
            os.makedirs(log_path)
            print(f"Была создана директория для лог-фалов: {log_path}")
    except Exception as ex:
        print(ex)
        ret_value = False

    return ret_value


class Logger:

    def __init__(self, class_settings: SettingsIni):
        self.set_ini = class_settings
        self.font_color = False
        self.log_guard = threading.Lock()

    def add_log(self, text: str, print_it=True):
        """ Обшивает текст датой, табуляцией и переходом на новую строку.
            Переменная print_it определяет нужно ли выводить в консоль лог, где True выводить в консоль."""
        ret_value = False

        log_path = self.set_ini.take_log_path()
        today = datetime.datetime.today()

        for_file_name = str(today.strftime("%Y-%m-%d"))

        date_time = str(today.strftime("%Y-%m-%d-%H.%M.%S"))
        # Создаем лог
        mess = date_time + "\t" + text + "\n"

        if test_dir(log_path):
            with self.log_guard:  # Защищаем поток

                if print_it:
                    # print(date_time + "\t" + text)
                    if 'ERROR' == text[:5]:
                        print(f"{BColors.col_fail}{date_time}\t{text}{BColors.col_endc}")
                    elif 'WARNING' == text[:7]:
                        print(f"{BColors.col_warning}{date_time}\t{text}{BColors.col_endc}")
                    else:
                        print(date_time + "\t" + text)

                # Открываем и записываем логи в файл отчета.
                with open(f'{log_path}{for_file_name}.log', 'a', encoding='utf-8') as file:
                    file.write(mess)
                    ret_value = True

        return ret_value
