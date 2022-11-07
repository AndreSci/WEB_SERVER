from misc.logger import Logger
from database.db_connection import connect_db


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

                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                                f"where FCompanyID = tcompany.FID "
                                f"and taccount.FID = {account_id} "
                                f"and tcompany.FActivity = 1 "
                                f"and taccount.FActivity = 1")
                request_activity = cur.fetchall()

                # TODO проверять номер машины на правильность написания (исключать пробелы и англ. буквы)

                cur.execute(f"select FID "
                            f"from sac3.tblacklist "
                            f"where FCarNumber = '{car_number}' "
                            f"and FActivity = 1")
                is_blocked = cur.fetchall()

                cur.execute(f"select FID "
                            f"from sac3.tguest "
                            f"where FRemoteID = {remote_id}")
                is_exist = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["status"] = "ACCESS_DENIED"
                    ret_value["desc"] = "отказ в регистрации " \
                                        "(на этапе проверки учетная запись компании или пользователя не активна)"

                elif len(is_blocked) != 0:
                    ret_value["status"] = "IS_BLOCKED"
                    ret_value["desc"] = "car_is_blocked"

                elif len(is_exist) != 0:
                    ret_value["status"] = "WARNING"
                    ret_value["desc"] = "is_exist"

                else:
                    # Загружаем данные в базу
                    cur.execute(f"insert into sac3.tguest("
                                    "FLastName, FFirstName, FMiddleName, "
                                    "FCarNumber, FRemoteID, FActivity, "
                                    "FDateCreate, FDateFrom, FDateTo, "
                                    "FAccountID, FPhone, FInviteCode) "
                                    "values ("
                                    f"'{last_name}', '{first_name}', '{middle_name}', '{car_number}', "
                                    f"{remote_id}, '1', now(), "
                                    f"'{date_from}', '{date_to}', {account_id}, '{phone_number}', {invite_code})")

                    connection.commit()

                    # Получаем FID для ответа
                    cur.execute(f"select FID "
                                f"from sac3.tguest "
                                f"where FRemoteID = {remote_id}")
                    is_exist = cur.fetchall()

                    ret_value["data"] = is_exist[0]

                    logger.add_log(f"CreateGuestDB.add_guest - "
                                   f"\tSUCCESS\tУспешно добавлен GUEST в базу данных {account_id}")
                    ret_value["status"] = "SUCCESS"
                    ret_value["desc"] = "Пропуск добавлен в базу."

            connection.close()

        except Exception as ex:
            logger.add_log(f"CreateGuestDB.add_guest - \tERROR\tОшибка работы с базой данных: {ex}")
            ret_value["desc"] = "Ошибка. Не удалось добавить пропуск."

        return ret_value
