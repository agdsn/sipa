# -*- coding: utf-8 -*-

"""
Custom exceptions for sipa
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


class SubnetFull(Exception):
    pass


class DBQueryEmpty(Exception):
    pass


class UnknownError(Exception):
    pass


class UserNotContactableError(Exception):
    pass


class TokenNotFound(InvalidCredentials):
    pass
