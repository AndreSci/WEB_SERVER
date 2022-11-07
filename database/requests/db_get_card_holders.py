import datetime
import fdb

from misc.logger import Logger
from database.db_connection import connect_db, connect_fire_bird_db


class CardHoldersDB:
    # функция отправки данных для таблицы sac3.tguest
    @staticmethod
    def get_sac3(account_id: str, logger: Logger) -> dict:
        """ Принимает id и logger """

        ret_value = {"status": False, "desc": ''}

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

                if len(request_activity) == 0:
                    ret_value["desc"] = "Не удалось найти данные CardHoldersDB.get_sac3"
                else:
                    ret_value["desc"] = "Успешно"
                    ret_value["status"] = True

            connection.close()

        except Exception as ex:
            ret_value["desc"] = "Ошибка работы с базой данных CardHoldersDB.get_sac3"
            logger.add_log(f"CardHoldersDB.get_sac3 - \tERROR\tОшибка работы с базой данных: {ex}")

        return ret_value

    @staticmethod
    def get_fdb(finn: str, logger: Logger) -> dict:
        """ Принимает словарь с данными и logger """

        ret_value = {"status": False, "data": list(), "desc": ''}

        try:
            # Создаем подключение
            connection = connect_fire_bird_db()

            cur = connection.cursor()

            cur.execute(f"select TAPCCARDHOLDER.FID1, FLASTNAME, FFIRSTNAME, FMIDDLENAME "
                        f"from TAPCTREEOBJECT, TAPCCARDHOLDER "
                        f"where FCOMPANYID1 = TAPCTREEOBJECT.FID1 and FALIAS = 'ИНН{finn}'")
            res = cur.fetchall()

            res_size = len(res)

            if res_size:

                ret_res = list()
                for it in res:
                    ret_res.append({"fid": str(it[0]), "flastname": it[1], "ffirstname": it[2], "fmiddlename": it[3]})

                ret_value["status"] = True
                ret_value["data"] = ret_res
                ret_value["desc"] = "Успешно"
            else:
                ret_value["desc"] = "Не удалось найти информацию CardHoldersDB.get_fdb"

            cur.close()

        except Exception as ex:
            ret_value["desc"] = "Ошибка работы с базой данных CardHoldersDB.get_fdb"
            logger.add_log(f"CardHoldersDB.get_fdb - \tERROR\tОшибка работы с базой данных: {ex}")

        return ret_value
