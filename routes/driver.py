from flask import Blueprint, request, jsonify
from misc.consts import LOGGER, ALLOW_IP, ERROR_ACCESS_IP, ConstControl
from database.driver.rest_driver import FaceDriver


driver_blue = Blueprint('driver_blue', __name__, template_folder='templates', static_folder='static')

# DRIVER FUNCTION ------


@driver_blue.route('/DoAddPerson', methods=['POST'])
def add_person():
    """ Добавляет персону в терминалы без фото """

    json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": None}

    user_ip = request.remote_addr
    LOGGER.event(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:
        try:
            res_json = request.json

            # создаем и подключаемся к драйверу Коли
            connect_driver = FaceDriver(ConstControl.get_set_ini())
            result = connect_driver.add_person(res_json, LOGGER)

            if result == "SUCCESS":
                json_replay["RESULT"] = "SUCCESS"
                json_replay["DESC"] = f"Персона успешно добавлена."
            else:
                json_replay["DESC"] = f"Драйвер ответил ошибкой."

        except Exception as ex:
            json_replay['DESC'] = "Ошибка чтения Json из запроса"
            LOGGER.exception(f"Исключение вызвало чтение Json из запроса {ex}")

    return jsonify(json_replay)


@driver_blue.route('/DoUpdatePerson', methods=['POST'])
def update_guest_driver():
    json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": None}

    user_ip = request.remote_addr
    LOGGER.event(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:
        try:
            res_json = request.json

            # создаем и подключаемся к драйверу Коли
            connect_driver = FaceDriver(ConstControl.get_set_ini())
            result = connect_driver.update_person(res_json, LOGGER)

            if result == "SUCCESS":
                json_replay["RESULT"] = "SUCCESS"
                json_replay["DESC"] = f"Персона успешно обновлена."
            else:
                json_replay["DESC"] = f"Драйвер ответил ошибкой."

        except Exception as ex:
            json_replay['DESC'] = "Ошибка чтения Json из запроса"
            LOGGER.exception(f"Исключение вызвало чтение Json из запроса {ex}")

    return jsonify(json_replay)


@driver_blue.route('/DoAddPhoto', methods=['POST'])
def add_new_photo_driver():
    json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": None}

    user_ip = request.remote_addr
    LOGGER.event(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:
        try:
            res_json = request.json

            # создаем и подключаемся к драйверу Коли
            connect_driver = FaceDriver(ConstControl.get_set_ini())
            result = connect_driver.add_face(res_json, LOGGER)

            if result['RESULT'] == "SUCCESS":
                json_replay["RESULT"] = "SUCCESS"
                json_replay["DESC"] = f"Фотография успешно добавлена."
            else:
                json_replay = result

        except Exception as ex:
            json_replay['DESC'] = "Ошибка чтения Json из запроса"
            LOGGER.exception(f"Исключение вызвало чтение Json из запроса {ex}")

    return jsonify(json_replay)
