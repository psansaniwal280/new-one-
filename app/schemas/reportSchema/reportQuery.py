import graphene
from .reportType import *
from app.utilities.errors import *


class Query(graphene.ObjectType):

        #Report Post Reasons
    reportPostReasons = graphene.List(ReportPostReasonType)
    reportUserReasons = graphene.List(ReportUserReasonType)
    
    #Report Users Reason Detail
    reportUserReason = graphene.Field(UserReasonDetailObjectType, userId = graphene.Int(), reportUserReasonId = graphene.Int())

    #Report Post reason Detail
    reportPostReason = graphene.Field(PostReasonDetailObjectType, userId = graphene.Int(), reportPostReasonId = graphene.Int())


    #Report Post Reasons
    def resolve_reportPostReasons(self, info):
        return ReportPostReason.objects.all()

 #Report User Reasons
    def resolve_reportUserReasons(self, info):
        return ReportUserReason.objects.all()


 
#Report User Reason Detail
    def resolve_reportUserReason(self, info, **kwargs):
        userId = kwargs.get('userId')
        reasonId = kwargs.get('reportUserReasonId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
                
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if reasonId is not None:
            try:
                reason = ReportUserReason.objects.using('default').get(report_user_reason_id=reasonId)
                return UserReasonDetailObjectType(report_user_reason_id=reasonId, reason = reason.report_user_reason_name, description=reason.report_user_reason_description)
            except ReportUserReason.DoesNotExist:
                raise NotFoundException("reportUserReasonId provided not found")
        else:
            raise BadRequestException("invalid request; reportUserReasonId provided is invalid")

#Report User Reason Detail
    def resolve_reportPostReason(self, info, **kwargs):
        userId = kwargs.get('userId')
        reasonId = kwargs.get('reportPostReasonId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if reasonId is not None:
            try:
                reason = ReportPostReason.objects.using('default').get(report_post_reason_id=reasonId)
                return PostReasonDetailObjectType(report_post_reason_id=reasonId, reason = reason.report_post_reason_name, description=reason.report_post_reason_description)
            except ReportPostReason.DoesNotExist:
                raise NotFoundException("reportPostReasonId provided not found")
        else:
            raise BadRequestException("invalid request; reportPostReasonId provided is invalid")



    

    
    
 




  