import re


def convert_word(word: str) -> str:
    """ Функция убирает лишние спец символы """

    if word:
        result = re.sub("[^А-Яа-яA-Za-z0-9]", "", word)
    else:
        result = word

    return result


if __name__ == "__main__":
    print(convert_word("1236127368273000"))