from misc.logger import Logger
from database.db_connection import connect_db


class CompanyDB:

    @staticmethod
    def get_block_car(account_id: str, logger: Logger) -> dict:
        """ Принимает FID аккаунта/компании и возвращает информацию о поле 'FBlockCar' """

        ret_value = {"RESULT": "ERROR", "DESC": '', "DATA": ""}

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
            logger.add_log(f"ERROR\tCompanyDB.get_block_status - Ошибка работы с базой данных: {ex}")

        return ret_value
