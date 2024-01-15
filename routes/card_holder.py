import requests
import datetime
from flask import Blueprint, request, jsonify
from misc.consts import LOGGER, ALLOW_IP, ERROR_ACCESS_IP, ConstControl
from misc.allowed_words import convert_word
from database.requests.db_company import CompanyDB
from database.requests.db_get_card_holders import CardHoldersDB
from misc.consts import GUEST_DAYS


card_holder_blue = Blueprint('card_holder_blue', __name__, template_folder='templates', static_folder='static')


class JsonGuest:
    def __init__(self):
        self.id = None
        self.img64 = ''
        self.account_id = None
        self.last_name = ''
        self.first_name = ''
        self.middle_name = ''
        self.car_number = ''
        self.date_from = datetime.datetime.now().strftime("%d-%m-%y")
        self.date_to = (datetime.datetime.now() + datetime.timedelta(days=GUEST_DAYS)).strftime("%d-%m-%y")
        self.invite_code = None
        self.remote_id = 0
        self.phone = ''
        self.inn = None

    def take_json_guest(self) -> dict:

        json_guest = {
            "id": self.id,
            "img64": self.img64,
            "FAccountID": self.account_id,
            "FLastName": self.last_name,
            "FFirstName": self.first_name,
            "FMiddleName": self.middle_name,
            "FCarNumber": self.car_number,
            "FDateFrom": self.date_from,
            "FDateTo": self.date_to,
            "FInviteCode": self.invite_code,
            "FRemoteID": self.remote_id,
            "FPhone": self.phone
        }

        return json_guest

@card_holder_blue.route('/DoGetCardHolders', methods=['GET'])
def get_card_holder():
    """ Функция возвращает список сотрудников компании """

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\tDoGetCardHolders запрос от ip: {user_ip}", print_it=False)

    json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:
        json_request = dict()

        # Проверяем запрос на Json
        if request.is_json:
            json_request = request.json
        else:
            json_request['FAccountID'] = request.args.get("FAccountID")
            json_request['FINN'] = request.args.get("FINN")

        if not json_request['FAccountID']:
            LOGGER.add_log(f"ERROR\tDoGetCardHolders - Не удалось прочитать args/data из request")
            json_replay["DESC"] = "Ошибка. Не удалось прочитать args/data из request."
        else:

            account_id = json_request.get("FAccountID")
            finn = json_request.get("FINN")

            LOGGER.add_log(f"EVENT\tDoGetCardHolders\tПолучены данные: ("
                           f"FINN: {finn} "
                           f"FAccountID: {account_id})", print_it=False)

            con_db = CardHoldersDB()

            # Запрос в БД sac3
            db_sac3 = CardHoldersDB.get_sac3(account_id, LOGGER)

            if db_sac3["status"]:

                # Запрос в БД FIREBIRD
                db_fdb = con_db.get_fdb(finn, LOGGER)

                json_replay["DESC"] = db_fdb["desc"]

                if db_fdb["status"]:
                    json_replay["RESULT"] = "SUCCESS"
                    # json_replay["DATA"] = db_fdb["data"]

                    list_id = list()

                    # создаем список fid для получения списка сотрудников из базы лиц
                    for it in db_fdb['data']:
                        list_id.append(it["fid"])

                    face_db = con_db.get_with_face(list_id, LOGGER)

                    ret_list_id = list()

                    # Перезаписываем в новый лист данные пользователей с полем isphoto
                    for it in db_fdb["data"]:
                        if it["fid"] in str(face_db['data']):
                            it['isphoto'] = 1
                        else:
                            it['isphoto'] = 0

                        ret_list_id.append(it)

                    json_replay["DATA"] = ret_list_id

            else:
                json_replay["DESC"] = db_sac3["desc"]

    return jsonify(json_replay)


