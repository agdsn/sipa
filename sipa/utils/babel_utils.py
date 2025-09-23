from flask_babel import get_locale


def lang():
    l = get_locale()
    assert l is not None, "lang() must be called inside a request context"
    return str(l)


def get_weekday(day):
    l = get_locale()
    assert l is not None, "get_weekday() must be called inside a request context"
    return l.days['format']['wide'][day]
