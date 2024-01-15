from database.requests.db_guest import CreateGuestDB
from flask import Blueprint, request, jsonify
from misc.consts import LOGGER, ALLOW_IP, ERROR_ACCESS_IP, ERROR_READ_JSON, ConstControl
from database.driver.rest_driver import FaceDriver
from misc.car_number_test import NormalizeCar
from misc.invite_code import gen_invite_code

from database.requests.db_company import CompanyDB


guests_blue = Blueprint('guests_blue', __name__, template_folder='templates', static_folder='static')


@guests_blue.route('/DoCreateGuest', methods=['POST'])
def do_create_guest():
    """ Добавляет посетителя в БД
    (и отправляет смс если номер указан) - смс отключены и решена проблема ожидания 20 секунд """

    json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.event(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["RESULT"] = "ERROR"
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:

        # Проверяем наличие Json
        if request.is_json:

            json_request = request.json

            LOGGER.info(f"Получены данные: ({json_request})", print_it=False)

            # Проверяем номер авто
            car_number = json_request.get("FCarNumber")

            if car_number:
                norm_num = NormalizeCar()
                car_number = norm_num.do_normal(car_number)

                json_request['FCarNumber'] = car_number

            if not json_request.get('FInviteCode'):
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
            LOGGER.error(f"Ошибка чтения Json: В запросе нет Json")
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = ERROR_READ_JSON

    return jsonify(json_replay)


@guests_blue.route('/DoBlockGuest', methods=['POST'])
def do_block_guest():
    """ Блокирует заявку на посетителя """

    json_replay = {'RESULT': 'ERROR', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.event(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        if request.is_json:
            json_request = request.json

            LOGGER.info(f"Получены данные: ({json_request})", print_it=False)

            json_replay = CreateGuestDB.block_guest(json_request.get('FAccountID'), json_request.get('FID'), LOGGER)

            if json_replay['FACE_DRIVER']:
                connect_driver = FaceDriver(ConstControl.get_set_ini())
                res_driver = connect_driver.delete_person(json_replay['DATA'], LOGGER)

                if res_driver['RESULT'] != "SUCCESS":
                    json_replay['DESC'] += res_driver['DESC']
                    json_replay['RESULT'] = 'WARNING'

        else:
            LOGGER.error(f"Ошибка чтения Json: В запросе нет данных")
            json_replay['DESC'] = ERROR_READ_JSON

    return json_replay


@guests_blue.route('/DoChangeTimeAccess', methods=['POST'])
def change_access_time():
    json_replay = {'RESULT': 'ERROR', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.event(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        if request.is_json:
            json_request = request.json

            LOGGER.info(f"Получены данные: ({json_request})", print_it=False)

            # Создаем запрос к БД с просьбой изменить дату доступа гостя
            json_replay = CreateGuestDB.change_time_access(json_request.get('FAccountID'), json_request.get('FID'),
                                                           LOGGER, json_request.get('DateTimeFrom'),
                                                           json_request.get('DateTimeTo'))
        else:
            LOGGER.error(f"Ошибка чтения Json: В запросе нет данных")
            json_replay['DESC'] = ERROR_READ_JSON

    return json_replay


@guests_blue.route('/DoTestGetInviteCode', methods=['POST'])
def guest_take_invite_code():
    json_replay = {'RESULT': 'SUCCESS', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.event(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        json_replay['DATA'] = gen_invite_code()
        print(CompanyDB.get_account_id_by_inn('7719187199'))

    return json_replay