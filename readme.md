<img src="web_rum_img.png" alt="Описание изображения" width="600">

[![Build Status](https://img.shields.io/badge/python-3.9-green)](https://www.python.org/downloads/) ![Build Status](https://img.shields.io/badge/Flask-2.0.3-red) ![Build Status](https://img.shields.io/badge/PyMySQL-1.1.1-orange) ![Build Status](https://img.shields.io/badge/Firebird_DB-2.5.0-red)


Требуется установленная база данных FIREBIRD на сервере, где запущен сервис WEB_INTERFACE
файл установки - Firebird-2.5.0.26074_1_x64.exe в папке "setup"

------------------------------------------------------
!Вся документация находится в папке readme:
# Методы:
## Защита
+ DoAddIP - Добавить новый IP для доступа к API

## Сотрудники
+ DoCreateCardHolder - Создать пропуск сотруднику
+ DoGetCardHolders - Получить список сотрудников компании
+ DoDeleteCardHolder - Заблокировать карту сотрудника

## Терминал лиц
+ DoAddEmployeePhoto - Добавить фото сотруднику
+ DoAddPerson - Добавить персону в терминал
+ DoAddPhoto - Добавить фото в терминал
+ DoDeletePhoto - Удалить фото из терминала
+ DoUpdatePerson - Обновить данные персоны

## Гости
+ DoBlockGuest - Заблокировать заявку на гостя
+ DoChangeTimeAccess - Изменить период действия пропуска на гостя
+ DoCreateGuest - Создать заявку на гостя
