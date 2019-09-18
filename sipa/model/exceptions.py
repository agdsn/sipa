# -*- coding: utf-8 -*-

"""
Custom exceptions for sipa

OperationalError for MySQL and SERVER_DOWN for LDAP are global app handlers!
"""


class InvalidCredentials(Exception):
    pass


class UserNotFound(InvalidCredentials):
    pass


class PasswordInvalid(InvalidCredentials):
    pass


class MacAlreadyExists(Exception):
    pass


class NetworkAccessAlreadyActive(Exception):
    pass


class TerminationNotPossible(Exception):
    pass


class ContinuationNotPossible(Exception):
    pass


class DBQueryEmpty(Exception):
    pass


class LDAPConnectionError(Exception):
    pass


class UnknownError(Exception):
    pass
