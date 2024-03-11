from flask import Blueprint, request, jsonify
from misc.consts import LOGGER, ALLOW_IP

ip_blue = Blueprint('ip_blue', __name__, template_folder='templates', static_folder='static')


@ip_blue.route('/DoAddIp', methods=['POST'])
def add_ip():
    json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\tDoAddIp запрос от ip: {user_ip}", print_it=False)

    if not ALLOW_IP.find(user_ip, LOGGER, 2):  # Устанавливаем activity_lvl=2 для проверки уровня доступа
        json_replay["DESC"] = "Ошибка доступа по IP"
    else:

        if request.is_json:
            json_request = request.json

            new_ip = json_request.get("ip")
            activity = int(json_request.get("activity"))

            ALLOW_IP.add(new_ip, LOGGER, activity)

            json_replay["RESULT"] = "SUCCESS"
            json_replay["DESC"] = f"IP - {new_ip} добавлен с доступом {activity}"
        else:
            LOGGER.add_log(f"ERROR\tDoCreateGuest Не удалось прочитать Json из request")
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = "Ошибка. Не удалось прочитать Json из request."

    return jsonify(json_replay)
