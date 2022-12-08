from flask import Flask, render_template, request, make_response, jsonify
import requests

from misc.util import SettingsIni
from misc.logger import Logger
from misc.allow_ip import AllowedIP
from misc.send_sms import SendSMS
from misc.car_number_test import NormalizeCar
from misc.block_logs import block_flask_logs

from database.requests.db_create_guest import CreateGuestDB
from database.requests.db_get_card_holders import CardHoldersDB
from database.driver.rest_driver import ConDriver
from database.base_helper.helper import BSHelper


ERROR_ACCESS_IP = 'access_block_ip'
ERROR_READ_JSON = 'error_read_request'
ERROR_ON_SERVER = 'server_error'


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
        logger.add_log(f"EVENT\tDoAddIp запрос от ip: {user_ip}")

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
        logger.add_log(f"EVENT\tDoCreateGuest запрос от ip: {user_ip}")

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:

            # Проверяем наличие Json
            if request.is_json:

                json_request = request.json
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
        logger.add_log(f"EVENT\tDoGetCardHolders запрос от ip: {user_ip}")

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
        """ Добавляет сотрудника в терминалы с фото лица """

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoAddEmployeePhoto\tзапрос от ip: {user_ip}")

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:
            # Проверяем наличие Json в запросе
            if request.is_json:
                res_json = request.json

                con_helper = BSHelper(set_ini)

                # Отправляем запрос на получение данных сотрудника
                logger.add_log(f"EVENT\tDoAddEmployeePhoto\tПолучен json: {res_json.get('id')}")
                res_base_helper = con_helper.get_card_holder(res_json, logger)
                result = res_base_helper.get("RESULT")

                logger.add_log(f"EVENT\tDoAddEmployeePhoto\tПосле BaseHelper "
                               f"json: {res_base_helper['DATA'].get('id')} - {res_base_helper['DATA'].get('name')}")

                if result == "SUCCESS":

                    res_json["id"] = res_base_helper["DATA"].get("id")
                    res_json["name"] = res_base_helper["DATA"].get("name")
                    # создаем и подключаемся к драйверу Коли
                    connect_driver = ConDriver(set_ini)

                    res_driver = connect_driver.add_person_with_face(res_json, logger)

                    if res_driver["RESULT"] == "ERROR":
                        logger.add_log(f"ERROR\tDoAddEmployeePhoto\t2: Ошибка добавления фото {res_driver['DATA']}")
                        result = 'DRIVER'

                        # отменяем заявку в базе через base_helper
                        con_helper.deactivate_person(res_json, logger)

                if result == "EXCEPTION":
                    pass
                else:
                    # Незначительная нагрузка
                    json_replay["DESC"] = res_base_helper["DESC"]

                # Задумка на случай добавления ситуаций
                if result == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                elif result == "ERROR":
                    logger.add_log(f"ERROR\tDoAddEmployeePhoto\t3: {json_replay['DESC']}")
                elif result == "EXCEPTION":
                    pass
                elif result == "DRIVER":
                    json_replay["DESC"] = f"При добавлении фото произошла ошибка"
                elif result == "WARNING":
                    logger.add_log(f"WARNING\tDoAddEmployeePhoto\t4: {json_replay['DESC']}")
                elif result == "NotDefined":
                    logger.add_log(f"WARNING\tDoAddEmployeePhoto\t5: {json_replay['DESC']}")
                else:
                    pass

            else:
                logger.add_log(f"ERROR\tDoAddEmployeePhoto\t6: {ERROR_READ_JSON}")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = f"Ошибка. {ERROR_READ_JSON}"

        return jsonify(json_replay)

    @app.route('/DoDeletePhoto', methods=['POST'])
    def delete_person():
        json_replay = {"RESULT": "ERROR", "DESC": ERROR_ON_SERVER, "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoDeletePhoto запрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:
            try:
                res_json = request.json

                con_helper = BSHelper(set_ini)

                # Отправляем запрос на удаление данных сотрудника
                res_base_helper = con_helper.deactivate_person_apacsid(res_json, logger)
                result = res_base_helper.get("RESULT")

                if result == "SUCCESS":
                    res_json["id"] = res_base_helper["DATA"].get("id")
                    res_json["name"] = res_base_helper["DATA"].get("name")

                    # создаем и подключаемся к драйверу Коли
                    connect_driver = ConDriver(set_ini)
                    res_driver = connect_driver.delete_person(res_json, logger)

                    if res_driver == "SUCCESS":
                        json_replay["RESULT"] = "SUCCESS"
                        json_replay["DESC"] = f"Пропуск успешно удалена."
                        logger.add_log(f"SUCCESS\tDoDeletePhoto\tПропуск для id: {res_json['id']} успешно удален.")

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
        logger.add_log(f"EVENT\tDoAddGuest запрос от ip: {user_ip}")

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
        logger.add_log(f"EVENT\tDoUpdateGuest запрос от ip: {user_ip}")

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
        logger.add_log(f"EVENT\tDoOnPhoto запрос от ip: {user_ip}")

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:
            try:
                res_json = request.json

                # создаем и подключаемся к драйверу Коли
                connect_driver = ConDriver(set_ini)
                result = connect_driver.add_face(res_json, logger)

                if result == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                    json_replay["DESC"] = f"Фотография успешно добавлена."
                else:
                    json_replay["DESC"] = f"Драйвер ответил ошибкой."

            except Exception as ex:
                json_replay['DESC'] = "Ошибка чтения Json из запроса"
                logger.add_log(f"ERROR\tDoOnPhoto Исключение вызвало чтение Json из запроса {ex}")

        return jsonify(json_replay)

    # EMPLOYEE ----

    @app.route('/DoCreateEmployee', methods=['POST'])   # TODO добавить сотрудника в компанию
    def create_employee():
        """ Добавляет посетителя в БД и отправляет смс если номер указан """

        json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoCreateGuest запрос от ip: {user_ip}")

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:

            # Проверяем наличие Json
            if request.is_json:

                json_request = request.json

                pass

            else:
                # Если в запросе нет Json данных
                logger.add_log(f"ERROR\tDoCreateEmployee ошибка чтения Json: В запросе нет Json")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = ERROR_READ_JSON

        return jsonify(json_replay)

    @app.route('/DoDeleteEmployee', methods=['POST'])   # TODO удалить сотрудника из компании
    def delete_employee():
        """ Добавляет посетителя в БД и отправляет смс если номер указан """

        json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoDeleteEmployee запрос от ip: {user_ip}")

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:

            # Проверяем наличие Json
            if request.is_json:

                json_request = request.json

                pass

            else:
                # Если в запросе нет Json данных
                logger.add_log(f"ERROR\tDoDeleteEmployee ошибка чтения Json: В запросе нет Json")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = ERROR_READ_JSON

        return jsonify(json_replay)

    @app.route('/GetBlockCar', methods=['GET'])     # TODO получать информацию блока авто для личного кабинета
    def get_block_car():
        """ Добавляет посетителя в БД и отправляет смс если номер указан """

        json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoCreateGuest запрос от ip: {user_ip}")

        # Проверяем разрешен ли доступ для IP
        if not allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = ERROR_ACCESS_IP
        else:

            # Проверяем наличие Json
            if request.is_json:

                json_request = request.json

                pass

            else:
                # Если в запросе нет Json данных
                logger.add_log(f"ERROR\tDoCreateGuest ошибка чтения Json: В запросе нет Json")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = ERROR_READ_JSON

        return jsonify(json_replay)

    # RUN SERVER FLASK  ------
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
