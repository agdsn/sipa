import model.wu.user
from model.wu.user import User


def init_context(app):
    model.wu.user.init_context(app)

# todo evaluate a parameter and decide which package to use (wu, hss, test(?))
