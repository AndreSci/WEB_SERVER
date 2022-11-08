from misc.logger import Logger
from database.db_connection import connect_db


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
    # функция отправки данных для таблицы sac3.tguest
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

                # TODO проверять номер машины на правильность написания (исключать пробелы и англ. буквы)

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
                    ret_value["desc"] = "registration_denial"

                    logger.add_log(f"CreateGuestDB.add_guest - \tACCESS_DENIED\t"
                                   f"Регистрация заявки отклонена AccountID: {account_id}.")

                elif len(is_exist) != 0:
                    ret_value["status"] = "WARNING"
                    ret_value["desc"] = "is_exist"

                    ret_value["data"] = is_exist[0]
                    logger.add_log(f"CreateGuestDB.add_guest - \tWARNING\tОшибка RemoteID: {remote_id} уже занят.")

                elif len(is_blocked) != 0:
                    ret_value["status"] = "IS_BLOCKED"
                    ret_value["desc"] = "car_is_blocked"

                    # Загружаем данные в базу
                    sql_request = do_request_str(last_name, first_name, middle_name, car_number, remote_id, 0,
                                                    date_from, date_to, account_id, phone_number, invite_code)
                    cur.execute(sql_request)

                    connection.commit()
                    logger.add_log(f"CreateGuestDB.add_guest - \tIS_BLOCKED\tНомер {car_number} в черном списке.")
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

                    logger.add_log(f"CreateGuestDB.add_guest - "
                                   f"\tSUCCESS\tУспешно добавлен GUEST в базу данных Account_ID: {account_id}")
                    ret_value["status"] = "SUCCESS"
                    ret_value["desc"] = "guest_added"

            connection.close()

        except Exception as ex:
            logger.add_log(f"CreateGuestDB.add_guest - \tERROR\tОшибка работы с базой данных: {ex}")
            ret_value["desc"] = "any_error"

        return ret_value
