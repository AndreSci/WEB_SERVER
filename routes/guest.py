from database.requests.db_guest import CreateGuestDB
from flask import Blueprint, request, jsonify
from misc.consts import LOGGER, ALLOW_IP, ERROR_ACCESS_IP, ERROR_READ_JSON, ConstControl
from database.driver.rest_driver import FaceDriver
from misc.car_number_test import NormalizeCar
import random


guests_blue = Blueprint('guests_blue', __name__, template_folder='templates', static_folder='static')


def gen_invite_code() -> dict:
    """ Генератор случайных чисел для InviteCode(код приглашения гостя) """

    ret_value = {"RESULT": False, "DESC": '', "DATA": list()}
    index = 0

    while True:
        index += 1
        invite_code = random.randint(100000, 999999)
        from_db_res = CreateGuestDB.check_invite_code(invite_code, LOGGER)

        if from_db_res['RESULT']:
            ret_value['RESULT'] = True
            ret_value['DATA'] = {'InviteCode': invite_code}
            break
        elif index >= 500:
            # Защита от завешивания запроса
            break

    return ret_value


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

                res_code_gen = gen_invite_code()

                if res_code_gen.get("RESULT"):
                    json_request['FInviteCode'] = res_code_gen['DATA'].get("InviteCode")

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


@guests_blue.route('/DoBlockGuest', methods=['POST'])
def block_guest():
    """ Блокирует заявку на посетителя """

    json_replay = {'RESULT': 'ERROR', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\troute/guest.DoBlockGuest\tзапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        if request.is_json:
            json_request = request.json

            LOGGER.add_log(f"EVENT\troute/guest.DoBlockGuest\tПолучены данные: ({json_request})", print_it=False)

            json_replay = CreateGuestDB.block_guest(json_request.get('FAccountID'), json_request.get('FID'), LOGGER)

            if json_replay['FACE_DRIVER']:
                connect_driver = FaceDriver(ConstControl.get_set_ini())
                res_driver = connect_driver.delete_person(json_replay['DATA'], LOGGER)

                if res_driver['RESULT'] != "SUCCESS":
                    json_replay['DESC'] += res_driver['DESC']
                    json_replay['RESULT'] = 'WARNING'

        else:
            LOGGER.add_log(f"ERROR\troute/guest.DoBlockGuest\tОшибка чтения Json: В запросе нет данных")
            json_replay['DESC'] = ERROR_READ_JSON

    return json_replay


@guests_blue.route('/DoChangeTimeAccess', methods=['POST'])
def change_access_time():
    json_replay = {'RESULT': 'ERROR', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\troute/guest.DoChangeTimeAccess\tЗапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        if request.is_json:
            json_request = request.json

            LOGGER.add_log(f"EVENT\troute/guest.DoChangeTimeAccess\tПолучены данные: ({json_request})", print_it=False)

            # Создаем запрос к БД с просьбой изменить дату доступа гостя
            json_replay = CreateGuestDB.change_time_access(json_request.get('FAccountID'), json_request.get('FID'),
                                                           LOGGER, json_request.get('DateTimeFrom'),
                                                           json_request.get('DateTimeTo'))
        else:
            LOGGER.add_log(f"ERROR\troute/guest.DoChangeTimeAccess\tОшибка чтения Json: В запросе нет данных")
            json_replay['DESC'] = ERROR_READ_JSON

    return json_replay


@guests_blue.route('/DoTestGetInviteCode', methods=['POST'])
def guest_take_invite_code():
    json_replay = {'RESULT': 'SUCCESS', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.info(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        json_replay['DATA'] = gen_invite_code()

    return json_replay