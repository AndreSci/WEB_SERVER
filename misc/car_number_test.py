

class NormalizeCar:

    def __init__(self):

        self.str_bad_array = set("\p\r\n\t!@#$%^&*()_+=-*?:%;№\"\',./\\<> ")

        self._repl_old = 'ABCEHKMOPTXYЁ'
        self._repl_new = 'АВСЕНКМОРТХУЕ'
        self._repl_tuples = set(zip(self._repl_old, self._repl_new))

    def do_normal(self, number: str) -> str:
        number = number.upper()

        number = number.replace(' ', '')

        number = number.replace('РУС', '')
        number = number.replace('RUS', '')

        number = number.replace('REG', '')
        number = number.replace('РЕГ', '')

        for it in self.str_bad_array:
            number = number.replace(it, '')

        for rt in self._repl_tuples:  # латиницу в кириллицу
            number = number.replace(rt[0], rt[1])

        return number


if __name__ == "__main__":
    test = NormalizeCar()

    print(test.do_normal("РУС REGв100 >//pe\t999? \ndfdf"))  # В100РЕ999DFDF
