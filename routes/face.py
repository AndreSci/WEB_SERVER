import datetime
from flask import Blueprint, request, jsonify
from misc.consts import LOGGER, ALLOW_IP, ERROR_ACCESS_IP, ConstControl
from face_id.resize_img import FlipImg
from face_id.face_recognition import FaceClass
from database.requests.db_guest import CreateGuestDB


face_blue = Blueprint('face_blue', __name__, template_folder='templates', static_folder='static')


@face_blue.route('/DoIsFace', methods=['GET'])
def it_face_route():
    """ Обрабатывает фото и определяет лицо """
    ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\tDoIsFace\tЗапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        ret_value["DESC"] = ERROR_ACCESS_IP
    else:

        try:
            json_request = request.json

            # Делаем уникальный id по времени
            today = datetime.datetime.today()
            json_request['id'] = str(today.strftime("%Y%m%d%H%M%S"))

            LOGGER.add_log(f"EVENT\tDoIsFace\tПолучены данные: img64.size: {len(json_request['img64'])}",
                           print_it=False)

            # Проверяем и меняем, если нужно, размер фото (максимальный размер для терминала 1080p.)
            # Значительная производительность замечена на 720p, так же облегчаете передачу данных терминалу
            FlipImg.convert_img(json_request, LOGGER, max_size=720)

            # Ищем лицо на фото
            it_face = FaceClass()
            ret_value = it_face.is_face(json_request)

            LOGGER.add_log(f"EVENT\tDoIsFace\tРезультат обработки фотографии: {ret_value}",
                           print_it=False)

            # Сохраняем и убираем лишние символы в коде (b' в начале и ' в конце ).
            ret_value['DATA']['img64'] = str(json_request['img64'])[2:-1]

        except Exception as ex:
            # Если в запросе нет Json данных
            LOGGER.add_log(f"ERROR\tDoIsFace\tОшибка чтения Json: В запросе нет {ex}")
            ret_value["DESC"] = "Ошибка в работе системы"

    return jsonify(ret_value)


@face_blue.route('/GetGuestPhotoByInviteCode', methods=['GET'])
def get_guest_photo():
    """ Получить фото гостя """
    ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\tGetGuestPhotoByInviteCode\tЗапрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        ret_value['DESC'] = ERROR_ACCESS_IP
    else:

        try:
            request_data = request.args

            # Получаем FID гостя
            db_result = CreateGuestDB.get_photo(request_data.get('InviteCode'), LOGGER)

            if db_result['RESULT']:
                id_guest = db_result['DATA'].get('FID')

                with open(f"{ConstControl.get_set_ini().get('term_path')}/{id_guest}.txt", 'r') as file:
                    ret_value['DATA'] = file.read()

                ret_value['RESULT'] = "SUCCESS"
            else:
                ret_value['DESC'] = db_result['DESC']

        except Exception as ex:
            LOGGER.add_log(f"ERROR\tGetGuestPhotoByInviteCode\tИсключение вызвало: {ex}")
            ret_value['DESC'] = f"Исключение вызвало: {ex}"

    return jsonify(ret_value)
