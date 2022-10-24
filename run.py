from misc.util import SettingsIni
from misc.allow_ip import AllowedIP
from misc.logger import Logger


def main():

    settings = SettingsIni()
    result = settings.create_settings()

    logger = Logger(settings)

    if not result["result"]:

        print(result["desc"])
        return

    allow_ip = AllowedIP()

    allow_ip.read_file(logger)


if __name__ == '__main__':
    main()
