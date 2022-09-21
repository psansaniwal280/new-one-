import graphene
from app.models import *


"""
    String Type
"""
class stringType(graphene.ObjectType):
    message = graphene.String()


class responseResetPasswordType(graphene.ObjectType):
    message = graphene.String()
    token = graphene.String()

