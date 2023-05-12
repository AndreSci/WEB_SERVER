import re


def convert_word(word: str) -> str:
    """ Функция убирает лишние спец символы """

    if word:
        result = re.sub("[^А-Яа-яA-Za-z1-9]", "", word)
    else:
        result = word

    return result
