# -*- coding: utf-8 -*-

"""
Custom exceptions for sipa

OperationalError for MySQL and SERVER_DOWN for LDAP are global app handlers!
"""


class UserNotFound(Exception):
    pass


class PasswordInvalid(Exception):
    pass


class DBQueryEmpty(Exception):
    pass


class LDAPConnectionError(Exception):
    pass
