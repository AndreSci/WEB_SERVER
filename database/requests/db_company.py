from misc.logger import Logger
from database.db_connection import connect_db


RET_VALUE = {"RESULT": "ERROR", "DESC": '', "DATA": dict()}
LOGGER = Logger()


class CompanyDB:

    @staticmethod
    def get_block_car(account_id: str, logger: Logger) -> dict:
        """ Принимает FID аккаунта/компании и возвращает информацию о поле 'FBlockCar' """

        ret_value = RET_VALUE

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:

                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                                f"where FCompanyID = tcompany.FID "
                                f"and taccount.FID = %s "
                                f"and tcompany.FActivity = 1 "
                                f"and taccount.FActivity = 1", (account_id, ))

                request_res = cur.fetchall()

                if len(request_res) > 0:

                    if request_res[0]['FBlockCar'] == 0:
                        ret_value["RESULT"] = "ALLOWED"
                    else:
                        request_res["RESULT"] = "BANNED"
                        request_res["DESC"] = "Учетная запись заблокирована для выдачи пропусков на автомобиль"

                    ret_value['DATA'] = {'FBlockCar': request_res[0]['FBlockCar'],
                                         "FID": request_res[0]['FID']}
                else:
                    ret_value["DESC"] = f"Не удалось найти данные для ID: {account_id}"

            connection.close()

        except Exception as ex:
            ret_value["DESC"] = "Ошибка работы с БД"
            logger.exception(f"Ошибка работы с базой данных: {ex}")

        return ret_value

    @staticmethod
    def get_account_id_by_inn(inn: str) -> dict:
        """ Функция предоставляет FID из БД sac3.taccount """

        ret_value = RET_VALUE

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:

                cur.execute(f"select taccount.FID as FAccountID "
                            f"from sac3.tcompany, sac3.taccount "
                            f"where FINN = %s and tcompany.FID = taccount.FCompanyID", (inn, ))

                request_res = cur.fetchone()

                if request_res:
                    ret_value['RESULT'] = "SUCCESS"
                    ret_value['DATA'] = request_res
                else:
                    ret_value['DESC'] = "Не удалось найти ID по ИНН"

        except Exception as ex:
            ret_value['DESC'] = f"Ошибку вызвало: {ex}"
            LOGGER.exception(f"Ошибку вызвало: {ex}")


        return ret_value


    @staticmethod
    def add_contact(data: dict) -> dict:
        """ Функция предоставляет FID из БД sac3.taccount """

        ret_value = RET_VALUE

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:

                # Проверяем компанию и пользователя на доступность
                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                                f"where FCompanyID = tcompany.FID "
                                f"and taccount.FID = %s "
                                f"and tcompany.FActivity = 1 "
                                f"and taccount.FActivity = 1", (data.get('FAccountID'), ))

                request_res = cur.fetchone()

                if request_res:

                    cur.execute(f"select * from sac3.tcompany where FINN = %s", (str(data.get('FINN')), ))

                    inn_result = cur.fetchone()

                    if inn_result:

                        cur.execute(f"insert into sac3.tcompanycontact "
                                    f"(FCompanyID, FPhone, FOfficeNumber, FOKVED, FName, FDateCreate) "
                                    f"values "
                                    f"({inn_result.get('FID')}, '{data.get('FPhone')}', "
                                    f"'{data.get('FOfficeNumber')}', '{data.get('FOKVED')}',"
                                    f"'{data.get('FName')}',now());")

                        res = cur.rowcount

                        if res == 1:
                            ret_value['RESULT'] = "SUCCESS"
                            connection.commit()
                        else:
                            ret_value['DESC'] = f"Сервер SQL ответил кол. изменений = {res}"
                    else:
                        ret_value['DESC'] = f"Не удалось найти ИНН: {data.get('FINN')}"
                else:
                    ret_value['DESC'] = "Не удалось найти компанию"

        except Exception as ex:
            ret_value['DESC'] = f"Ошибку вызвало: {ex}"
            LOGGER.exception(f"Ошибку вызвало: {ex}")


        return ret_value

    @staticmethod
    def get_contact(data: dict) -> dict:
        """ Функция предоставляет FID из БД sac3.taccount """

        ret_value = RET_VALUE

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:

                # Проверяем компанию и пользователя на доступность
                cur.execute(f"select * from sac3.taccount, sac3.tcompany "
                                f"where FCompanyID = tcompany.FID "
                                f"and taccount.FID = %s "
                                f"and tcompany.FActivity = 1 "
                                f"and taccount.FActivity = 1", (data.get('FAccountID'), ))

                request_res = cur.fetchone()

                if request_res:

                    cur.execute(f"select * from sac3.tcompany where FINN = %s", (str(data.get('FINN')), ))

                    inn_result = cur.fetchone()

                    if inn_result:

                        cur.execute(f"select * from sac3.tcompanycontact "
                                    f"where FCompanyID = {inn_result.get('FID')} order by FID desc")

                        res = cur.fetchone()

                        if res:
                            ret_value['RESULT'] = "SUCCESS"
                            ret_value['DATA'] = {'name': res.get('FName'),
                                                'OKVED': res.get('FOKVED'),
                                                'office': res.get('FOfficeNumber'),
                                                'phone': res.get('FPhone'),
                                                 'date_create': str(res.get('FDateCreate'))
                                                }
                        else:
                            ret_value['DESC'] = f"Не удалось найти контакты по данному ИНН: {data.get('FINN')}"
                    else:
                        ret_value['DESC'] = f"Не удалось найти ИНН: {data.get('FINN')}"

                else:
                    ret_value['DESC'] = "Не удалось найти компанию"

        except Exception as ex:

            ret_value['DESC'] = f"Ошибку вызвало: {ex}"
            LOGGER.exception(f"Ошибку вызвало: {ex}")


        return ret_value