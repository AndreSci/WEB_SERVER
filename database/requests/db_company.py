from misc.logger import Logger
from database.db_connection import connect_db


class CompanyDB:

    @staticmethod
    def get_block_status(account_id: str, logger: Logger) -> dict:
        """ Принимает FID аккаунта/компании и возвращает информацию о поле 'FBlockCar' """

        ret_value = {"status": False, "desc": ''}

        try:
            # Создаем подключение
            connection = connect_db()

            with connection.cursor() as cur:

                cur.execute(f"select * from sac3.taccount "
                                f"and taccount.FID = {account_id} "
                                f"and taccount.FActivity = 1")

                request_activity = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["desc"] = f"Не удалось найти данные для ID: {account_id}"
                else:
                    ret_value["desc"] = "Успешно"
                    ret_value["status"] = True

            connection.close()

        except Exception as ex:
            ret_value["desc"] = "Ошибка работы с базой данных CompanyDB.get_block_status"
            logger.add_log(f"CompanyDB.get_block_status - \tERROR\tОшибка работы с базой данных: {ex}")

        return ret_value

