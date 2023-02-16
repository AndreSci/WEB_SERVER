import cv2
import numpy
import os
import base64

from misc.timer import timer_function


class FaceClass:
    """ Класс поиска позиции лица на фото и возвращает нужный угол для правки """

    def __init__(self):
        self.FACE_CASCADE_DB = cv2.CascadeClassifier(r'./mod/front.xml')
        self.EYE_CASCADE = cv2.CascadeClassifier(r'./mod/eye.xml')
        self.MOUTH_CASCADE = cv2.CascadeClassifier(r'./mod/mouth.xml')

        self.img = ""
        self.test_img = ''
        self.dict_img = {}

    def is_face(self, json_data: dict):
        """ Принимает json с фото base64 уже готового размера """

        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        img_create = False
        face_detected = False

        try:
            # Преобразуем фото в cv2 формат
            img_data = base64.b64decode(json_data['img64'])
            self.test_img = self.img = cv2.imdecode(numpy.fromstring(img_data, numpy.uint8), cv2.IMREAD_UNCHANGED)

            img_create = True

        except Exception as ex:
            ret_value['DESC'] = f"Ошибка обработки входных данных: {ex} "

        if img_create:
            # Пробуем найти лицо и повернуть
            try:
                for flip in range(1, 10, 1):
                    self.change_orientation(flip)

                    # Пробуем найти лицо на фото
                    faces = self.FACE_CASCADE_DB.detectMultiScale(self.img, 1.1, 19)

                    if faces != ():

                        # Пробуем найти глаза на фото
                        eyes = self.EYE_CASCADE.detectMultiScale(self.img, 1.1, 19)

                        if eyes != ():
                            # Пробуем найти рот на фото
                            mouths = self.MOUTH_CASCADE.detectMultiScale(self.img, 1.1, 19)

                            if mouths != ():
                                # print(f"Это глаза:\n{eyes}")
                                # print(f"Это рот:\n{mouths}")

                                face_detected = True

                                file_name = f'{json_data["id"]}_img_{flip}.jpg'

                                try:
                                    # TODO после тестов нужно будет добавить метод продолжения поиска лица
                                    #  после определения что рот выше глаз
                                    if eyes[0][1] < mouths[0][1]:
                                        # print("Глаза выше рта.")
                                        pass
                                    else:
                                        cv2.imwrite(os.path.join("./temp/pos_eye_mouth", file_name), self.img)

                                        with open(f"./temp/pos_eye_mouth/"
                                                  f'{json_data["id"]}_img_{flip}.txt', "w") as file:
                                            file.write(f"eyes: {eyes}\nmouth: {mouths}")

                                except Exception as ex:
                                    ret_value['DESC'] = ret_value['DESC'] + f"Ошибка сравнения высоты глаз и рта: {ex}"

                                cv2.imwrite(os.path.join("./temp", file_name), self.img)

                                try:    # Выгружаем в правильный base64 (opencv кодирует в своей стиль)
                                    with open(f"./temp/{file_name}", "rb") as file:
                                        json_data['img64'] = base64.b64encode(file.read())

                                    ret_value['RESULT'] = "SUCCESS"
                                    ret_value['DATA'] = {"path": f"./temp/{file_name}", "flip": flip}

                                    # TODO включить после тестов
                                    # os.remove(f"./temp/{file_name}")

                                except Exception as ex:
                                    ret_value['DESC'] = ret_value['DESC'] + f" Не удалось прочитать файл: {ex}"

                                break

            except Exception as ex:
                ret_value["DESC"] = f"Ошибка в процессе поиска угла: {ex}"

        if not face_detected:
            ret_value["DESC"] = ret_value["DESC"] + "Не удалось найти лицо на фото"

        return ret_value

    def change_orientation(self, orientation):
        """ Поворачивает фото по индексу orientation, \n
        порядок изменён и не может быть использован для определения позиции фото из разных аппаратов. """

        # Зона 360 --------------------------------------
        if orientation == 1:
            # без изменений
            pass
        elif orientation == 2:
            # 90
            self.img = cv2.rotate(self.test_img, cv2.ROTATE_90_CLOCKWISE)
        elif orientation == 3:
            # 180
            self.img = cv2.rotate(self.test_img, cv2.ROTATE_180)
        elif orientation == 4:
            # 270
            self.img = cv2.rotate(self.test_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # ----------------------------------------------

        # зеркальные Если не удалось найти в зоне 360
        elif orientation == 5:
            # Зеркало
            self.img = cv2.flip(self.test_img, 1)
        elif orientation == 6:
            # 270 + зеркало
            temp_img = cv2.flip(self.test_img, 0)
            self.img = cv2.rotate(temp_img, cv2.ROTATE_90_CLOCKWISE)
        elif orientation == 7:
            # 90 + зеркало
            temp_img = cv2.flip(self.test_img, 0)
            self.img = cv2.rotate(temp_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif orientation == 8:
            # 180 + зеркало
            self.img = cv2.flip(self.test_img, 0)

        # не уверен в номере 9
        elif orientation == 9:
            # 180
            self.img = cv2.flip(self.test_img, -1)
