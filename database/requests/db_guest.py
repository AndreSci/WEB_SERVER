from misc.logger import Logger
from database.db_connection import connect_db
from misc.car_number_fix import NormalizeCar
from misc.fio_fix import FioFix

SUCCESS_GUEST_ADDED = 'guest_added'
ERROR_ANY_ERROR = 'any_error'
ACCESS_DENIED_REGISTRATION_DENIAL = 'registration_denial'
IS_BLOCKED_CAR_IS_BLOCKED = 'car_is_blocked'
WARNING_IS_EXIST = 'is_exist'

EXCEPTION_DB_TXT = "Ошибка работы с базой данных"


# Создаем строку для запроса в БД
def do_request_str(last_name, first_name, middle_name, car_number, remote_id, activity,
                   date_from, date_to, account_id, phone_number, invite_code, block_by_out=0) -> str:

    if not block_by_out:  # Заглушка
        block_by_out = 0

    try:
        if str(date_to) == str(date_from) and len(str(date_to)) == 10:
            date_to = date_to + " 23:59:59"
    except Exception as ex:
        print(f"Исключение в функции подготовки SQL запроса {ex}")

    req_str = f"insert into sac3.tguest(" \
                f"FLastName, FFirstName, FMiddleName, " \
                f"FCarNumber, FRemoteID, FActivity, " \
                f"FDateCreate, FDateFrom, FDateTo, " \
                f"FAccountID, FPhone, FInviteCode, FBlockByOutput) " \
                f"values (" \
                f"'{last_name}', '{first_name}', '{middle_name}', '{car_number}', " \
                f"{remote_id}, '{activity}', now(), " \
                f"'{date_from}', '{date_to}', {account_id}, '{phone_number}', {invite_code}, {block_by_out})"

    return req_str


