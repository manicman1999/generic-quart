import bcrypt


def hashPassword(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def checkPassword(password: str, hashedPassword: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashedPassword.encode("utf-8"))
