from flask import Flask, render_template, request, make_response, jsonify

from misc.util import SettingsIni
from misc.logger import Logger
from misc.allow_ip import AllowedIP
from misc.send_sms import SendSMS

from database.requests.db_create_guest import CreateGuestDB
from database.requests.db_get_card_holders import CardHoldersDB
from database.driver.rest_driver import ConDriver


def web_flask(logger: Logger, settings_ini: SettingsIni):
    """ Главная функция создания сервера Фласк. """
    app = Flask(__name__)  # Обьявления сервера

    set_ini = settings_ini.take_settings()

    allow_ip = AllowedIP()
    allow_ip.read_file(logger)

    print("Hello I'm WEB_INTERFACE flask")
    logger.add_log(f"SUCCESS\tweb_flask\t Сервер WEB_Flask начал свою работу")  # log

    @app.route('/DoAddIp', methods=['POST'])
    def add_ip():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoAddIp запрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger, 2):  # Устанавливаем activity_lvl=2 для проверки уровня доступа

            json_replay["DESC"] = "Ошибка доступа по IP"
        else:
            json_request = request.json

            new_ip = json_request.get("ip")
            activity = int(json_request.get("activity"))

            allow_ip.add_ip(new_ip, logger, activity)

            json_replay["RESULT"] = "SUCCESS"
            json_replay["DESC"] = f"IP - {new_ip} добавлен с доступом {activity}"

        return jsonify(json_replay)

    # MAIN FUNCTION ------------------------------------------

    @app.route('/DoGetCardHolders', methods=['GET'])
    def get_card_holder():

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoGetCardHolders запрос от ip: {user_ip}")

        json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

        if not allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = "Ошибка доступа по IP"
        else:
            json_request = request.json
            account_id = json_request.get("FAccountID")
            finn = json_request.get("FINN")

            # Запрос в БД sac3
            db_sac3 = CardHoldersDB.get_sac3(account_id, logger)

            if db_sac3["status"]:

                # Запрос в БД FIREBIRD
                db_fdb = CardHoldersDB.get_fdb(finn, logger)

                json_replay["DESC"] = db_fdb["desc"]

                if db_fdb["status"]:
                    json_replay["DATA"] = db_fdb["data"]
                else:
                    json_replay["RESULT"] = "ERROR"
            else:
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = db_sac3["desc"]

        return jsonify(json_replay)

    @app.route('/DoAddGuest', methods=['POST'])
    def add_guest():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoAddGuest запрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = "Ошибка доступа по IP"
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

    @app.route('/DoAddGuestWithFace', methods=['POST'])
    def add_guest_with_face():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoAddGuestWithFace запрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = "Ошибка доступа по IP"
        else:
            try:
                res_json = request.json

                # создаем и подключаемся к драйверу Коли
                connect_driver = ConDriver(set_ini)
                result = connect_driver.add_person_with_face(res_json, logger)

                if result == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                    json_replay["DESC"] = f"Персона успешно добавлена."
                else:
                    json_replay["DESC"] = f"Драйвер ответил ошибкой."

            except Exception as ex:
                json_replay['DESC'] = "Ошибка чтения Json из запроса"
                logger.add_log(f"ERROR\tDoAddGuestWithFace\tИсключение вызвало чтение Json из запроса {ex}")

        return jsonify(json_replay)

    @app.route('/DoUpdateGuest', methods=['POST'])
    def update_guest():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoUpdateGuest запрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = "Ошибка доступа по IP"
        else:
            try:
                res_json = request.json

                # создаем и подключаемся к драйверу Коли
                connect_driver = ConDriver(set_ini)
                result = connect_driver.update_person(res_json, logger)

                if result == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                    json_replay["DESC"] = f"Персона успешно добавлена."
                else:
                    json_replay["DESC"] = f"Драйвер ответил ошибкой."

            except Exception as ex:
                json_replay['DESC'] = "Ошибка чтения Json из запроса"
                logger.add_log(f"ERROR\tDoUpdateGuest\tИсключение вызвало чтение Json из запроса {ex}")

        return jsonify(json_replay)

    @app.route('/DoCreateGuest', methods=['POST'])
    def create_guest():

        json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoCreateGuest запрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = "Ошибка доступа по IP"
        else:
            json_request = request.json
            # Результат из БД
            db_result = CreateGuestDB.add_guest(json_request, logger)

            if json_request.get("FPhone") and db_result["status"]:

                sms = SendSMS(set_ini)
                try:
                    sms.send_sms(json_request["FPhone"], json_request["FInviteCode"])
                except Exception as ex:
                    logger.add_log(f"ERROR\tDoCreateGuest ошибка отправки СМС: {ex}")

            if db_result["status"]:
                json_replay["DESC"] = "Пропуск добавлен в базу."
            else:
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = "Ошибка. Не удалось добавить пропуск."

        return jsonify(json_replay)

    @app.route('/DoDeleteGuest', methods=['POST'])
    def delete_guest():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoDeleteGuest запрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = "Ошибка доступа по IP"
        else:
            try:
                res_json = request.json

                # создаем и подключаемся к драйверу Коли
                connect_driver = ConDriver(set_ini)
                result = connect_driver.delete_person(res_json, logger)

                if result == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                    json_replay["DESC"] = f"Персона успешно добавлена."
                else:
                    json_replay["DESC"] = f"Драйвер ответил ошибкой."

            except Exception as ex:
                json_replay['DESC'] = "Ошибка чтения Json из запроса"
                logger.add_log(f"ERROR\tDoDeleteGuest\tИсключение вызвало чтение Json из запроса {ex}")

        return jsonify(json_replay)

    @app.route('/DoOnPhoto', methods=['POST'])
    def add_new_photo():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoOnPhoto запрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger):
            json_replay["DESC"] = "Ошибка доступа по IP"
        else:
            try:
                res_json = request.json

                # создаем и подключаемся к драйверу Коли
                connect_driver = ConDriver(set_ini)
                result = connect_driver.send_photo(res_json, logger)

                if result == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                    json_replay["DESC"] = f"Фотография успешно добавлена."
                else:
                    json_replay["DESC"] = f"Драйвер ответил ошибкой."

            except Exception as ex:
                json_replay['DESC'] = "Ошибка чтения Json из запроса"
                logger.add_log(f"ERROR\tDoOnPhoto\tИсключение вызвало чтение Json из запроса {ex}")

        return jsonify(json_replay)

    # --------------------------------------------------------

    # ЗАПУСК СЕРВЕРА С ПАРАМЕТРАМИ  <-------------------------
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
