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

    ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.info(f"Запрос от ip: {user_ip}", print_it=False)

    # Проверяем разрешен ли доступ для IP
    if not ALLOW_IP.find(user_ip, LOGGER):
        ret_value["DESC"] = ERROR_ACCESS_IP
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
                    print(f"ТЕСТОВАЯ ЗАПИСЬ : {activity} - {len(res_json['img64'])}")

            except Exception as ex:
                LOGGER.exception(f"Не удалось проверить фото! {ex}")

            # Отправляем запрос на получение данных сотрудника
            res_base_helper = con_helper.get_card_holder(res_json, activity, LOGGER)
            result = res_base_helper.get("RESULT")

            LOGGER.event(f"После BaseHelper "
                           f"json: {res_base_helper['DATA'].get('id')} - {res_base_helper['DATA'].get('name')}",
                           print_it=False)

            if result == "SUCCESS" or result == "WARNING":

                res_json["id"] = res_base_helper["DATA"].get("id")
                res_json["name"] = res_base_helper["DATA"].get("name")

                if activity == 1:
                    # Проверяем и меняем, если нужно, размер фото (максимальный размер для терминала 1080p.)
                    # Значительная производительность замечена на 720p, так же облегчаете передачу данных терминалу
                    FlipImg.convert_img(res_json, LOGGER, max_size=1080)

                    # Ищем лицо на фото
                    it_face = FaceClass()
                    res_face_rec = it_face.is_face(res_json)

                    LOGGER.event(f"Результат обработки фотографии: {res_face_rec}", print_it=False)

                    # подключаемся к драйверу Распознания лиц
                    connect_driver = FaceDriver(ConstControl.get_set_ini())
                    res_driver = connect_driver.add_person_with_face(res_json, LOGGER)

                    if res_driver["RESULT"] == "ERROR":
                        ret_value['DATA'] = res_driver['DATA']
                        result = 'DRIVER'

                        # отменяем заявку в базе через base_helper
                        con_helper.deactivate_person(res_json, LOGGER)
                        LOGGER.warning(f"Отмена пропуска в BaseHelper "
                                       f"из-за ошибки на Драйвере распознания лиц")

                        # Сохраняем фото в log_path где папка photo_errors
                        ErrorPhoto.save(res_json, ConstControl.get_set_ini().get('log_path'), LOGGER)
                else:
                    result = "NO_IMG64"

            if result == "EXCEPTION":
                pass
            else:
                # Незначительная нагрузка
                ret_value["DESC"] = res_base_helper["DESC"]

            # Задумка на случай добавления ситуаций
            if result == "SUCCESS":
                ret_value["RESULT"] = "SUCCESS"
                LOGGER.event(f"Успешно добавлено лицо под id: {res_base_helper['DATA'].get('id')}")
            elif result == "ERROR":
                LOGGER.error(f"{ret_value['DESC']}")
            elif result == "EXCEPTION":
                LOGGER.add_log(f"ERROR\tDoAddEmployeePhoto\tEXCEPTION")
            elif result == "DRIVER":

                # Вариации ошибок связанные с фото и перевод их на русский язык
                try:
                    if 'Photo registered' == ret_value['DATA']['msg']:
                        str_msg = "Лицо уже зарегистрировано"
                    elif 'Face deflection angle is too large' == ret_value['DATA']['msg']:
                        str_msg = "Неудачное расположение лица на фото"
                    elif 'Face clarity is too low' == ret_value['DATA']['msg']:
                        str_msg = "На фото плохо видно лицо"
                    elif 'Registered photo size cannot exceed 2M' == ret_value['DATA']['msg']:
                        str_msg = "Фото слишком большого размера"
                    elif 'Face too large or incomplete' == ret_value['DATA']['msg']:
                        str_msg = "Лицо слишком большое или неполное"
                    elif 'The registered photo resolution is greater than 1080p' == ret_value['DATA']['msg']:
                        str_msg = "Размер фото слишком высоко (требуется не выше 1080р)"
                    else:
                        str_msg = "Не удалось распознать лицо на фото"

                    ret_value["DESC"] = f"Не удалось добавить фотографию в систему: {str_msg}"

                except Exception as ex:
                    LOGGER.exception(f"Не удалось получить данные из ответа Драйвера {ex}")
                    ret_value["DESC"] = f"При добавлении фото произошла ошибка"

            elif result == "WARNING":
                LOGGER.warning(f"{ret_value['DESC']}")
            elif result == "NotDefined":
                LOGGER.warning(f"{ret_value['DESC']}")
            elif result == "NO_IMG64":
                ret_value['RESULT'] = 'SUCCESS_GUEST'
                LOGGER.event(f"Создан сотрудник без фотографии с флагом activity = 0: {res_json}")
            else:
                pass

        else:
            LOGGER.error(f"Ошибка, в запросе нет Json данных: {ERROR_READ_JSON}")
            ret_value["RESULT"] = "ERROR"
            ret_value["DESC"] = f"Ошибка на сервере: {ERROR_READ_JSON}"

    return jsonify(ret_value)


@employee_blue.route('/DoDeletePhoto', methods=['POST'])
def delete_person():
    json_replay = {"RESULT": "ERROR", "DESC": ERROR_ON_SERVER, "DATA": ""}

    user_ip = request.remote_addr
    LOGGER.event(f"Запрос от ip: {user_ip}", print_it=False)

    if not ALLOW_IP.find(user_ip, LOGGER):
        json_replay["DESC"] = ERROR_ACCESS_IP
    else:
        try:
            res_json = request.json

            LOGGER.info(f"Получены данные: id: {res_json.get('id')}")

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
                LOGGER.error(f"BaseHelper DESC: {res_base_helper.get('DESC')}, DATA: {res_base_helper.get('DATA')}")

        except Exception as ex:
            json_replay['DESC'] = ERROR_READ_JSON
            LOGGER.exception(f"Исключение вызвало {ex}")

    return jsonify(json_replay)