from misc.util import SettingsIni
from misc.logger import Logger
from flask_server import web_flask


def main():

    settings = SettingsIni()
    result = settings.create_settings()

    logger = Logger(settings)

    if not result["result"]:

        print(result["desc"])
        return

    web_flask(logger, settings)


if __name__ == '__main__':
    main()
