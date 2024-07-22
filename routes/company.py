from flask import Blueprint, request, jsonify
from misc.consts import ALLOW_IP, ERROR_ACCESS_IP
from misc.logger import Logger
from database.requests.db_company import CompanyDB

logger = Logger()
company_blue = Blueprint('company_blue', __name__, template_folder='templates', static_folder='static')


@company_blue.route('/DoAddCompanyContact', methods=['POST', ])
def add_comp_contact():
    """ Добавляет данные компаний (новая запись в БД является главной) """

    ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": ''}

    user_ip = request.remote_addr
    logger.info(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, logger):
        ret_value["DESC"] = ERROR_ACCESS_IP
    else:
        json_request: dict = request.json

        if json_request:
            data = {'FAccountID': json_request.get('id'),
                    'FINN': json_request.get('inn'),
                    'FName': json_request.get('name'),
                    'FOKVED': json_request.get('OKVED'),
                    'FOfficeNumber': json_request.get('office'),
                    'FPhone': json_request.get('phone')
                    }
            ret_value = CompanyDB.add_contact(data)

        else:
           logger.error(f"Не удалось получить данные из JSON: {json_request}")
           ret_value['DESC'] = "Не удалось получить данные из JSON"

    return jsonify(ret_value)


@company_blue.route('/GetCompanyContact', methods=['GET', ])
def get_comp_contact():
    """ Получает данные по компании из поля sac3.companycontact """

    ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": ''}

    user_ip = request.remote_addr
    logger.info(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, logger):
        ret_value["DESC"] = ERROR_ACCESS_IP
    else:
        json_request: dict = request.json

        if json_request:
            data = {'FAccountID': json_request.get('id'),
                    'FINN': json_request.get('inn')
                    }
            ret_value = CompanyDB.get_contact(data)

        else:
           logger.error(f"Не удалось получить данные из JSON: {json_request}")
           ret_value['DESC'] = "Не удалось получить данные из JSON"

    return jsonify(ret_value)
