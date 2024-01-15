from flask import Blueprint, request, jsonify
from misc.consts import LOGGER, ALLOW_IP, ERROR_ACCESS_IP, ERROR_READ_JSON, ERROR_ON_SERVER, ConstControl
from misc.errors.save_photo import ErrorPhoto
from face_id.resize_img import FlipImg
from face_id.face_recognition import FaceClass
from database.driver.rest_driver import FaceDriver
from database.base_helper.helper import BSHelper


employee_blue = Blueprint('employee_blue', __name__, template_folder='templates', static_folder='static')


@employee_blue.route('/DoAddEmployeePhoto', methods=['POST'])
def add_employee_photo():
    """ Добавляет сотрудника с фото лица в терминалы """

    json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.info(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:
        # Проверяем наличие Json в запросе
        if request.is_json:
            res_json = request.json
            LOGGER.event(f"Получены данные: (id: {res_json.get('id')})")

            con_helper = BSHelper(ConstControl.get_set_ini())

            # Если нет фото, считается что сотрудник сам добавить фото позднее
            activity = 0

            try:  # Проверяем наличие фото для активации сотрудника в БД
                if len(res_json['img64']) > 100:
                    activity = 1

            except Exception as ex:
                LOGGER.exception(f"Не удалось проверить фото! {ex}")

            # Отправляем запрос на получение данных сотрудника
            res_base_helper = con_helper.get_card_holder(res_json, activity, LOGGER)
            result = res_base_helper.get("RESULT")

            LOGGER.add_log(f"EVENT\tDoAddEmployeePhoto\tПосле BaseHelper "
                           f"json: {res_base_helper['DATA'].get('id')} - {res_base_helper['DATA'].get('name')}",
                           print_it=False)

            if result == "SUCCESS" or result == "WARNING" and activity == 1:

                res_json["id"] = res_base_helper["DATA"].get("id")
                res_json["name"] = res_base_helper["DATA"].get("name")

                # Проверяем и меняем, если нужно, размер фото (максимальный размер для терминала 1080p.)
                # Значительная производительность замечена на 720p, так же облегчаете передачу данных терминалу
                FlipImg.convert_img(res_json, LOGGER, max_size=1080)

                # Ищем лицо на фото
                it_face = FaceClass()
                res_face_rec = it_face.is_face(res_json)

                LOGGER.add_log(f"EVENT\tDoAddEmployeePhoto\tРезультат обработки фотографии: {res_face_rec}",
                               print_it=False)

                # подключаемся к драйверу Распознания лиц
                connect_driver = FaceDriver(ConstControl.get_set_ini())
                res_driver = connect_driver.add_person_with_face(res_json, LOGGER)

                if res_driver["RESULT"] == "ERROR":
                    json_replay['DATA'] = res_driver['DATA']
                    result = 'DRIVER'

                    # отменяем заявку в базе через base_helper
                    con_helper.deactivate_person(res_json, LOGGER)
                    LOGGER.add_log(f"WARNING\tDoAddEmployeePhoto\tОтмена пропуска в BaseHelper "
                                   f"из-за ошибки на Драйвере распознания лиц")

                    # Сохраняем фото в log_path где папка photo_errors
                    ErrorPhoto.save(res_json, ConstControl.get_set_ini().get('log_path'), LOGGER)
            elif result == "SUCCESS" or result == "WARNING" and activity == 0:
                result = "NO_FACE"

            if result == "EXCEPTION":
                pass
            else:
                # Незначительная нагрузка
                json_replay["DESC"] = res_base_helper["DESC"]

            # Задумка на случай добавления ситуаций
            if result == "SUCCESS":
                json_replay["RESULT"] = "SUCCESS"
                LOGGER.add_log(f"SUCCESS\tDoAddEmployeePhoto\t"
                               f"Успешно добавлено лицо под id: {res_base_helper['DATA'].get('id')}")
            elif result == "ERROR":
                LOGGER.add_log(f"ERROR\tDoAddEmployeePhoto\t{json_replay['DESC']}")
            elif result == "EXCEPTION":
                LOGGER.add_log(f"ERROR\tDoAddEmployeePhoto\tEXCEPTION")
            elif result == "DRIVER":

                # Вариации ошибок связанные с фото и перевод их на русский язык
                try:
                    if 'Photo registered' == json_replay['DATA']['msg']:
                        str_msg = "Лицо уже зарегистрировано"
                    elif 'Face deflection angle is too large' == json_replay['DATA']['msg']:
                        str_msg = "Неудачное расположение лица на фото"
                    elif 'Face clarity is too low' == json_replay['DATA']['msg']:
                        str_msg = "На фото плохо видно лицо"
                    elif 'Registered photo size cannot exceed 2M' == json_replay['DATA']['msg']:
                        str_msg = "Фото слишком большого размера"
                    elif 'Face too large or incomplete' == json_replay['DATA']['msg']:
                        str_msg = "Лицо слишком большое или неполное"
                    elif 'The registered photo resolution is greater than 1080p' == json_replay['DATA']['msg']:
                        str_msg = "Размер фото слишком высоко (требуется не выше 1080р)"
                    else:
                        str_msg = "Не удалось распознать лицо на фото"

                    json_replay["DESC"] = f"Не удалось добавить фотографию в систему: {str_msg}"

                except Exception as ex:
                    LOGGER.add_log(f"ERROR\tDoAddEmployeePhoto\tНе удалось получить данные из ответа Драйвера {ex}")
                    json_replay["DESC"] = f"При добавлении фото произошла ошибка"

            elif result == "WARNING":
                LOGGER.add_log(f"WARNING\tDoAddEmployeePhoto\t{json_replay['DESC']}")
            elif result == "NotDefined":
                LOGGER.add_log(f"WARNING\tDoAddEmployeePhoto\t{json_replay['DESC']}")
            elif result == "NO_FACE":
                LOGGER.add_log(f"EVENT\tDoAddEmployeePhoto\t"
                               f"Создан сотрудник без фотографии с флагом activity = 0: {res_json}")
            else:
                pass

        else:
            LOGGER.add_log(f"ERROR\tDoAddEmployeePhoto\tОшибка, в запросе нет Json данных: {ERROR_READ_JSON}")
            json_replay["RESULT"] = "ERROR"
            json_replay["DESC"] = f"Ошибка на сервере: {ERROR_READ_JSON}"

    return jsonify(json_replay)


@employee_blue.route('/DoDeletePhoto', methods=['POST'])
def delete_person():
    json_replay = {"RESULT": "ERROR", "DESC": ERROR_ON_SERVER, "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.add_log(f"EVENT\tDoDeletePhoto запрос от ip: {user_ip}", print_it=False)

    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:
        try:
            res_json = request.json

            LOGGER.add_log(f"EVENT\tDoDeletePhoto\tПолучены данные: ("
                           f"id: {res_json.get('id')})")

            # Отправляем запрос на удаление данных сотрудника
            con_helper = BSHelper(ConstControl.get_set_ini())
            res_base_helper = con_helper.deactivate_person_apacsid(res_json, LOGGER)
            result = res_base_helper.get("RESULT")

            if result == "SUCCESS" or result == "WARNING":
                res_json["id"] = res_base_helper["DATA"].get("id")
                res_json["name"] = res_base_helper["DATA"].get("name")

                # создаем и подключаемся к драйверу Коли
                connect_driver = FaceDriver(ConstControl.get_set_ini())
                res_driver = connect_driver.delete_person(res_json, LOGGER)

                if res_driver['RESULT'] == "SUCCESS":
                    json_replay["RESULT"] = "SUCCESS"
                    json_replay["DESC"] = f"Пропуск успешно удалена."
                else:
                    json_replay['DESC'] = res_driver['DESC']

            else:
                LOGGER.add_log(f"ERROR\tDoDeletePhoto\tBaseHelper DESC: {res_base_helper.get('DESC')}, "
                               f"DATA: {res_base_helper.get('DATA')}")

        except Exception as ex:
            json_replay['DESC'] = ERROR_READ_JSON
            LOGGER.add_log(f"ERROR\tDoDeletePhoto\tИсключение вызвало {ex}")

    return jsonify(json_replay)