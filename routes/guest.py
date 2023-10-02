from database.requests.db_guest import CreateGuestDB
from flask import Blueprint, request, jsonify
from misc.consts import LOGGER, ALLOW_IP, ERROR_ACCESS_IP, ERROR_READ_JSON, SET_INI
from misc.send_sms import SendSMS
from misc.car_number_test import NormalizeCar


guests_blue = Blueprint('guests_blue', __name__, template_folder='templates', static_folder='static')


@guests_blue.route('/DoCreateGuest', methods=['POST'])
def create_guest():
    """ Добавляет посетителя в БД
    (и отправляет смс если номер указан) - смс отключены и решена проблема ожидания 20 секунд """

    json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\troute/guest.DoCreateGuest\tзапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["RESULT"] = "ERROR"
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:

        # Проверяем наличие Json
        if request.is_json:

            json_request = request.json

            LOGGER.add_log(f"EVENT\troute/guest.DoCreateGuest\tПолучены данные: ({json_request})", print_it=False)

            # Проверяем номер авто
            car_number = json_request.get("FCarNumber")

            if car_number:
                norm_num = NormalizeCar()
                car_number = norm_num.do_normal(car_number)

                json_request['FCarNumber'] = car_number

            # Результат из БД
            db_result = CreateGuestDB.add_guest(json_request, LOGGER)

            # отправляем СМС если есть номер телефона в заявке
            # if json_request.get("FPhone") and db_result["status"] == 'SUCCESS':
            #
            #     sms = SendSMS(SET_INI)
            #     try:
            #         sms.send_sms(json_request["FPhone"], json_request["FInviteCode"])
            #         LOGGER.add_log(f"EVENT\tОтправлен запрос на отправку СМС: {json_request['FPhone']}")
            #     except Exception as ex:
            #         LOGGER.add_log(f"ERROR\tDoCreateGuest ошибка отправки СМС: {ex}")

            json_replay["RESULT"] = db_result["status"]
            json_replay["DESC"] = db_result["desc"]
            json_replay["DATA"] = db_result["data"]

        else:
            # Если в запросе нет Json данных
            LOGGER.add_log(f"ERROR\troute/guest.DoCreateGuest\tошибка чтения Json: В запросе нет Json")
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = ERROR_READ_JSON

    return jsonify(json_replay)


@guests_blue.route('/DoDeleteGuest', methods=['POST'])
def delete_guest():
    """ Блокирует заявку на посетителя """

    json_replay = {'RESULT': 'ERROR', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\troute/guest.DoDeleteGuest\tзапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        if request.is_json:
            json_request = request.json

            LOGGER.add_log(f"EVENT\troute/guest.DoDeleteGuest\tПолучены данные: ({json_request})", print_it=False)

            json_replay = CreateGuestDB.del_guest(json_request.get('FAccountID'), json_request.get('FID'), LOGGER)

        else:
            LOGGER.add_log(f"ERROR\troute/guest.DoDeleteGuest\tОшибка чтения Json: В запросе нет данных")
            json_replay['DESC'] = ERROR_READ_JSON

    return json_replay