class CreateGuestDB:
    """ Класс работы с гостем """
    @staticmethod
    def add_guest(data_on_pass: dict, logger: Logger) -> dict:
        """ принимает словарь с данными от on_pass и logger """

        ret_value = {"status": "ERROR", "desc": '', "data": ''}

        try:
            if data_on_pass.get('FAccountID'):
                account_id = int(data_on_pass["FAccountID"])
            else:
                account_id = None

            last_name = data_on_pass['FLastName']
            first_name = data_on_pass['FFirstName']

            # middle_name = data_on_pass['FMiddleName']
            middle_name = data_on_pass.get("FMiddleName")

            try:
                last_name, first_name, middle_name = FioFix().do_normal(last_name, first_name, middle_name)
            except Exception as ex:
                logger.exception(f"Исключение в попытке поправить Ф.И.О.: {ex}")

            # car_number = data_on_pass['FCarNumber']
            car_number = data_on_pass.get("FCarNumber")

            date_from = data_on_pass['FDateFrom']
            date_to = data_on_pass['FDateTo']
            invite_code = int(data_on_pass['FInviteCode'])
            remote_id = int(data_on_pass["FRemoteID"])

            # phone_number = data_on_pass["FPhone"]
            phone_number = data_on_pass.get("FPhone")

            # Block by output (метод разового прохода)
            block_by_out = data_on_pass.get("FBlockByOutput")

            # logger.event(f"date_from: {date_from} and date_to: {date_to}")

            if not middle_name:
                middle_name = ''
            if not car_number:
                car_number = ''
            else:
                car_number = NormalizeCar().do_normal(str(car_number))
            if not phone_number:
                phone_number = ''

        except Exception as ex:
            logger.exception(f"Ошибка обработки данных для SQL: {ex}")
            ret_value['desc'] = "Ошибка обработки данных для SQL"
            return ret_value

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:

                # Если FAccountID пуст но есть inn
                if account_id is None:
                    inn = data_on_pass.get('inn')

                    cur.execute(f"select taccount.FID as FAccountID "
                                f"from sac3.tcompany, sac3.taccount "
                                f"where FINN = %s and tcompany.FID = taccount.FCompanyID", (inn,))
                    request_account_id = cur.fetchone()

                    account_id = request_account_id.get('FAccountID')

                # Проверяем компанию на доступность
                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                                f"where FCompanyID = tcompany.FID "
                                f"and taccount.FID = %s "
                                f"and tcompany.FActivity = 1 "
                                f"and taccount.FActivity = 1", (account_id, ))
                request_activity = cur.fetchall()

                # Если есть номер авто проверяем его в черном списке
                if car_number:
                    cur.execute(f"select FID "
                                f"from sac3.tblacklist "
                                f"where FCarNumber = %s "
                                f"and FActivity = 1", (car_number, ))
                    is_blocked = cur.fetchall()
                else:
                    is_blocked = list()

                # Проверяем ID на существования заявки
                cur.execute(f"select FID "
                            f"from sac3.tguest "
                            f"where FRemoteID = %s", (remote_id, ))
                is_exist = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["status"] = "ACCESS_DENIED"
                    ret_value["desc"] = ACCESS_DENIED_REGISTRATION_DENIAL

                    logger.add_log(f"WARNING\tCreateGuestDB.add_guest - "
                                   f"Регистрация заявки отклонена AccountID: {account_id}. "
                                   f"Компания/Аккаунт не найден(а) или имеет ограничения.")

                # Пропускать remote_id если он == 0 (сделано для регистрации Сотрудников без фото)
                elif len(is_exist) != 0 and remote_id != 0:
                    ret_value["status"] = "WARNING"
                    ret_value["desc"] = WARNING_IS_EXIST

                    ret_value["data"] = is_exist[0]
                    logger.add_log(f"WARNING\tCreateGuestDB.add_guest - Ошибка RemoteID: {remote_id} уже занят.")

                elif len(is_blocked) != 0:
                    ret_value["status"] = "IS_BLOCKED"
                    ret_value["desc"] = IS_BLOCKED_CAR_IS_BLOCKED

                    # Формируем запрос
                    sql_request = do_request_str(last_name, first_name, middle_name, car_number, remote_id, 0,
                                                    date_from, date_to, account_id, phone_number, invite_code,
                                                 block_by_out)
                    logger.info(sql_request, print_it=False)

                    # Загружаем данные в базу
                    cur.execute(sql_request)

                    connection.commit()
                    logger.add_log(f"WARNING\tCreateGuestDB.add_guest - Номер {car_number} в черном списке.")
                else:
                    # Формируем запрос
                    sql_request = do_request_str(last_name, first_name, middle_name, car_number, remote_id, 1,
                                                    date_from, date_to, account_id, phone_number, invite_code,
                                                 block_by_out)
                    logger.info(sql_request, print_it=False)
                    # Загружаем данные в базу
                    cur.execute(sql_request)

                    connection.commit()

                    # Получаем FID для ответа
                    cur.execute(f"select FID "
                                f"from sac3.tguest "
                                f"where FRemoteID = %s", (remote_id, ))
                    is_exist = cur.fetchall()

                    ret_value["data"] = is_exist[0]

                    logger.add_log(f"EVENT\tCreateGuestDB.add_guest - "
                                   f"Успешно добавлен GUEST в базу данных Account_ID: {account_id}")
                    ret_value["status"] = "SUCCESS"
                    ret_value["desc"] = SUCCESS_GUEST_ADDED

            connection.close()

        except Exception as ex:
            logger.exception(f"{EXCEPTION_DB_TXT}: {ex}")
            ret_value["desc"] = EXCEPTION_DB_TXT

        return ret_value

    @staticmethod
    def get_photo(invite_code: str, logger: Logger) -> dict:

        ret_value = {"RESULT": False, "DESC": '', 'DATA': dict()}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:

                cur.execute(f"select * from sac3.tguest where FInviteCode = %s", (invite_code, ))
                result = cur.fetchone()

                if not result:
                    ret_value["DESC"] = f"Не удалось найти InviteCode = {invite_code}"
                else:

                    cur.execute(f"select * from vig_face.tperson where "
                                f"FRemoteID = %s "
                                f"and ftag = 'Guest'", (result.get('FID'), ))

                    result = cur.fetchone()

                    if result:
                        ret_value["RESULT"] = True
                        ret_value['DATA'] = result
                    else:
                        ret_value["DESC"] = f"Не удалось найти в tperson.FRemoteID = {result.get('FID')}"

            connection.close()

        except Exception as ex:
            ret_value["DESC"] = EXCEPTION_DB_TXT
            logger.exception(f"{EXCEPTION_DB_TXT}: {ex}")

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
                            f"and taccount.FID = %s "
                            f"and tcompany.FActivity = 1 "
                            f"and taccount.FActivity = 1", (account_id, ))
                request_activity = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["DESC"] = "Компания/Аккаунт не найден(а) или имеет ограничения."
                    logger.add_log(f"WARNING\tCreateGuestDB.del_guest\tРегистрация заявки отклонена "
                                   f"AccountID: {account_id}. Компания/Аккаунт не найден(а) или имеет ограничения.")
                else:
                    # Получаем данные активной заявки на гостя
                    cur.execute(f"select * from sac3.tguest "
                                f"where FRemoteID = %s "
                                f"and FAccountID = %s "
                                f"and FActivity = 1", (remote_id, account_id))

                    guest_res = cur.fetchall()

                    if len(guest_res) > 0:
                        # Блокируем заявку
                        cur.execute(f"update sac3.tguest "
                                    f"set FActivity = 0 "
                                    f"where FRemoteID = %s "
                                    f"and FAccountID = %s", (remote_id, account_id))

                    connection.commit()

                    if len(guest_res) > 1:
                        ret_value['DESC'] = f"По какой то причине в БД было больше одной заявки с id = {remote_id}"
                        logger.add_log(f"WARNING\tCreateGuestDB.del_guest\tПо какой то причине в БД было больше одной "
                                       f"заявки с id = {remote_id}")

                    if len(guest_res) > 0:
                        guest_fid = guest_res[0].get('FID')

                        # Получаем данные персоны\карты которую выдали
                        cur.execute(f"select * from vig_face.tperson where FRemoteID = %s "
                                    f"and FActivity = 1 and FTag = 'Guest'", (guest_fid, ))

                        res_person = cur.fetchall()

                        if cur.rowcount == 0:
                            ret_value['RESULT'] = "SUCCESS"
                        else:
                            connection.commit()

                            person_fid = res_person[0].get('FID')
                            ret_value['DATA'] = {'id': person_fid}

                            # Получаем данные прохода и определяем был ли ВХОД\ВЫХОД
                            cur.execute(f"select * from vig_face.tpasses, vig_face.tfacestation "
                                        f"where FPersonID = %s "
                                        f"and tfacestation.FID = FFaceStationID "
                                        f"order by FDateTimePass desc "
                                        f"limit 1", (person_fid, ))

                            res_tpasses = cur.fetchall()

                            if cur.rowcount == 0:
                                ret_value['FACE_DRIVER'] = True
                            else:
                                if res_tpasses[0].get('FWayType') == 'Input':
                                    # Если последняя запись в БД является ВХОД, ставим метку заблокировать после выхода
                                    cur.execute(f"update vig_face.tperson "
                                                f"set FBlockByOutput = 1 "
                                                f"where FID = %s", (person_fid, ))

                                else:
                                    # Блокируем персону\карту и
                                    # устанавливаем в ответе флаг на удаления лица из терминала
                                    cur.execute(f"update vig_face.tperson "
                                                f"set FActivity = 0 "
                                                f"where FID = %s", (person_fid, ))
                                    ret_value['FACE_DRIVER'] = True

                                connection.commit()

                            ret_value['RESULT'] = "SUCCESS"
                    else:
                        ret_value['DESC'] = f"Не удалось найти Заявку"

        except Exception as ex:
            ret_value['DESC'] = EXCEPTION_DB_TXT
            logger.exception(f"{EXCEPTION_DB_TXT}: {ex}")

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
                            f"and taccount.FID = %s "
                            f"and tcompany.FActivity = 1 "
                            f"and taccount.FActivity = 1", (account_id, ))
                request_activity = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["DESC"] = "Компания/Аккаунт не найден(а) или имеет ограничения."
                    logger.add_log(f"WARNING\tCreateGuestDB.unblock_guest\tРегистрация заявки отклонена "
                                   f"AccountID: {account_id}. Компания/Аккаунт не найден(а) или имеет ограничения.")
                else:
                    cur.execute(f"update sac3.tguest set FActivity = 1 "
                                f"where FRemoteID = %s "
                                f"and FAccountID = %s", (remote_id, account_id))

                    connection.commit()

                    if cur.rowcount == 1:
                        ret_value['RESULT'] = "SUCCESS"
                    else:
                        ret_value['DESC'] = f"Не удалось найти Заявку."

        except Exception as ex:
            ret_value['DESC'] = EXCEPTION_DB_TXT
            logger.exception(f"{EXCEPTION_DB_TXT}: {ex}")

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
                            f"and taccount.FID = %s "
                            f"and tcompany.FActivity = 1 "
                            f"and taccount.FActivity = 1", (account_id, ))
                request_activity = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["DESC"] = "Компания/Аккаунт не найден(а) или имеет ограничения."
                    logger.add_log(f"WARNING\tCreateGuestDB.unblock_guest\tРегистрация заявки отклонена "
                                   f"AccountID: {account_id}. Компания/Аккаунт не найден(а) или имеет ограничения.")
                else:

                    cur.execute(f"select * from sac3.tguest "
                                f"where FRemoteID = %s and FAccountID = %s;", (remote_id, account_id))

                    if cur.rowcount == 1:

                        cur.execute(f"delete from sac3.tguest where FRemoteID = %s "
                                    f"and FAccountID = %s;", (remote_id, account_id))

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
            ret_value['DESC'] = EXCEPTION_DB_TXT
            logger.exception(f"{EXCEPTION_DB_TXT}: {ex}")

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
                cur.execute(f"insert into vig_face.tperson(FName, FRemoteID, FDateCreate) "
                            f"values (%s, %s, now())", (f_name, remote_id))

                connection.commit()

                cur.execute(f"select * from vig_face.tperson where FRemoteID = {remote_id}")

                res_person = cur.fetchall()

                if cur.rowcount == 1:
                    ret_value['DATA'] = {"FID": res_person[0].get("FID")}
                    ret_value['RESULT'] = "SUCCESS"
                else:
                    ret_value['DESC'] = "Не удалось найти созданный пропуск."

        except Exception as ex:
            ret_value['DESC'] = EXCEPTION_DB_TXT

            logger.exception(f"{EXCEPTION_DB_TXT}: {ex}")

        return ret_value

    @staticmethod  # Тестовая функция для проверки блокировки гостя
    def add_pass_guest(station_id: int, person_id: int, logger: Logger) -> dict:
        """ Имитация проход Гостя """

        ret_value = {'RESULT': "ERROR", 'DESC': '', 'DATA': dict()}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:
                # Проверяем компанию на доступность
                sql_str = f"insert into vig_face.tpasses(FDateTimePass, FPersonID, FFaceStationID) " \
                          f"values (now(), %s, %s)"

                cur.execute(sql_str, (person_id, station_id))

                connection.commit()

                ret_value['RESULT'] = "SUCCESS"

        except Exception as ex:
            ret_value['DESC'] = EXCEPTION_DB_TXT
            logger.exception(f"{EXCEPTION_DB_TXT}: {ex}")

        return ret_value

    @staticmethod
    def change_time_access(account_id: int, remote_id: int, logger: Logger,
                           time_from: str = None, time_to: str = None) -> dict:
        """ Изменить время действие временного пропуска """

        ret_value = {'RESULT': "ERROR", 'DESC': '', 'DATA': dict(), 'FACE_DRIVER': False}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:
                # Проверяем компанию на доступность
                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                            f"where FCompanyID = tcompany.FID "
                            f"and taccount.FID = %s "
                            f"and tcompany.FActivity = 1 "
                            f"and taccount.FActivity = 1", (account_id, ))
                request_activity = cur.fetchall()

            if len(request_activity) == 0:
                ret_value["DESC"] = "Компания/Аккаунт не найден(а) или имеет ограничения."
                logger.add_log(f"WARNING\tCreateGuestDB.change_time_access\tРегистрация заявки отклонена "
                               f"AccountID: {account_id}. Компания/Аккаунт не найден(а) или имеет ограничения.")
            else:
                # Получаем данные активной заявки на гостя
                cur.execute(f"select * from sac3.tguest "
                            f"where FRemoteID = %s "
                            f"and FAccountID = %s "
                            f"and FActivity = 1", (remote_id, account_id))

                guest_res = cur.fetchall()

                if len(guest_res) > 0:
                    # Меняем дату
                    # '2023-12-12 12:00:01' стиль времени
                    if not time_from:
                        time_from = guest_res[0].get('FDateFrom')
                    if not time_to:
                        time_to = guest_res[0].get('FDateTo')

                    cur.execute(f"update sac3.tguest "
                                f"set FDateFrom = %s, FDateTo= %s "
                                f"where FRemoteID = %s "
                                f"and FAccountID = %s "
                                f"and FActivity = 1", (time_from, time_to, remote_id, account_id))
                    connection.commit()

                    if cur.rowcount == 1:
                        ret_value['RESULT'] = "SUCCESS"
                    else:
                        ret_value["RESULT"] = "WARNING"
                        ret_value['DESC'] = f"Внесено изменений: {cur.rowcount} (должно быть 1)"
                        logger.event(f"В БД было внесено: {cur.rowcount}! Данные: remote_id: {remote_id} "
                                     f"account_id: {account_id} time_from: {time_from} time_to: {time_to}")
                else:
                    ret_value['DESC'] = "Не удалось найти заявку"

        except Exception as ex:
            ret_value['DESC'] = EXCEPTION_DB_TXT
            logger.exception(f"{EXCEPTION_DB_TXT}: {ex}")

        return ret_value

    @staticmethod
    def check_invite_code(invite_code: int, logger: Logger) -> dict:

        ret_value = {"RESULT": False, "DESC": '', 'DATA': list()}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:
                # Запрашиваем у БД запись с таким же invite_code, а так же проверяем срок до которого должен действовать
                cur.execute(f"select * from sac3.tguest where FInviteCode = %s and FDateTo >= now()", (invite_code, ))
                result = cur.fetchone()

                # Если результат пуст считаем что invite_code доступен для использования для нового гостя
                if not result:
                    ret_value["DESC"] = f"InviteCode свободен"
                    ret_value['RESULT'] = True

        except Exception as ex:
            ret_value["DESC"] = EXCEPTION_DB_TXT
            logger.exception(f"{EXCEPTION_DB_TXT}: {ex}")

        return ret_value