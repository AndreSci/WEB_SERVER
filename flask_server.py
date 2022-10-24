from flask import Flask, render_template, request, make_response
from misc.util import SettingsIni
from misc.logger import Logger

import os
import requests
import socket


def web_flask(logger: Logger, settings_ini: SettingsIni):
    """ Главная функция создания сервера Фласк.
        По стандарту сервер фласк будет создаваться на local с портом 8055
        """
    set_ini = settings_ini.take_settings()

    app = Flask(__name__)   # Обьявления сервера

    print("Hello I'm WEB_Flask")
    logger.add_log(f"SUCCESS\tweb_flask\t Сервер WEB_Flask начал сво работу")  # log

    @app.route('/test_server/', methods=['GET'])
    def test_server():
        """ Просто функция проверки сервера """
        logger.add_log(f"SUCCESS\tweb_flask\t server test is OK!")  # log
        return make_response("hello")

    # --------------------------------------------------------------------------

    # ЗАПУСК СЕРВЕРА С ПАРАМЕТРАМИ  <---------------------------------------------------------------------------<<<
    app.run(debug=False, host=set_ini["host"], port=int(set_ini["port"]))
