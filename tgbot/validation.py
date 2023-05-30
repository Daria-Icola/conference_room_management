import re


def password_validation(password):
    if re.fullmatch(r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z]{9,}$", password):
        return True
    else:
        return False


def username_validation(username):
    if re.fullmatch(r'^[A-ЯЁ][а-яё]+\s[A-ЯЁ][а-яё]+$', username):
        return True
    else:
        return False
