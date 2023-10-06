from misc.logger import Logger
from misc.allow_ip import AllowedIP
from misc.util import SettingsIni

LOGGER = Logger()
ALLOW_IP = AllowedIP()

ERROR_ACCESS_IP = 'access_block_ip'
ERROR_READ_JSON = 'error_read_request'
ERROR_ON_SERVER = 'server_error'

CLASS_SET_INI = SettingsIni()
SET_INI = dict()


class ConstControl:
    @staticmethod
    def allow_ip_read_file() -> bool:
        global ALLOW_IP
        ALLOW_IP.read_file(LOGGER)

        return True

    @staticmethod
    def set_ini() -> bool:
        global SET_INI

        res = CLASS_SET_INI.create_settings()
        if res.get('result'):
            SET_INI = CLASS_SET_INI.take_settings()
            return True
        else:
            LOGGER.add_log(f"ERROR\tConstControl.set_ini\t{res['desc']}")
            return False

    @staticmethod
    def get_set_ini():
        return SET_INI
