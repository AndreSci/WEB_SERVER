from misc.logger import Logger

import datetime
import os

import base64


class ErrorPhoto:
    @staticmethod
    def save(res_json: dict, log_path: str, logger: Logger) -> dict:
        """ Сохраняет фотографии в директории логов для оценки ошибки вызванной
        в процессе сохранения фото в терминалы распознания лица
        """

        json_replay = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        today = datetime.datetime.now()
        date_time = str(today.strftime("%Y-%m-%d-%H.%M.%S"))

        dir_ex = False

        # Проверяем путь для создания отчета об ошибке
        if not os.path.exists(f"{log_path}photo_errors/"):
            try:
                os.makedirs(f"{log_path}photo_errors/")
                dir_ex = True
            except Exception as ex:
                logger.add_log(f"ERROR\tErrorPhoto.save\tОшибка создания директории для фото: {ex}")
        else:
            dir_ex = True

        if dir_ex:
            try:
                # Сохраняем исходный код base64
                base_help_id = res_json.get('id')   # id полученный из ответа base_helper

                with open(f"{log_path}photo_errors/{base_help_id}_{date_time}.txt", 'w') as file:
                    file.write(res_json['img64'])

                img_data = base64.b64decode(res_json['img64'])

                # Сохраняем декодированное фото в файл
                with open(f"{log_path}photo_errors/{base_help_id}_{date_time}.jpg", 'wb') as file:
                    file.write(img_data)

                json_replay['RESULT'] = "SUCCESS"

            except Exception as ex:
                logger.add_log(f"ERROR\tErrorPhoto.save\tНе удалось сохранить фотографию в отчете по ошибкам: {ex}")

        return json_replay
