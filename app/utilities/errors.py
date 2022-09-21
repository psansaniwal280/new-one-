from graphql import GraphQLError

class NotFoundException(Exception):

    def __init__(self, message, status=404):
        if status:
            self.context  = status
        super().__init__(message)

class BadRequestException(Exception):
    def __init__(self, message, status=400):
        if status:
            self.context  = status
        super().__init__(message)

class ConflictException(Exception):
    def __init__(self, message, status=409):
        if status:
            self.context  = status
        super().__init__(message)

class AuthorizationException(Exception):
    def __init__(self, message, status=401):
        if status:
            self.context  = status
        super().__init__(message)

class NoContentException(Exception):
    def __init__(self, message, status=204):

        if status:
            self.context = status
        super().__init__(message)
