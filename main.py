""" Made by Andrew Terleckii (2022\12\19) """

import ctypes
from flask import Flask
from misc.consts import LOGGER, ConstControl

from routes.driver import driver_blue
from routes.ip import ip_blue
from routes.face import face_blue
from routes.card_holder import card_holder_blue
from routes.guest import guests_blue
from routes.employee import employee_blue
from routes.company import company_blue

# unittest routes
from routes.unittest_guest import unittest_guests_blue

# IP_HOST_APACS = '192.168.15.10'

app = Flask(__name__)  # Объявление сервера

# Регистрируем routes в сервисе
# Регистрация без url_prefix=''
app.register_blueprint(driver_blue)
app.register_blueprint(ip_blue)
app.register_blueprint(face_blue)
app.register_blueprint(card_holder_blue)
app.register_blueprint(guests_blue)
app.register_blueprint(employee_blue)
app.register_blueprint(company_blue)

# unittests
app.register_blueprint(unittest_guests_blue)


def web_flask():
    """ Главная функция создания сервера Фласк. """

    app.config['JSON_AS_ASCII'] = False

    # Блокируем сообщения фласк
    # block_flask_logs()

    assert ConstControl.allow_ip_read_file() is True
    assert ConstControl.set_ini() is True

    from misc.consts import SET_INI

    # Меняем имя терминала
    ctypes.windll.kernel32.SetConsoleTitleW(f"REST API interface port: {SET_INI['port']} - (use OpenCV) 11032024")

    LOGGER.add_log(f"SUCCESS\tweb_flask\tСервер WEB_Flask начал свою работу")  # log

    # RUN SERVER FLASK  ------
    app.run(debug=False, host=SET_INI["host"], port=int(SET_INI["port"]))


if __name__ == '__main__':
    web_flask()

    input()
