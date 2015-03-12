from flask_babel import get_locale


def lang():
    return str(get_locale())