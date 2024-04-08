

class FioFix:
    """ Класс исправления Ф.И.О."""
    def __init__(self):
        self.str_bad_array = set("\p\r\n\t!@#$%^&*()+=*?:%;№\"\',./\\<>")

    def do_normal(self, last_name: str, first_name: str, middle_name: str = None) -> list:
        """ Убираем лишние символы из данных Ф.И.О."""
        if last_name:
            for it in self.str_bad_array:
                last_name = last_name.replace(it, '')
            last_name = last_name.title()
            last_name = last_name.strip()

        if first_name:
            for it in self.str_bad_array:
                first_name = first_name.replace(it, '')
            first_name = first_name.title()
            first_name = first_name.strip()

        if middle_name:
            for it in self.str_bad_array:
                middle_name = middle_name.replace(it, '')
            middle_name = middle_name.title()
            middle_name = middle_name.strip()

        return [last_name, first_name, middle_name]


if __name__ == "__main__":

    print(FioFix().do_normal("\tИванов", " иван", "Иван:ович"))
