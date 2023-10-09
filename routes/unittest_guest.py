from database.requests.db_guest import CreateGuestDB
from flask import Blueprint, request, jsonify
from misc.consts import LOGGER, ALLOW_IP, ERROR_ACCESS_IP, ERROR_READ_JSON, ConstControl

unittest_guests_blue = Blueprint('unittest_guests_blue', __name__, template_folder='templates', static_folder='static')


# ТЕСТОВЫЙ ЗАПРОС для Unittest
@unittest_guests_blue.route('/DoUnBlockGuest', methods=['POST'])
def unblock_guest():
    """ Сделан для тестов блокировки заявку на посетителя """

    json_replay = {'RESULT': 'ERROR', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\troute/guest.DoUnBlockGuest\tзапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        if request.is_json:
            json_request = request.json

            LOGGER.add_log(f"EVENT\troute/guest.DoUnBlockGuest\tПолучены данные: ({json_request})", print_it=False)

            json_replay = CreateGuestDB.unblock_guest(json_request.get('FAccountID'), json_request.get('FID'), LOGGER)

        else:
            LOGGER.add_log(f"ERROR\troute/guest.DoUnBlockGuest\tОшибка чтения Json: В запросе нет данных")
            json_replay['DESC'] = ERROR_READ_JSON

    return json_replay


# ТЕСТОВЫЙ ЗАПРОС для Unittest
@unittest_guests_blue.route('/DoDeleteGuest', methods=['POST'])
def delete_guest():
    """ Сделан для тестов блокировки заявку на посетителя """

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

            json_replay = CreateGuestDB.delete_guest(json_request.get('FAccountID'), json_request.get('FID'), LOGGER)

        else:
            LOGGER.add_log(f"ERROR\troute/guest.DoDeleteGuest\tОшибка чтения Json: В запросе нет данных")
            json_replay['DESC'] = ERROR_READ_JSON

    return json_replay


# ТЕСТОВЫЙ ЗАПРОС для Unittest
@unittest_guests_blue.route('/DoAddPersonGuest', methods=['POST'])
def add_person_guest():
    """ Сделан для тестов блокировки заявку на посетителя (Создаем в таблице tperson временные данные) \n
    Принимает FName: str и FID: fid из sac3.tguest """

    json_replay = {'RESULT': 'ERROR', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\troute/guest.DoAddPersonGuest\tзапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        if request.is_json:
            json_request = request.json

            LOGGER.add_log(f"EVENT\troute/guest.DoAddPersonGuest\tПолучены данные: ({json_request})", print_it=False)

            json_replay = CreateGuestDB.add_person_guest(json_request.get('FName'),
                                                         json_request.get('FID'), LOGGER)

        else:
            LOGGER.add_log(f"ERROR\troute/guest.DoAddPersonGuest\tОшибка чтения Json: В запросе нет данных")
            json_replay['DESC'] = ERROR_READ_JSON

    return json_replay


# ТЕСТОВЫЙ ЗАПРОС для Unittest
@unittest_guests_blue.route('/DoAddPassesGuest', methods=['POST'])
def add_pass_guest():
    """ Добавляет в таблицу tpasses персону с флагом Input (принимает json - FPersonID и FStationID)"""

    json_replay = {'RESULT': 'ERROR', 'DESC': '', 'DATA': ''}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\troute/guest.DoAddPassesGuest\tзапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay['DESC'] = ERROR_ACCESS_IP
    else:
        if request.is_json:
            json_request = request.json

            LOGGER.add_log(f"EVENT\troute/guest.DoAddPassesGuest\tПолучены данные: ({json_request})", print_it=False)

            json_replay = CreateGuestDB.add_pass_guest(json_request.get('FStationID'),
                                                       json_request.get('FPersonID'), LOGGER)

        else:
            LOGGER.add_log(f"ERROR\troute/guest.DoAddPassesGuest\tОшибка чтения Json: В запросе нет данных")
            json_replay['DESC'] = ERROR_READ_JSON

    return json_replay
