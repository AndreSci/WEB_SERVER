from flask import Flask, render_template, request, make_response, jsonify

from misc.util import SettingsIni
from misc.logger import Logger
from misc.allow_ip import AllowedIP
from misc.util import app
from misc.send_sms import SendSMS

from database.requests.db_create_guest import CreateGuestDB

import asyncio
import threading
import time
import os
import requests
import socket


def web_flask(logger: Logger, settings_ini: SettingsIni):
    """ Главная функция создания сервера Фласк.
        По стандарту сервер фласк будет создаваться на local с портом 8055
        """
    set_ini = settings_ini.take_settings()

    allow_ip = AllowedIP()
    allow_ip.read_file(logger)

    print("Hello I'm WEB_Flask")
    logger.add_log(f"SUCCESS\tweb_flask\t Сервер WEB_Flask начал сво работу")  # log

    @app.route('/test_server/', methods=['GET'])
    def test_server():
        """ Просто функция проверки сервера """

        res = request.json

        json_data = {"f_first_name": "Name", "f_last_name": "Last", "f_middle_name": "Middle", "request": res["12"]}
        time.sleep(20)
        logger.add_log(f"SUCCESS\tweb_flask\t server test is OK!")  # log

        return jsonify(json_data)

    @app.route('/test_server1/', methods=['GET'])
    def test_server1():
        """ Просто функция проверки сервера """

        res = request.json

        json_data = {"f_first_name": "Name", "f_last_name": "Last", "f_middle_name": "Middle", "request": res["12"]}

        logger.add_log(f"SUCCESS\tweb_flask\t server test is OK!")  # log

        return jsonify(json_data)

    @app.route('/DoAddIp', methods=['POST'])
    def add_ip():
        # json_replay = {"RESULT": "NOT_ALLOWED", "DESC": "None", "DATA": "None"}

        user_ip = request.remote_addr

        if not allow_ip.find_ip(user_ip, logger, '2'):
            return "ERROR"
        else:
            json_request = request.json

            new_ip = json_request.get("ip")
            activity = json_request.get("activity")

            allow_ip.add_ip(new_ip, logger, activity)

            return f"IP добавлен с доступом {activity}", 200

    # MAIN FUNCTION ------------------------------------------

    @app.route('/DoGetEmployee', methods=['GET'])
    def get_employee():

        # Запрос в БД
        json_data = {'0001': {"fid": '0001', "flastname": "Last_Name", "ffirstname": "Name", "fmiddlename": "MiddleName"},
                     '0002': {"fid": '0002', "flastname": "Last_Name", "ffirstname": "Name", "fmiddlename": "MiddleName"}}

        return jsonify(json_data)

    @app.route('/DoNewEmployee', methods=['POST'])
    def new_employee():

        res = request.json

        return "hello new_employee"

    @app.route('/DoCreateGuest.txt', methods=['POST'])
    def create_guest():

        user_ip = request.remote_addr

        if not allow_ip.find_ip(user_ip, logger):
            return "ERROR"
        else:
            json_request = request.json
            # Результат из БД
            db_result = CreateGuestDB.add_guest(json_request, logger)

            if json_request.get("FPhone") and db_result["status"]:
                sms = SendSMS(set_ini)
                sms.send_sms(json_request["FPhone"], json_request["FInviteCode"])

            return "SUCCESS"

    @app.route('/DoDeleteEmployee', methods=['POST'])
    def delete_employee():
        res = request.json

        return "hello delete_employee"

    # --------------------------------------------------------

    # ЗАПУСК СЕРВЕРА С ПАРАМЕТРАМИ  <-------------------------
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
