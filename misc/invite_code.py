from database.requests.db_guest import CreateGuestDB
from misc.consts import LOGGER
import random


def gen_invite_code() -> dict:
    """ Генератор случайных чисел для InviteCode(код приглашения гостя) """

    ret_value = {"RESULT": False, "DESC": '', "DATA": list()}
    index = 0

    while True:
        index += 1
        invite_code = random.randint(100000, 999999)
        from_db_res = CreateGuestDB.check_invite_code(invite_code, LOGGER)

        if from_db_res['RESULT']:
            ret_value['RESULT'] = True
            ret_value['DATA'] = {'InviteCode': invite_code}
            break
        elif index >= 500:
            # Защита от завешивания запроса
            break

    return ret_value