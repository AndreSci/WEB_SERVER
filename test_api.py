from misc.util import SettingsIni
from misc.allow_ip import AllowedIP
from misc.logger import Logger
import pytest


def test_set():
    set_ini = SettingsIni()
    result = set_ini.create_settings()

    if result["result"]:
        return True


def test_ip():
    set_ini = SettingsIni()
    set_ini.create_settings()

    log = Logger(set_ini)

    allow_ip = AllowedIP()
    allow_ip.read_file(log)

    assert(allow_ip.find_ip("192.168.48.1", log) == True)  # True
    assert(allow_ip.find_ip("192.168.48.2", log) == False)  # False
    assert(allow_ip.find_ip("192.168.48.3", log) == True)  # True
    assert(allow_ip.find_ip("192.168.48.4", log) == False)  # False
    assert(allow_ip.find_ip("192.168.48.5", log) == False)  # False
    assert(allow_ip.find_ip("192.168.48.6", log) == False)  # False
    assert(allow_ip.find_ip("192.168.48.7", log) == False)  # False
    assert(allow_ip.find_ip("192.168.48.8", log) == False)  # False
