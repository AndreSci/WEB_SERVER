from flask import Flask, render_template, request, make_response, jsonify

from misc.util import SettingsIni
from misc.logger import Logger
from misc.allow_ip import AllowedIP
from misc.util import app
from misc.send_sms import SendSMS

from database.requests.db_create_guest import CreateGuestDB
from database.requests.db_get_card_holders import CardHoldersDB

import asyncio
import threading
import time
import os
import requests
import socket
import fdb


def web_flask(logger: Logger, settings_ini: SettingsIni):
    """ Главная функция создания сервера Фласк. """
    set_ini = settings_ini.take_settings()

    allow_ip = AllowedIP()
    allow_ip.read_file(logger)

    print("Hello I'm WEB_INTERFACE flask")
    logger.add_log(f"SUCCESS\tweb_flask\t Сервер WEB_Flask начал сво работу")  # log

    @app.route('/DoAddIp', methods=['POST'])
    def add_ip():
        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_ip = request.remote_addr
        logger.add_log(f"EVENT\tDoAddIp запрос от ip: {user_ip}")

        if not allow_ip.find_ip(user_ip, logger, 2):  # Устанавливаем activity_lvl=2 для проверки уровня доступа
            pass
        else:
            json_request = request.json

            new_ip = json_request.get("ip")
            activity = int(json_request.get("activity"))

            allow_ip.add_ip(new_ip, logger, activity)

            json_replay["RESULT"] = "SUCCESS"
            json_replay["DESC"] = f"IP - {new_ip} добавлен с доступом {activity}", 200

        return jsonify(json_replay)

    # MAIN FUNCTION ------------------------------------------

    @app.route('/DoGetCardHolders', methods=['GET'])
    def get_employee():

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

    @app.route('/DoNewEmployee', methods=['POST'])
    def new_employee():

        res = request.json

        return "hello new_employee"

    @app.route('/DoCreateGuest', methods=['POST'])
    def create_guest():

        json_replay = {"RESULT": "SUCCESS", "DESC": "None", "DATA": "None"}

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
                sms.send_sms(json_request["FPhone"], json_request["FInviteCode"])

            if db_result["status"]:
                json_replay["DESC"] = "Пропуск добавлен в базу."
            else:
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = "Ошибка. Не удалось добавить пропуск."

        return jsonify(json_replay)

    @app.route('/DoDeleteEmployee', methods=['POST'])
    def delete_employee():
        res = request.json

        return "hello delete_employee"

    # --------------------------------------------------------

    # ЗАПУСК СЕРВЕРА С ПАРАМЕТРАМИ  <-------------------------
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
