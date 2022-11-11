import requests
from misc.logger import Logger


class BSHelper:
    """ Класс связи с base_helper """
    def __init__(self, set_ini):
        self.settings_ini = set_ini

    def get_card_holder(self, res_json: dict, logger: Logger) -> dict:
        """ Отправляем запрос в base_helper, где добавляется заявка и возвращает её ID """
        result = dict()

        try:
            res_base_helper = requests.get(f'http://{self.settings_ini["hl_host"]}:'
                                           f'{self.settings_ini["hl_port"]}/getcardholderbyfid',
                                           params={"fid": res_json["id"]})

            res_base_helper = res_base_helper.json()
            print(res_base_helper)
            result["result"] = res_base_helper.get("RESULT")
            result["DESC"] = res_base_helper.get("Description")
        except Exception as ex:
            logger.add_log(f"ERROR\tBSHelper.get_card_holder\t1: error_with_base_helper: {ex}")
            result["DESC"] = "error_with_base_helper"
            result["result"] = "EXCEPTION"

        return result

    def deactivate_person(self, res_json: dict, logger: Logger) -> dict:
        """ Отправляем запрос в base_helper, для блокировки заявки """
        result = dict()

        try:
            res_base_helper = requests.get(f'http://{self.settings_ini["hl_host"]}:'
                                           f'{self.settings_ini["hl_port"]}/dodeactivateperson',
                                           params={"id": res_json["id"]})

            res_base_helper = res_base_helper.json()
            print(res_base_helper)
            result["result"] = res_base_helper.get("RESULT")
            result["DESC"] = res_base_helper.get("Description")
        except Exception as ex:
            logger.add_log(f"ERROR\tBSHelper.deactivate_person\t1: error_with_base_helper: {ex}")
            result["DESC"] = "error_with_base_helper"
            result["result"] = "EXCEPTION"

        return result
