import hashlib
import base64
import re
import unicodedata


def capitalizeFirstLetter(s: str) -> str:
    return s[0].upper() + s[1:] if s else ""


def lowerFirstLetter(s: str) -> str:
    return s[0].lower() + s[1:] if s else ""


def isVowel(char):
    vowels = "aeiouAEIOU"
    return char in vowels


def camelToSnake(name: str) -> str:
    result = []
    for char in name:
        if char.isupper():
            result.append("_")
            result.append(char.lower())
        else:
            result.append(char)
    return "".join(result).lstrip("_")


def camelToKebab(camelStr: str):
    kebabStr = re.sub(r"([a-z])([A-Z])", r"\1-\2", camelStr)
    return kebabStr.lower()


def plural(st: str) -> str:
    if st[-1] == "s":
        return st
    if st[-1] == "y" and (not isVowel(st[-2])):
        return f"{st[:-1]}ies"
    return f"{st}s"


class ModelName:
    pascal: str

    def __init__(self, name: str):
        self.pascal = capitalizeFirstLetter(name)

    @property
    def camel(self) -> str:
        return lowerFirstLetter(self.pascal)

    @property
    def snake(self) -> str:
        return camelToSnake(self.camel)

    @property
    def kebab(self) -> str:
        return self.snake.replace("_", "-")

    def __str__(self):
        return self.camel


def hashAndEncode(inputString: str) -> str:
    hashObject = hashlib.sha256()
    hashObject.update(inputString.encode())
    binaryData: bytes = hashObject.digest()
    base64_encoded: bytes = base64.b64encode(binaryData)
    return base64_encoded.decode("utf-8")


def strip_unwanted_characters(s: str) -> str:
    result = s.replace("—", " - ")
    result = re.sub(r"[^a-zA-Z0-9\s.,!?;:\'’-]", "", result)
    result = re.sub(r"\s+", " ", result)
    return result


def isUUID(s: str):
    regex = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    return bool(re.match(regex, s))


def replace_non_typable_chars(s: str) -> str:
    # Define a mapping of non-typable characters to typable ones
    replacements = {
        '’': "'",
        '–': '-',
        '—': '-',
        '“': '"',
        '”': '"',
        '‘': "'",
        '…': '...',
        '«': '"',
        '»': '"'
    }
    
    # Normalize the string to NFKC form to handle composed characters
    normalized_str = unicodedata.normalize('NFKC', s)
    
    # Replace non-typable characters using the replacements dictionary
    for non_typable, typable in replacements.items():
        normalized_str = normalized_str.replace(non_typable, typable)
    
    # Replace any excess whitespace with a single space and strip leading/trailing spaces
    cleaned_str = re.sub(r'\s+', ' ', normalized_str).strip()
    
    return cleaned_str
