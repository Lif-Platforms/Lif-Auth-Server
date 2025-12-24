class InvalidToken(Exception):
    pass

class InvalidCredentials(Exception):
    pass

class AccountSuspended(Exception):
    pass

class UserNotFound(Exception):
    pass

class Conflict(Exception):
    pass

class TwoFaNotSetup(Exception):
    pass