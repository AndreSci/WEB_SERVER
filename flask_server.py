""" Made by Andrew Terleckii (2022\12\19) """

from flask import Flask, request, jsonify
import requests

from misc.util import SettingsIni
from misc.logger import Logger
from misc.allow_ip import AllowedIP
from misc.send_sms import SendSMS
from misc.car_number_test import NormalizeCar
from misc.errors.save_photo import ErrorPhoto
# from misc.block_logs import block_flask_logs
from face_id.resize_img import FlipImg

from database.requests.db_create_guest import CreateGuestDB
from database.requests.db_get_card_holders import CardHoldersDB
from database.requests.db_company import CompanyDB
from database.driver.rest_driver import ConDriver
from database.base_helper.helper import BSHelper


ERROR_ACCESS_IP = 'access_block_ip'
ERROR_READ_JSON = 'error_read_request'
ERROR_ON_SERVER = 'server_error'

# IP_HOST_APACS = '192.168.15.10'
IP_HOST_APACS = '127.0.0.1'
PORT_APACS = '8080'


def web_flask(logger: Logger, settings_ini: SettingsIni):
    """ Главная функция создания сервера Фласк. """
    app = Flask(__name__)  # Объявление сервера

    app.config['JSON_AS_ASCII'] = False

    # Блокируем сообщения фласк
    # block_flask_logs()

    set_ini = settings_ini.take_settings()

    allow_ip = AllowedIP()
    allow_ip.read_file(logger)

    print("Hello I'm WEB_INTERFACE flask")
    logger.add_log(f"SUCCESS\tweb_flask\t Сервер WEB_Flask начал свою работу")  # log

    # IP FUNCTION -----

    @app.route('/DoAddIp', methods=['POST'])
    def add_ip():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoAddIp запрос от ip: {user_ip}", print_it=False)

        if not allow_ip.find_ip(user_ip, logger, 2):  # Устанавливаем activity_lvl=2 для проверки уровня доступа
            json_replay["DESC"] = "Ошибка доступа по IP"
        else:

            if request.is_json:
                json_request = request.json

                new_ip = json_request.get("ip")
                activity = int(json_request.get("activity"))

                allow_ip.add_ip(new_ip, logger, activity)

                json_replay["RESULT"] = "SUCCESS"
                json_replay["DESC"] = f"IP - {new_ip} добавлен с доступом {activity}"
            else:
                logger.add_log(f"ERROR\tDoCreateGuest Не удалось прочитать Json из request")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = "Ошибка. Не удалось прочитать Json из request."

        return jsonify(json_replay)

    # MAIN FUNCTION ------

    @app.route('/DoCreateGuest', methods=['POST'])
    def create_guest():
        """ Добавляет посетителя в БД и отправляет смс если номер указан """

        json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoCreateGuest запрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:

            # Проверяем наличие Json
            if request.is_json:

                json_request = request.json

                logger.add_log(f"EVENT\tDoCreateGuest\tПолучены данные: ({json_request})", print_it=False)

                # Проверяем номер авто
                car_number = json_request.get("FCarNumber")

                if car_number:
                    norm_num = NormalizeCar()
                    car_number = norm_num.do_normal(car_number)

                    json_request['FCarNumber'] = car_number

                # Результат из БД
                db_result = CreateGuestDB.add_guest(json_request, logger)

                # отправляем СМС если есть номер телефона в заявке
                if json_request.get("FPhone") and db_result["status"] == 'SUCCESS':

                    sms = SendSMS(set_ini)
                    try:
                        sms.send_sms(json_request["FPhone"], json_request["FInviteCode"])
                        logger.add_log(f"EVENT\tОтправлен запрос на отправку СМС: {json_request['FPhone']}")
                    except Exception as ex:
                        logger.add_log(f"ERROR\tDoCreateGuest ошибка отправки СМС: {ex}")

                json_replay["RESULT"] = db_result["status"]
                json_replay["DESC"] = db_result["desc"]
                json_replay["DATA"] = db_result["data"]

            else:
                # Если в запросе нет Json данных
                logger.add_log(f"ERROR\tDoCreateGuest ошибка чтения Json: В запросе нет Json")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = ERROR_READ_JSON

        return jsonify(json_replay)

    @app.route('/DoGetCardHolders', methods=['GET'])
    def get_card_holder():
        """ Функция возвращает список сотрудников компании """

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoGetCardHolders запрос от ip: {user_ip}", print_it=False)

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:
            json_request = dict()

            # Проверяем запрос на Json
            if request.is_json:
                json_request = request.json
            else:
                json_request['FAccountID'] = request.args.get("FAccountID")
                json_request['FINN'] = request.args.get("FINN")

            if not json_request['FAccountID']:
                logger.add_log(f"ERROR\tDoGetCardHolders - Не удалось прочитать args/data из request")
                json_replay["DESC"] = "Ошибка. Не удалось прочитать args/data из request."
            else:

                account_id = json_request.get("FAccountID")
                finn = json_request.get("FINN")

                logger.add_log(f"EVENT\tDoGetCardHolders\tПолучены данные: ("
                               f"FINN: {finn} "
                               f"FAccountID: {account_id})", print_it=False)

                con_db = CardHoldersDB()

                # Запрос в БД sac3
                db_sac3 = CardHoldersDB.get_sac3(account_id, logger)

                if db_sac3["status"]:

                    # Запрос в БД FIREBIRD
                    db_fdb = con_db.get_fdb(finn, logger)

                    json_replay["DESC"] = db_fdb["desc"]

                    if db_fdb["status"]:
                        json_replay["RESULT"] = "SUCCESS"
                        # json_replay["DATA"] = db_fdb["data"]

                        list_id = list()

                        # создаем список fid для получения списка сотрудников из базы лиц
                        for it in db_fdb['data']:
                            list_id.append(it["fid"])

                        face_db = con_db.get_with_face(list_id, logger)

                        ret_list_id = list()

                        # Перезаписываем в новый лист данные пользователей с полем isphoto
                        for it in db_fdb["data"]:
                            if it["fid"] in str(face_db['data']):
                                it['isphoto'] = 1
                            else:
                                it['isphoto'] = 0

                            ret_list_id.append(it)

                        json_replay["DATA"] = ret_list_id

                else:
                    json_replay["DESC"] = db_sac3["desc"]

        return jsonify(json_replay)

    @app.route('/DoAddEmployeePhoto', methods=['POST'])
    def add_employee_photo():
        """ Добавляет сотрудника с фото лица в терминалы """

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoAddEmployeePhoto\tзапрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:
            # Проверяем наличие Json в запросе
            if request.is_json:
                res_json = request.json
                logger.add_log(f"EVENT\tDoAddEmployeePhoto\tПолучены данные: (id: {res_json.get('id')})")

                con_helper = BSHelper(set_ini)

                # Отправляем запрос на получение данных сотрудника
                res_base_helper = con_helper.get_card_holder(res_json, logger)
                result = res_base_helper.get("RESULT")

                logger.add_log(f"EVENT\tDoAddEmployeePhoto\tПосле BaseHelper "
                                f"json: {res_base_helper['DATA'].get('id')} - {res_base_helper['DATA'].get('name')}",
                                print_it=False)

                if result == "SUCCESS" or result == "WARNING":

                    res_json["id"] = res_base_helper["DATA"].get("id")
                    res_json["name"] = res_base_helper["DATA"].get("name")

                    # Проверяем и меняем, если нужно, размер фото (максимальный размер изначально 1080p.)
                    FlipImg.convert_img(res_json, logger)

                    # подключаемся к драйверу Распознания лиц
                    connect_driver = ConDriver(set_ini)
                    res_driver = connect_driver.add_person_with_face(res_json, logger)

                    if res_driver["RESULT"] == "ERROR":
                        json_replay['DATA'] = res_driver['DATA']
                        result = 'DRIVER'

                        # отменяем заявку в базе через base_helper
                        con_helper.deactivate_person(res_json, logger)
                        logger.add_log(f"WARNING\tDoAddEmployeePhoto\tОтмена пропуска в BaseHelper "
                                       f"из-за ошибки на Драйвере распознания лиц")

                        # Сохраняем фото в log_path где папка photo_errors
                        ErrorPhoto.save(res_json, settings_ini.take_log_path(), logger)

                if result == "EXCEPTION":
                    pass
                else:
                    # Незначительная нагрузка
                    json_replay["DESC"] = res_base_helper["DESC"]

                # Задумка на случай добавления ситуаций
                if result == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                elif result == "ERROR":
                    logger.add_log(f"ERROR\tDoAddEmployeePhoto\t{json_replay['DESC']}")
                elif result == "EXCEPTION":
                    pass
                elif result == "DRIVER":

                    # Вариации ошибок связанные с фото и перевод их на русский язык
                    try:
                        if 'Photo registered' == json_replay['DATA']['msg']:
                            str_msg = "Лицо уже зарегистрировано"
                        elif 'Face deflection angle is too large' == json_replay['DATA']['msg']:
                            str_msg = "Неудачное расположение лица на фото"
                        elif 'Face clarity is too low' == json_replay['DATA']['msg']:
                            str_msg = "На фото плохо видно лицо"
                        elif 'Registered photo size cannot exceed 2M' == json_replay['DATA']['msg']:
                            str_msg = "Фото слишком большого размера"
                        elif 'Face too large or incomplete' == json_replay['DATA']['msg']:
                            str_msg = "Лицо слишком большое или неполное"
                        elif 'The registered photo resolution is greater than 1080p' == json_replay['DATA']['msg']:
                            str_msg = "Размер фото слишком высоко (требуется не выше 1080р)"
                        else:
                            str_msg = "Не удалось распознать лицо на фото"

                        json_replay["DESC"] = f"Не удалось добавить фотографию в систему: {str_msg}"

                    except Exception as ex:
                        logger.add_log(f"ERROR\tDoAddEmployeePhoto\tНе удалось получить данные из ответа Драйвера {ex}")
                        json_replay["DESC"] = f"При добавлении фото произошла ошибка"

                elif result == "WARNING":
                    logger.add_log(f"WARNING\tDoAddEmployeePhoto\t{json_replay['DESC']}")
                elif result == "NotDefined":
                    logger.add_log(f"WARNING\tDoAddEmployeePhoto\t{json_replay['DESC']}")
                else:
                    pass

            else:
                logger.add_log(f"ERROR\tDoAddEmployeePhoto\tОшибка, в запросе нет Json данных: {ERROR_READ_JSON}")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = f"Ошибка на сервере: {ERROR_READ_JSON}"

        return jsonify(json_replay)

    @app.route('/DoDeletePhoto', methods=['POST'])
    def delete_person():
        json_replay = {"RESULT": "ERROR", "DESC": ERROR_ON_SERVER, "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoDeletePhoto запрос от ip: {user_ip}", print_it=False)

        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:
            try:
                res_json = request.json

                logger.add_log(f"EVENT\tDoDeletePhoto\tПолучены данные: ("
                               f"id: {res_json.get('id')})")

                # Отправляем запрос на удаление данных сотрудника
                con_helper = BSHelper(set_ini)
                res_base_helper = con_helper.deactivate_person_apacsid(res_json, logger)
                result = res_base_helper.get("RESULT")

                if result == "SUCCESS" or result == "WARNING":
                    res_json["id"] = res_base_helper["DATA"].get("id")
                    res_json["name"] = res_base_helper["DATA"].get("name")

                    # создаем и подключаемся к драйверу Коли
                    connect_driver = ConDriver(set_ini)
                    res_driver = connect_driver.delete_person(res_json, logger)

                    if res_driver['RESULT'] == "SUCCESS":
                        json_replay["RESULT"] = "SUCCESS"
                        json_replay["DESC"] = f"Пропуск успешно удалена."
                    else:
                        json_replay['DESC'] = res_driver['DESC']

                else:
                    logger.add_log(f"ERROR\tDoDeletePhoto\tBaseHelper DESC: {res_base_helper.get('DESC')}, "
                                   f"DATA: {res_base_helper.get('DATA')}")

            except Exception as ex:
                json_replay['DESC'] = ERROR_READ_JSON
                logger.add_log(f"ERROR\tDoDeletePhoto\tИсключение вызвало {ex}")

        return jsonify(json_replay)

    # DRIVER FUNCTION ------

    @app.route('/DoAddPerson', methods=['POST'])
    def add_person():
        """ Добавляет персону в терминалы без фото """

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoAddGuest запрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:
            try:
                res_json = request.json

                # создаем и подключаемся к драйверу Коли
                connect_driver = ConDriver(set_ini)
                result = connect_driver.add_person(res_json, logger)

                if result == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                    json_replay["DESC"] = f"Персона успешно добавлена."
                else:
                    json_replay["DESC"] = f"Драйвер ответил ошибкой."

            except Exception as ex:
                json_replay['DESC'] = "Ошибка чтения Json из запроса"
                logger.add_log(f"ERROR\tDoAddGuest\tИсключение вызвало чтение Json из запроса {ex}")

        return jsonify(json_replay)

    @app.route('/DoUpdatePerson', methods=['POST'])
    def update_guest_driver():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoUpdateGuest запрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:
            try:
                res_json = request.json

                # создаем и подключаемся к драйверу Коли
                connect_driver = ConDriver(set_ini)
                result = connect_driver.update_person(res_json, logger)

                if result == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                    json_replay["DESC"] = f"Персона успешно обновлена."
                else:
                    json_replay["DESC"] = f"Драйвер ответил ошибкой."

            except Exception as ex:
                json_replay['DESC'] = "Ошибка чтения Json из запроса"
                logger.add_log(f"ERROR\tDoUpdateGuest\tИсключение вызвало чтение Json из запроса {ex}")

        return jsonify(json_replay)

    @app.route('/DoAddPhoto', methods=['POST'])
    def add_new_photo_driver():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoAddPhoto запрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:
            try:
                res_json = request.json

                # создаем и подключаемся к драйверу Коли
                connect_driver = ConDriver(set_ini)
                result = connect_driver.add_face(res_json, logger)

                if result['RESULT'] == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                    json_replay["DESC"] = f"Фотография успешно добавлена."
                else:
                    json_replay = result

            except Exception as ex:
                json_replay['DESC'] = "Ошибка чтения Json из запроса"
                logger.add_log(f"ERROR\tDoAddPhoto Исключение вызвало чтение Json из запроса {ex}")

        return jsonify(json_replay)

    # EMPLOYEE ----

    @app.route('/DoCreateCardHolder', methods=['POST'])
    def create_card_holder():
        """ Добавляет сотрудника в БД Apacs3000,\n
        запрашивает добавление пропуска по лицу через requests в DoAddEmployeePhoto"""

        json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoCreateCardHolder запрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:

            # Проверяем наличие Json
            if request.is_json:

                json_request = request.json

                first_name = json_request.get("First_Name")
                last_name = json_request.get("Last_Name")
                middle_name = json_request.get("Middle_Name")
                str_inn = json_request.get("inn")
                car_number = json_request.get("Car_Number")
                photo_img64 = 0

                try:
                    photo_img64 = len(json_request['img64'])
                except Exception as ex:
                    logger.add_log(f"ERROR\tDoCreateCardHolder\tОшибка подсчета размера фотографии img64: {ex}")

                logger.add_log(f"EVENT\tDoCreateCardHolder\tПолучены данные: ("
                               f"First_Name: {first_name} "
                               f"Last_Name: {last_name} "
                               f"Middle_Name: {middle_name} "
                               f"inn: {str_inn} "
                               f"Car_Number: {car_number} "
                               f"img64_size: {photo_img64})", print_it=False)

                if not middle_name:
                    middle_name = ''

                if not car_number:
                    car_number = ''
                else:
                    car_number = str(car_number).upper().replace(' ', '')

                try:
                    res = requests.get(f'http://{set_ini["host_apacs_i"]}:{set_ini["port_apacs_i"]}/CreateEmployee'
                                       f'?First_Name={first_name}'
                                       f'&Last_Name={last_name}'
                                       f'&Middle_Name={middle_name}'
                                       f'&INN={str_inn}'
                                       f'&Car_Number={car_number}')

                    json_create = res.json()

                    if json_create["RESULT"] == "SUCCESS":

                        # Получаем id пользователя из системного адреса (HEX) в (DEC)
                        sys_addr_id = json_create['DATA']['sysAddrID']
                        sys_addr_id = sys_addr_id[8:]

                        json_empl = dict()

                        json_empl['id'] = int(sys_addr_id, 16)
                        json_empl['img64'] = json_request.get("img64")

                        res_add_photo = requests.post(f"http://127.0.0.1:{set_ini['port']}/DoAddEmployeePhoto",
                                                      json=json_empl)

                        if res_add_photo.status_code == 200:
                            res_add_photo = res_add_photo.json()

                            if res_add_photo['RESULT'] == "SUCCESS":

                                json_replay['DESC'] = "Успешно создан сотрудник"
                                logger.add_log(f"EVENT\tDoCreateCardHolder Успешно создан сотрудник для ИНН{str_inn}")
                            else:
                                json_replay['RESULT'] = "WARNING"
                                json_replay['DESC'] = "Сотрудник создан. " \
                                                      f"Ошибка: {res_add_photo['DESC']}"

                            json_replay['DATA'] = {'id': json_empl['id']}
                    else:
                        logger.add_log(f"WARNING\tDoCreateCardHolder "
                                       f"Интерфейс Apacs ответил отказом на запрос создания сотрудника "
                                       f"JSON: {json_request}")

                        json_replay["RESULT"] = 'ERROR'
                        json_replay['DATA'] = json_create["DATA"]
                        json_replay['DESC'] = json_create["DESC"]

                except Exception as ex:
                    logger.add_log(f"ERROR\tDoCreateCardHolder ошибка обращения к интерфейсу Apacs3000: {ex}")
                    json_replay["RESULT"] = "ERROR"
                    json_replay["DESC"] = "Ошибка в работе системы"

            else:
                # Если в запросе нет Json данных
                logger.add_log(f"ERROR\tDoCreateCardHolder ошибка чтения Json: В запросе нет Json")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = "Ошибка в работе системы"

        return jsonify(json_replay)

    @app.route('/DoDeleteCardHolder', methods=['POST'])
    def delete_card_holder():
        """ Удаляет сотрудника из БД Принимает id он же Apacs_id и inn компании"""

        # создаем и подключаемся к драйверу Коли
        # connect_driver = ConDriver(set_ini)
        # res_driver = connect_driver.delete_person({"id": 2450}, logger)

        json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoDeleteCardHolder запрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:

            # Проверяем наличие Json
            if request.is_json:

                json_request = request.json

                str_inn = json_request.get("inn")
                str_fid = json_request.get("id")    # (он же Apacs_id или RemoteID)

                logger.add_log(f"EVENT\tDoDeleteCardHolder\tПолучены данные: ("
                               f"fid: {str_fid} "
                               f"inn: {str_inn})", print_it=False)

                try:
                    res = requests.delete(f'http://{set_ini["host_apacs_i"]}:{set_ini["port_apacs_i"]}/DeleteEmployee'
                                           f'?INN={str_inn}'
                                           f'&FID={str_fid}')

                    try:
                        json_create = res.json()

                        if json_create['RESULT'] == "ERROR":
                            json_replay["RESULT"] = "ERROR"
                            json_replay["DESC"] = json_create["DESC"]
                            json_replay['DATA'] = json_create["DATA"]

                            logger.add_log(f"ERROR\tDoDeleteCardHolder "
                                           f"Не удалось удалить сотрудника в системе Апакс3000: {json_create['DESC']}")
                        else:
                            # Отправляем запрос на удаление данных сотрудника

                            result = requests.post(f"http://127.0.0.1:{set_ini['port']}/DoDeletePhoto",
                                                   json=json_request)
                            result = result.json()

                            # con_helper = BSHelper(set_ini)
                            # res_base_helper = con_helper.deactivate_person_apacsid({"id": str_fid}, logger)
                            # result = res_base_helper.get("RESULT")

                            if result['RESULT'] == "ERROR":
                                json_replay["RESULT"] = "WARNING"
                                json_replay["DESC"] = "Сотрудник успешно удалён. " \
                                                      "Не удалось заблокировать пропуск сотрудника"
                                json_replay['DATA'] = result

                    except Exception as ex:
                        logger.add_log(f"ERROR\tDoDeleteCardHolder Ошибка обращения к интерфейсу Apacs3000: {ex}")
                        json_replay["RESULT"] = "ERROR"
                        json_replay["DESC"] = "Ошибка в работе системы"

                except Exception as ex:
                    logger.add_log(f"ERROR\tDoDeleteCardHolder Ошибка обращения к интерфейсу Apacs3000: {ex}")
                    json_replay["RESULT"] = "ERROR"
                    json_replay["DESC"] = "Ошибка в работе системы"

            else:
                # Если в запросе нет Json данных
                logger.add_log(f"ERROR\tDoDeleteCardHolder ошибка чтения Json: В запросе нет Json")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = "Ошибка в работе системы"

        return jsonify(json_replay)

    @app.route('/GetBlockCar', methods=['GET'])
    def get_block_car():
        """ Получает информацию о возможности открытия пропусков на авто """
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tGetBlockCar запрос от ip: {user_ip}", print_it=False)

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:

            try:
                json_request = request.json

                com_fid = json_request.get("id")
                # inn = json_request.get("inn") убран из-за лишней нагрузки

                logger.add_log(f"EVENT\tGetBlockCar\tПолучены данные: (id: {com_fid})", print_it=False)

                json_replay = CompanyDB.get_block_car(com_fid, logger)

            except Exception as ex:
                # Если в запросе нет Json данных
                logger.add_log(f"ERROR\tGetBlockCar ошибка чтения Json: В запросе нет {ex}")
                json_replay["DESC"] = "Ошибка в работе системы"

        return jsonify(json_replay)

    # RUN SERVER FLASK  ------
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
