import graphene
from app.models import *



class ReportPostReasonType(graphene.ObjectType):
    report_post_reason_id = graphene.Int()
    report_post_reason_name = graphene.String()

class ReportUserReasonType(graphene.ObjectType):
    report_user_reason_id = graphene.Int()
    report_user_reason_name = graphene.String()

class UserReasonDetailObjectType(graphene.ObjectType):
    reason = graphene.String()
    description = graphene.String()
    report_user_reason_id = graphene.Int()

class PostReasonDetailObjectType(graphene.ObjectType):
    reason = graphene.String()
    description = graphene.String()
    report_post_reason_id = graphene.Int()