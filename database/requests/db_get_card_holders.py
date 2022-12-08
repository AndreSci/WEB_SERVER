import datetime
import fdb

from misc.logger import Logger
from database.db_connection import connect_db, connect_fire_bird_db


class CardHoldersDB:
    # функция отправки данных для таблицы sac3.tguest

    def __init__(self):
        self.connection_is = 0
        self.connection_is_fdb = 0

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

    def get_fdb(self, finn: str, logger: Logger) -> dict:
        """ Принимает ИНН компании и logger """

        ret_value = {"status": False, "data": list(), "desc": ''}

        try:
            # Создаем подключение
            if self.connection_is_fdb == 0:
                self.connection_is_fdb = connect_fire_bird_db()

            cur = self.connection_is_fdb.cursor()

            cur.execute(f"select TAPCCARDHOLDER.FID1, FLASTNAME, FFIRSTNAME, FMIDDLENAME "
                        f"from TAPCTREEOBJECT, TAPCCARDHOLDER "
                        f"where FCOMPANYID1 = TAPCTREEOBJECT.FID1 and FALIAS = 'ИНН{finn}' "
                        f"order by FLASTNAME")
            res = cur.fetchall()

            res_size = len(res)

            if res_size:

                ret_res = list()
                for it in res:
                    ret_res.append({"fid": str(it[0]),
                                    "flastname": it[1], "ffirstname": it[2], "fmiddlename": it[3]})

                ret_value["status"] = True
                ret_value["data"] = ret_res
                ret_value["desc"] = "Успешно"
            else:
                ret_value["desc"] = "Не удалось найти информацию CardHoldersDB.get_fdb"

        except Exception as ex:
            ret_value["desc"] = "Ошибка работы с базой данных CardHoldersDB.get_fdb"
            logger.add_log(f"CardHoldersDB.get_fdb - \tERROR\tОшибка работы с базой данных: {ex}")

        return ret_value

    def get_with_face(self, remote_id: list, logger: Logger) -> dict:
        """ Принимает id и logger """

        ret_value = {"status": False, "desc": '', "data": dict()}
        sql_list = ', '.join(remote_id)
        try:
            # Создаем подключение
            if self.connection_is == 0:
                self.connection_is = connect_db()

            with self.connection_is.cursor() as cur:

                cur.execute(f"select FRemoteID "
                                "from vig_face.tperson "
                                "where FTag = 'Employee' "
                                "and FActivity = 1 "
                                f"and FRemoteID in ({sql_list})")
                request_activity = cur.fetchall()

                if len(request_activity) == 0:
                    ret_value["desc"] = "Не удалось найти данные CardHoldersDB.get_with_face"
                else:
                    ret_value["desc"] = "Успешно"
                    ret_value["status"] = True

                    ret_list = list()

                    for it in request_activity:
                        ret_list.append(it["FRemoteID"])

                    ret_value["data"] = ret_list

        except Exception as ex:
            ret_value["desc"] = "Ошибка работы с базой данных CardHoldersDB.get_with_face"
            logger.add_log(f"CardHoldersDB.get_sac3 - \tERROR\tОшибка работы с базой данных: {ex}")

        return ret_value
