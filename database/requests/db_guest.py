from misc.logger import Logger
from database.db_connection import connect_db

SUCCESS_GUEST_ADDED = 'guest_added'
ERROR_ANY_ERROR = 'any_error'
ACCESS_DENIED_REGISTRATION_DENIAL = 'registration_denial'
IS_BLOCKED_CAR_IS_BLOCKED = 'car_is_blocked'
WARNING_IS_EXIST = 'is_exist'


# Создаем строку для запроса в БД
def do_request_str(last_name, first_name, middle_name, car_number, remote_id, activity,
                   date_from, date_to, account_id, phone_number, invite_code) -> str:

    req_str = f"insert into sac3.tguest(" \
                f"FLastName, FFirstName, FMiddleName, " \
                f"FCarNumber, FRemoteID, FActivity, " \
                f"FDateCreate, FDateFrom, FDateTo, " \
                f"FAccountID, FPhone, FInviteCode) " \
                f"values (" \
                f"'{last_name}', '{first_name}', '{middle_name}', '{car_number}', " \
                f"{remote_id}, '{activity}', now(), " \
                f"'{date_from}', '{date_to}', {account_id}, '{phone_number}', {invite_code})"

    return req_str


class CreateGuestDB:
    # Класс работы с гостем
    @staticmethod
    def add_guest(data_on_pass: dict, logger: Logger) -> dict:
        """ принимает словарь с данными от on_pass и logger """

        account_id = int(data_on_pass["FAccountID"])
        last_name = data_on_pass['FLastName']
        first_name = data_on_pass['FFirstName']

        # middle_name = data_on_pass['FMiddleName']
        middle_name = data_on_pass.get("FMiddleName")

        # car_number = data_on_pass['FCarNumber']
        car_number = data_on_pass.get("FCarNumber")

        date_from = data_on_pass['FDateFrom']
        date_to = data_on_pass['FDateTo']
        invite_code = int(data_on_pass['FInviteCode'])
        remote_id = int(data_on_pass["FRemoteID"])

        # phone_number = data_on_pass["FPhone"]
        phone_number = data_on_pass.get("FPhone")

        if not middle_name:
            middle_name = ''
        if not car_number:
            car_number = ''
        if not phone_number:
            phone_number = ''

        ret_value = {"status": "ERROR", "desc": '', "data": ''}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:

                # Проверяем компанию на доступность
                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                                f"where FCompanyID = tcompany.FID "
                                f"and taccount.FID = {account_id} "
                                f"and tcompany.FActivity = 1 "
                                f"and taccount.FActivity = 1")
                request_activity = cur.fetchall()

                # Если есть номер авто проверяем его в черном списке
                if car_number:
                    cur.execute(f"select FID "
                                f"from sac3.tblacklist "
                                f"where FCarNumber = '{car_number}' "
                                f"and FActivity = 1")
                    is_blocked = cur.fetchall()
                else:
                    is_blocked = list()

                # Проверяем ID на существования заявки
                cur.execute(f"select FID "
                            f"from sac3.tguest "
                            f"where FRemoteID = {remote_id}")
                is_exist = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["status"] = "ACCESS_DENIED"
                    ret_value["desc"] = ACCESS_DENIED_REGISTRATION_DENIAL

                    logger.add_log(f"WARNING\tCreateGuestDB.add_guest - "
                                   f"Регистрация заявки отклонена AccountID: {account_id}. "
                                   f"Компания/Аккаунт не найден(а) или имеет ограничения.")

                elif len(is_exist) != 0:
                    ret_value["status"] = "WARNING"
                    ret_value["desc"] = WARNING_IS_EXIST

                    ret_value["data"] = is_exist[0]
                    logger.add_log(f"WARNING\tCreateGuestDB.add_guest - Ошибка RemoteID: {remote_id} уже занят.")

                elif len(is_blocked) != 0:
                    ret_value["status"] = "IS_BLOCKED"
                    ret_value["desc"] = IS_BLOCKED_CAR_IS_BLOCKED

                    # Загружаем данные в базу
                    sql_request = do_request_str(last_name, first_name, middle_name, car_number, remote_id, 0,
                                                    date_from, date_to, account_id, phone_number, invite_code)
                    cur.execute(sql_request)

                    connection.commit()
                    logger.add_log(f"WARNING\tCreateGuestDB.add_guest - Номер {car_number} в черном списке.")
                else:
                    # Загружаем данные в базу
                    sql_request = do_request_str(last_name, first_name, middle_name, car_number, remote_id, 1,
                                                    date_from, date_to, account_id, phone_number, invite_code)
                    cur.execute(sql_request)

                    connection.commit()

                    # Получаем FID для ответа
                    cur.execute(f"select FID "
                                f"from sac3.tguest "
                                f"where FRemoteID = {remote_id}")
                    is_exist = cur.fetchall()

                    ret_value["data"] = is_exist[0]

                    logger.add_log(f"EVENT\tCreateGuestDB.add_guest - "
                                   f"Успешно добавлен GUEST в базу данных Account_ID: {account_id}")
                    ret_value["status"] = "SUCCESS"
                    ret_value["desc"] = SUCCESS_GUEST_ADDED

            connection.close()

        except Exception as ex:
            logger.add_log(f"ERROR\tCreateGuestDB.add_guest - Ошибка работы с базой данных: {ex}")
            ret_value["desc"] = ERROR_ANY_ERROR

        return ret_value

    @staticmethod
    def get_photo(invite_code: str, logger: Logger) -> dict:

        ret_value = {"RESULT": False, "DESC": '', 'DATA': dict()}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:

                cur.execute(f"select * from sac3.tguest where FInviteCode = '{invite_code}'")
                result = cur.fetchone()

                if not result:
                    ret_value["DESC"] = f"Не удалось найти InviteCode = {invite_code}"
                else:

                    cur.execute(f"select * from vig_face.tperson where "
                                f"FRemoteID = {result.get('FID')} "
                                f"and ftag = 'Guest'")

                    result = cur.fetchone()

                    if result:
                        ret_value["RESULT"] = True
                        ret_value['DATA'] = result
                    else:
                        ret_value["DESC"] = f"Не удалось найти в tperson.FRemoteID = {result.get('FID')}"

            connection.close()

        except Exception as ex:
            ret_value["DESC"] = "Ошибка работы с базой данных CreateGuestDB.get_photo"
            logger.add_log(f"ERROR\tCreateGuestDB.get_photo\tОшибка работы с базой данных: {ex}")

        return ret_value

    @staticmethod
    def block_guest(account_id: int, remote_id: int, logger: Logger) -> dict:
        """ Заблокировать заявку на посетителя. /n
        Так же имеется флаг в ответе для запроса на удаление персоны из терминалов распознания лица.
        RESULT: STR / DESC: STR / DATA: DISC / FACE_DRIVER: BOOL """

        ret_value = {'RESULT': "ERROR", 'DESC': '', 'DATA': dict(), 'FACE_DRIVER': False}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:
                # Проверяем компанию на доступность
                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                            f"where FCompanyID = tcompany.FID "
                            f"and taccount.FID = {account_id} "
                            f"and tcompany.FActivity = 1 "
                            f"and taccount.FActivity = 1")
                request_activity = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["status"] = "ACCESS_DENIED"
                    ret_value["DESC"] = "Компания/Аккаунт не найден(а) или имеет ограничения."
                    logger.add_log(f"WARNING\tCreateGuestDB.del_guest\tРегистрация заявки отклонена "
                                   f"AccountID: {account_id}. Компания/Аккаунт не найден(а) или имеет ограничения.")
                else:
                    # Получаем данные активной заявки на гостя
                    cur.execute(f"select * from sac3.tguest "
                                f"where FRemoteID = {remote_id} "
                                f"and FAccountID = {account_id} "
                                f"and FActivity = 1")

                    guest_res = cur.fetchall()

                    if len(guest_res) > 0:
                        # Блокируем заявку
                        cur.execute(f"update sac3.tguest "
                                    f"set FActivity = 0 "
                                    f"where FRemoteID = {remote_id} "
                                    f"and FAccountID = {account_id}")

                    connection.commit()

                    if len(guest_res) > 1:
                        ret_value['DESC'] = f"По какой то причине в БД было больше одной заявки с id = {remote_id}"
                        logger.add_log(f"WARNING\tCreateGuestDB.del_guest\tПо какой то причине в БД было больше одной "
                                       f"заявки с id = {remote_id}")

                    if len(guest_res) > 0:
                        print(guest_res[0])
                        guest_fid = guest_res[0].get('FID')

                        # Получаем данные персоны\карты которую выдали
                        cur.execute(f"select * from vig_face.tperson where FRemoteID = {guest_fid} "
                                    f"and FActivity = 1 and FTag = 'Guest'")

                        res_person = cur.fetchall()

                        if cur.rowcount == 0:
                            ret_value['RESULT'] = "SUCCESS"
                        else:
                            connection.commit()
                            print(res_person[0])
                            person_fid = res_person[0].get('FID')
                            ret_value['DATA'] = {'id': person_fid}

                            # Получаем данные прохода и определяем был ли ВХОД\ВЫХОД
                            cur.execute(f"select * from vig_face.tpasses, vig_face.tfacestation "
                                        f"where FPersonID = {person_fid} "
                                        f"and tfacestation.FID = FFaceStationID "
                                        f"order by FDateTimePass desc "
                                        f"limit 1")

                            res_tpasses = cur.fetchall()

                            if cur.rowcount == 0:
                                ret_value['RESULT'] = "SUCCESS"
                                ret_value['FACE_DRIVER'] = True
                            else:
                                print(res_tpasses[0])

                                if res_tpasses[0].get('FWayType') == 'Input':
                                    # Если последняя запись в БД является ВХОД, ставим метку заблокировать после выхода
                                    cur.execute(f"update vig_face.tperson "
                                                f"set FBlockByOutput = 1 "
                                                f"where FID = {person_fid}")

                                else:
                                    # Блокируем персону\карту и
                                    # устанавливаем в ответе флаг на удаления лица из терминала
                                    cur.execute(f"update vig_face.tperson "
                                                f"set FActivity = 1 "
                                                f"where FID = {person_fid}")
                                    ret_value['FACE_DRIVER'] = True

                                connection.commit()

                    else:
                        ret_value['DESC'] = f"Не удалось найти Заявку"

        except Exception as ex:
            ret_value['DESC'] = "Ошибка работы с базой данных"
            logger.exception(f"Ошибка работы с базой данных: {ex}")

        return ret_value

    @staticmethod  # Тестовая функция для проверки блокировки гостя
    def unblock_guest(account_id: int, remote_id: int, logger: Logger) -> dict:
        """ Разблокировать заявку на посетителя. """

        ret_value = {'RESULT': "ERROR", 'DESC': '', 'DATA': dict(), 'FACE_DRIVER': False}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:
                # Проверяем компанию на доступность
                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                            f"where FCompanyID = tcompany.FID "
                            f"and taccount.FID = {account_id} "
                            f"and tcompany.FActivity = 1 "
                            f"and taccount.FActivity = 1")
                request_activity = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["DESC"] = "Компания/Аккаунт не найден(а) или имеет ограничения."
                    logger.add_log(f"WARNING\tCreateGuestDB.unblock_guest\tРегистрация заявки отклонена "
                                   f"AccountID: {account_id}. Компания/Аккаунт не найден(а) или имеет ограничения.")
                else:
                    cur.execute(f"update sac3.tguest set FActivity = 1 "
                                f"where FRemoteID = {remote_id} "
                                f"and FAccountID = {account_id}")

                    connection.commit()

                    if cur.rowcount == 1:
                        ret_value['RESULT'] = "SUCCESS"
                    else:
                        ret_value['DESC'] = f"Не удалось найти Заявку."

        except Exception as ex:
            ret_value['DESC'] = "Ошибка работы с базой данных"
            logger.exception(f"Ошибка работы с базой данных: {ex}")

        return ret_value

    @staticmethod  # Тестовая функция для проверки блокировки гостя
    def delete_guest(account_id: int, remote_id: int, logger: Logger) -> dict:
        """ Удалить заявку на посетителя. """

        ret_value = {'RESULT': "ERROR", 'DESC': '', 'DATA': dict()}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:
                # Проверяем компанию на доступность
                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                            f"where FCompanyID = tcompany.FID "
                            f"and taccount.FID = {account_id} "
                            f"and tcompany.FActivity = 1 "
                            f"and taccount.FActivity = 1")
                request_activity = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["DESC"] = "Компания/Аккаунт не найден(а) или имеет ограничения."
                    logger.add_log(f"WARNING\tCreateGuestDB.unblock_guest\tРегистрация заявки отклонена "
                                   f"AccountID: {account_id}. Компания/Аккаунт не найден(а) или имеет ограничения.")
                else:

                    cur.execute(f"select * from sac3.tguest "
                                f"where FRemoteID = {remote_id} and FAccountID = {account_id};")

                    if cur.rowcount == 1:

                        cur.execute(f"delete from sac3.tguest where FRemoteID = {remote_id} "
                                    f"and FAccountID = {account_id};")

                        connection.commit()
                        ret_value['RESULT'] = "SUCCESS"

                        if cur.rowcount == 1:
                            ret_value['DESC'] = f"Успешно удалена заявка на {remote_id}"
                        else:
                            ret_value['DESC'] = f"Не удалось найти Заявку."
                    elif cur.rowcount > 1:
                        msg = f"Требуется ручная проверка БД, " \
                                            f"найдено больше 1 заявки с FRemoteID = {remote_id}"
                        ret_value["DESC"] = msg
                        logger.exception(f"Ошибка работы с базой данных: {msg}")
                    else:
                        ret_value['DESC'] = f"Не удалось найти заявку по FRemoteID = {remote_id}"

        except Exception as ex:
            ret_value['DESC'] = "Ошибка работы с базой данных"
            logger.exception(f"Ошибка работы с базой данных: {ex}")

        return ret_value

    @staticmethod  # Тестовая функция для проверки блокировки гостя
    def add_person_guest(f_name: str, remote_id: int, logger: Logger) -> dict:
        """ Имитация получения пропуска Гостем """

        ret_value = {'RESULT': "ERROR", 'DESC': '', 'DATA': dict()}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:
                # Проверяем компанию на доступность
                cur.execute(f"insert into vig_face.tperson(FName, FRemoteID) values ('{f_name}', {remote_id})")

                connection.commit()

                cur.execute(f"select * from vig_face.tperson where FRemoteID = {remote_id}")

                res_person = cur.fetchall()

                if cur.rowcount == 1:
                    ret_value['DATA'] = {"FID": res_person[0].get("FID")}
                    ret_value['RESULT'] = "SUCCESS"

        except Exception as ex:
            ret_value['DESC'] = "Ошибка работы с базой данных"
            logger.exception(f"Ошибка работы с базой данных: {ex}")

        return ret_value