@card_holder_blue.route('/DoCreateCardHolder', methods=['POST'])
def create_card_holder():
    """ Добавляет сотрудника в БД Apacs3000,\n
    запрашивает добавление пропуска по лицу через requests в DoAddEmployeePhoto"""

    class_guest = JsonGuest()

    json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.info(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["RESULT"] = "ERROR"
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:

        # Проверяем наличие Json
        if request.is_json:

            json_request = request.json

            # исправляем текст
            class_guest.first_name = convert_word(json_request.get("First_Name"))
            class_guest.last_name = convert_word(json_request.get("Last_Name"))
            class_guest.middle_name = convert_word(json_request.get("Middle_Name"))
            class_guest.inn = convert_word(json_request.get("inn"))
            class_guest.car_number = convert_word(json_request.get("Car_Number"))
            class_guest.img64 = json_request.get('img64')
            photo_img64 = 0

            try:
                photo_img64 = len(class_guest.img64)
            except Exception as ex:
                LOGGER.exception(f"Ошибка подсчета размера фотографии img64: {ex}")

            LOGGER.add_log(f"EVENT\tDoCreateCardHolder\tПолучены данные: ("
                           f"First_Name: {class_guest.first_name} "
                           f"Last_Name: {class_guest.last_name} "
                           f"Middle_Name: {class_guest.middle_name} "
                           f"inn: {class_guest.inn} "
                           f"Car_Number: {class_guest.car_number} "
                           f"img64_size: {photo_img64})", print_it=False)

            if not class_guest.middle_name:
                class_guest.middle_name = ''

            if not class_guest.car_number:
                class_guest.car_number = ''
            else:
                class_guest.car_number = str(class_guest.car_number).upper().replace(' ', '')

            try:
                # Создаем сотрудника через APACS3000
                res = requests.get(f'http://{ConstControl.get_set_ini().get("host_apacs_i")}:'
                                   f'{ConstControl.get_set_ini().get("port_apacs_i")}/CreateEmployee'
                                   f'?First_Name={class_guest.first_name}'
                                   f'&Last_Name={class_guest.last_name}'
                                   f'&Middle_Name={class_guest.middle_name}'
                                   f'&INN={class_guest.inn}'
                                   f'&Car_Number={class_guest.car_number}')

                json_create = res.json()

                if json_create["RESULT"] == "SUCCESS":
                    # Получаем id пользователя из системного адреса (HEX) в (DEC)
                    sys_addr_id = json_create['DATA']['sysAddrID']
                    sys_addr_id = sys_addr_id[8:]

                    # Переделано в класс class_guest
                    # json_empl = dict()
                    # json_empl['id'] = int(sys_addr_id, 16)
                    # json_empl['img64'] = json_request.get("img64")
                    # res_add_photo = requests.post(f"http://127.0.0.1:{ConstControl.get_set_ini().get('port')}"
                    #                               f"/DoAddEmployeePhoto",
                    #                               json=json_empl)

                    class_guest.id = int(sys_addr_id, 16)
                    res_add_photo = requests.post(f"http://127.0.0.1:{ConstControl.get_set_ini().get('port')}"
                                                  f"/DoAddEmployeePhoto",
                                                  json=class_guest.take_json_guest())

                    if res_add_photo.status_code == 200:
                        res_add_photo = res_add_photo.json()

                        if res_add_photo['RESULT'] == "SUCCESS":
                            json_replay['DESC'] = "Успешно создан сотрудник"
                            LOGGER.event(f"Успешно создан сотрудник для ИНН{class_guest.inn}")
                        elif res_add_photo['RESULT'] == "WARNING":
                            # TODO тут реализация создания гостя под сотрудника

                            try:
                                res_guest = requests.post(f"http://127.0.0.1:{ConstControl.get_set_ini().get('port')}"
                                                              f"/DoCreateGuest",
                                                              json=class_guest.take_json_guest(), timeout=10)

                                if res_guest.status_code == 200:

                                    json_replay['RESULT'] = "WARNING"
                                    json_replay[
                                        'DESC'] = "Успешно создан сотрудник без фото. Требуется авторизации по коду."
                                    LOGGER.event(f"Успешно создан сотрудник для ИНН{class_guest.inn}")
                                else:
                                    json_replay['RESULT'] = "ERROR"
                                    json_replay['DESC'] = "При попытке создать гостя связанного с сотрудником"
                                    json_replay['DATA'] = res_guest.json()

                            except Exception as ex:
                                json_replay['RESULT'] = 'ERROR'
                                json_replay['DESC'] = f"Исключение на сервере: {ex}"

                        else:
                            json_replay['RESULT'] = "WARNING"
                            json_replay['DESC'] = "Сотрудник создан. " \
                                                  f"Ошибка: {res_add_photo['DESC']}"

                        json_replay['DATA'] = {'id': class_guest.id}
                    else:
                        json_replay["RESULT"] = 'WARNING'
                        json_replay['DESC'] = "Ошибка на сервере, " \
                                              "не удалось отправить запрос на добавление фото и открытие пропуска"

                else:
                    LOGGER.add_log(f"WARNING\tDoCreateCardHolder\t"
                                   f"Интерфейс Apacs ответил отказом на запрос создания сотрудника "
                                   f"JSON: {str(json_create)[:150]}...")

                    json_replay["RESULT"] = 'ERROR'
                    json_replay['DATA'] = json_create["DATA"]
                    json_replay['DESC'] = json_create["DESC"]

            except Exception as ex:
                LOGGER.add_log(f"ERROR\tDoCreateCardHolder\tОшибка обращения к интерфейсу Apacs3000: {ex}")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = "Ошибка в работе системы"

        else:
            # Если в запросе нет Json данных
            LOGGER.add_log(f"ERROR\tDoCreateCardHolder ошибка чтения Json: В запросе нет Json")
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = "Ошибка в работе системы"

    return jsonify(json_replay)


@card_holder_blue.route('/DoDeleteCardHolder', methods=['POST'])
def delete_card_holder():
    """ Удаляет сотрудника из БД Принимает id он же Apacs_id и inn компании"""

    # создаем и подключаемся к драйверу Коли
    # connect_driver = ConDriver(set_ini)
    # res_driver = connect_driver.delete_person({"id": 2450}, logger)

    json_replay = {"RESULT": "SUCCESS", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\tDoDeleteCardHolder\tзапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["RESULT"] = "ERROR"
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:

        # Проверяем наличие Json
        if request.is_json:

            json_request = request.json

            str_inn = json_request.get("inn")
            str_fid = json_request.get("id")    # (он же Apacs_id или RemoteID)

            LOGGER.add_log(f"EVENT\tDoDeleteCardHolder\tПолучены данные: ("
                           f"fid: {str_fid} "
                           f"inn: {str_inn})", print_it=False)

            try:
                # Удаляем сотрудника из APACS3000
                res = requests.delete(f'http://{ConstControl.get_set_ini().get("host_apacs_i")}:'
                                      f'{ConstControl.get_set_ini().get("port_apacs_i")}/DeleteEmployee'
                                      f'?INN={str_inn}'
                                      f'&FID={str_fid}')

                try:
                    json_create = res.json()

                    if json_create['RESULT'] == "ERROR":
                        json_replay["RESULT"] = "ERROR"
                        json_replay["DESC"] = json_create["DESC"]
                        json_replay['DATA'] = json_create["DATA"]

                        LOGGER.add_log(f"ERROR\tDoDeleteCardHolder "
                                       f"Не удалось удалить сотрудника в системе Апакс3000: {json_create['DESC']}")
                    else:
                        # Отправляем запрос на удаление данных сотрудника

                        result = requests.post(f"http://127.0.0.1:{ConstControl.get_set_ini().get('port')}"
                                               f"/DoDeletePhoto",
                                               json=json_request)
                        result = result.json()

                        # con_helper = BSHelper(set_ini)
                        # res_base_helper = con_helper.deactivate_person_apacsid({"id": str_fid}, logger)
                        # result = res_base_helper.get("RESULT")

                        if result['RESULT'] == "ERROR":
                            json_replay["RESULT"] = "WARNING"
                            json_replay["DESC"] = "Сотрудник успешно удалён. " \
                                                  "Не удалось заблокировать пропуск сотрудника"
                            json_replay['DATA'] = result

                except Exception as ex:
                    LOGGER.add_log(f"ERROR\tDoDeleteCardHolder Ошибка обращения к интерфейсу Apacs3000: {ex}")
                    json_replay["RESULT"] = "ERROR"
                    json_replay["DESC"] = "Ошибка в работе системы"

            except Exception as ex:
                LOGGER.add_log(f"ERROR\tDoDeleteCardHolder Ошибка обращения к интерфейсу Apacs3000: {ex}")
                json_replay["RESULT"] = "ERROR"
                json_replay["DESC"] = "Ошибка в работе системы"

        else:
            # Если в запросе нет Json данных
            LOGGER.add_log(f"ERROR\tDoDeleteCardHolder ошибка чтения Json: В запросе нет Json")
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = "Ошибка в работе системы"

    return jsonify(json_replay)


@card_holder_blue.route('/GetBlockCar', methods=['GET'])
def get_block_car():
    """ Получает информацию о возможности открытия пропусков на авто """
    json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\tGetBlockCar\tзапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:

        try:
            json_request = request.json

            com_fid = json_request.get("id")
            # inn = json_request.get("inn") убран из-за лишней нагрузки

            LOGGER.add_log(f"EVENT\tGetBlockCar\tПолучены данные: (id: {com_fid})", print_it=False)

            json_replay = CompanyDB.get_block_car(com_fid, LOGGER)

        except Exception as ex:
            # Если в запросе нет Json данных
            LOGGER.add_log(f"ERROR\tGetBlockCar ошибка чтения Json: В запросе нет {ex}")
            json_replay["DESC"] = "Ошибка в работе системы"

    return jsonify(json_replay)
