from PIL import Image
from io import BytesIO
import base64
import os

from misc.logger import Logger


class FlipImg:
    """ Класс исправляет изображение до нужного размера с учётом фото сделанные на разных устройствах """
    @staticmethod
    def convert_img(res_json: dict, logger: Logger, max_size=1080) -> dict:
        """ Для проверки и изменения размера фото требуется словарь с полями id и img64 """
        ret_value = {"RESULT": "ERROR", "DESC": "", "DATA": ""}

        user_id = res_json.get('id')

        width = 0
        height = 0

        width_old = 0
        height_old = 0

        image = Image
        # Преобразуем данные(фото) из запроса в PIL/Image
        try:
            image = Image.open(BytesIO(base64.b64decode(res_json['img64'])))

            width = width_old = image.size[0]
            height = height_old = image.size[1]

        except Exception as ex:
            logger.add_log(f"WARNING\tFlipImg.convert_img\tНе удалось открыть фото из запроса: {ex}")

        if width >= max_size or height >= max_size:

            h1 = 0

            # Если ширина больше max_size и больше высоты
            if max_size <= width > height:
                h1 = int(1000 / width * 100) * 0.01
                width = int(width * h1)
                height = int(height * h1)

            # Если высота больше всех
            elif height >= max_size:
                h1 = int(1000 / height * 100) * 0.01
                width = int(width * h1)
                height = int(height * h1)

            # меняем размер
            image = image.resize((width, height))
            logger.add_log(f"EVENT\tFlipImg.convert_img\tДля id={user_id} "
                           f"процент изменения: {h1}% (новый размер: {width}x{height} - "
                           f"старый размер: {width_old}x{height_old})")

            try:

                exif_data = image.getexif()
                # ключ в словаре 274 он же Orientation в метаданных изображения
                orientation = exif_data[274]

                if orientation == 1:
                    # Ничего не даем
                    pass
                elif orientation == 2:
                    # Mirrored left to right
                    image = image.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    # Rotated 180 degrees
                    image = image.rotate(180)
                elif orientation == 4:
                    # Mirrored top to bottom
                    image = image.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 5:
                    # Mirrored along top-left diagonal
                    image = image.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 6:
                    # Разворот 90
                    image = image.rotate(-90, expand=True)
                elif orientation == 7:
                    # Mirrored along top-right diagonal
                    image = image.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 8:
                    # Разворот на 270
                    image = image.rotate(90, expand=True)
            except KeyError as ex:
                logger.add_log(f"WARNING\tFlipImg.convert_img\t"
                               f"Ошибка работы с метаданными, нет ключа в словаре: {ex}", print_it=False)
            except Exception as ex:
                logger.add_log(f"WARNING\tFlipImg.convert_img\tНе удалось получить метаданными: {ex}", print_it=False)

            # image.save(save_url)

            # Создаем файл для временного хранения
            it_saved = False
            try:
                if not os.path.exists("./temp"):
                    os.makedirs('./temp')

                image.save(f"./temp/{user_id}_img.jpg")

                it_saved = True
            except Exception as ex:
                logger.add_log(f"ERROR\tFlipImg.convert_img\tНе удалось создать и сохранить файл в папку ./temp: {ex}")

            if it_saved:
                with open("img64.jpg", 'rb') as file:
                    img_byt = file.read()
                    res_json['img64'] = base64.b64encode(img_byt)
                    # print(res_json['img64'])
                    # res_json['img64'] = 11
                    ret_value['RESULT'] = 'SUCCESS'

                # удаляем временную фотку
                os.remove(f"./temp/{user_id}_img.jpg")
        else:
            ret_value['RESULT'] = "SUCCESS"
        # image.show()

        return ret_value
