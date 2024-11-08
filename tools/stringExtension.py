import re


def capitalize_first_letter(s: str) -> str:
    return s[0].upper() + s[1:] if s else ""


def lower_first_letter(s: str) -> str:
    return s[0].lower() + s[1:] if s else ""


def is_vowel(char):
    vowels = "aeiouAEIOU"
    return char in vowels


def camel_to_snake(name: str) -> str:
    result = []
    for char in name:
        if char.isupper():
            result.append("_")
            result.append(char.lower())
        else:
            result.append(char)
    return "".join(result).lstrip("_")

def kebab_to_pascal(kebab_str: str) -> str:
    # Split the string by hyphens
    words = kebab_str.split('-')
    # Capitalize the first letter of each word and join them
    pascal_str = ''.join(word.capitalize() for word in words)
    return pascal_str


def plural(st: str) -> str:
    if st[-1] == "s":
        return st
    if st[-1] == "y" and not is_vowel(st[-2]):
        return f"{st[:-1]}ies"
    return f"{st}s"


class ModelName:
    pascal: str

    def __init__(self, name: str):
        self.pascal = capitalize_first_letter(name)

    @property
    def camel(self) -> str:
        return lower_first_letter(self.pascal)

    @property
    def snake(self) -> str:
        return camel_to_snake(self.camel)

    @property
    def kebab(self) -> str:
        return self.snake.replace("_", "-")

    def __str__(self):
        return self.camel
