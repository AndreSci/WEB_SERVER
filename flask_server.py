from flask import Flask, render_template, request, make_response
from misc.util import SettingsIni
from misc.logger import Logger
from misc.allow_ip import AllowedIP

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

    app = Flask(__name__)   # Обьявления сервера

    print("Hello I'm WEB_Flask")
    logger.add_log(f"SUCCESS\tweb_flask\t Сервер WEB_Flask начал сво работу")  # log

    @app.route('/test_server/', methods=['GET'])
    def test_server():
        """ Просто функция проверки сервера """
        logger.add_log(f"SUCCESS\tweb_flask\t server test is OK!")  # log
        return make_response("hello")

    @app.route('/add_allow_ip/', methods=['GET', 'POST'])
    def add_allow_ip():
        json_replay = {"RESULT": "NOT_ALLOWED", "DESC": "None", "DATA": "None"}
        user_ip = request.remote_addr

        if allow_ip.find_ip(user_ip, logger):
            json_replay["RESULT"] = "ALLOWED"

        # if request.method == "POST":
        #
        #     phone_num = request.form.get('fphone')
        #     text = request.form.get('ftext')
        #
        #     # Если запрос произведен с параметрами в ссылке
        #     if not phone_num:
        #         phone_num = request.args.get('fphone')
        #         text = request.args.get('ftext')

        return json_replay, 200

    # --------------------------------------------------------------------------

    # ЗАПУСК СЕРВЕРА С ПАРАМЕТРАМИ  <---------------------------------------------------------------------------<<<
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
