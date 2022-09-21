import graphene
from app.utilities.errors import *
from app.utilities.sendMail import sendPostReportMailToUser,sendUserReportMailToUser
import datetime
from app.models import *
from django.db.models import Q



"""
    Report Post
"""
class ReportPostMutation(graphene.Mutation):
    message = graphene.String()
    postId = graphene.Int()
    reporterId = graphene.Int()
    reasonId = graphene.Int()

    class Arguments:
        reporterId = graphene.Int()
        postId = graphene.Int()
        reasonId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        reporterId= kwargs.get('reporterId')
        postId= kwargs.get('postId')
        reasonId= kwargs.get('reasonId')
        if reporterId is not None:
            try:
                user = User.objects.using('default').get(user_id=reporterId)
            except User.DoesNotExist:
                raise NotFoundException("reporterId provided not found", 404)
        else:
            raise BadRequestException("invalid request; reporterId provided is invalid", 400)
        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id = postId)
                postUser = User.objects.using('default').get(user_id = post.user_id)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)
        if reasonId is not None:
            try:
                reason = ReportPostReason.objects.using('default').get(report_post_reason_id=reasonId)
            except ReportPostReason.DoesNotExist:
                raise NotFoundException("reasonId provided not found", 404)
        else:
            raise BadRequestException("invalid request; reasonId provided is invalid", 400)
        try:
            if ReportPost.objects.using('default').get(Q(post_id__exact=post.post_id) & Q(reporter_id__exact=user.user_id)):
                print("In TRY block")
                reportPost = ReportPost.objects.using('default').get(Q(post_id__exact=post.post_id) & Q(reporter_id__exact=user.user_id))
                reportPost.reason_id = reason.report_post_reason_id
                reportPost.reporter_id = user.user_id
                reportPost.count += 1
                reportPost.modified_on = datetime.datetime.now()
                reportPost.modified_on = datetime.datetime.now()
                reportPost.save()
                response = sendPostReportMailToUser(postUser.username, postUser.email, reason.report_post_reason_name)
                if response:
                    return ReportPostMutation(message="successfully updated report for the provided post", reasonId=reasonId, postId=postId, reporterId=reporterId)
        except ReportPost.DoesNotExist:
            print("in Except block")
            reportPost = ReportPost.objects.create(
                reason_id = reason.report_post_reason_id,
                reporter_id = user.user_id,
                post_id = post.post_id,
                count = 1,
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now(),
                created_by = user.user_id
            )
            response = sendPostReportMailToUser(postUser.username, postUser.email, reason.reason)
            reportPost.save()
            if response:
                return ReportPostMutation(message="successfully reported the provided post", reasonId=reasonId, postId=postId, reporterId=reporterId)

"""
    Report User
"""
class ReportUserMutation(graphene.Mutation):
    message = graphene.String()
    userId = graphene.Int()
    reporterId = graphene.Int()
    reasonId = graphene.Int()

    class Arguments:
        reporterId = graphene.Int()
        userId = graphene.Int()
        reasonId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        reporterId= kwargs.get('reporterId')
        userId= kwargs.get('userId')
        reasonId= kwargs.get('reasonId')
        if reporterId is not None:
            try:
                user1 = User.objects.using('default').get(user_id=reporterId)
            except User.DoesNotExist:
                raise NotFoundException("reporterId provided not found", 404)
        else:
            raise BadRequestException("invalid request; reporterId provided is invalid", 400)
        if userId is not None:
            try:
                user2 = User.objects.using('default').get(user_id = userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if reasonId is not None:
            try:
                reason = ReportUserReason.objects.using('default').get(report_user_reason_id=reasonId)
            except ReportUserReason.DoesNotExist:
                raise NotFoundException("reasonId provided not found", 404)
        else:
            raise BadRequestException("invalid request; reasonId provided is invalid", 400)

        try:
            if ReportUser.objects.using('default').get(Q(user_id__exact=user2.user_id) & Q(reporter_id__exact=user1.user_id)):
                reportUser = ReportUser.objects.using('default').get(Q(user_id__exact=user2.user_id) & Q(reporter_id__exact=user1.user_id))
                reportUser.reporter_id = user1.user_id
                reportUser.user_id = user2.user_id
                reportUser.reason_id = reason.report_user_reason_id
                reportUser.count += 1 
                reportUser.modified_on = datetime.datetime.now()
                reportUser.save()
                response = sendUserReportMailToUser(user2.username, user2.email, reason.report_user_reason_name)
                
                if response:
                    return ReportUserMutation(message="successfully updated report for the provided user", reasonId=reasonId, userId=userId, reporterId = reporterId)
        except ReportUser.DoesNotExist:

            reportUser = ReportUser.objects.create(
                reporter_id = user1.user_id,
                user_id = user2.user_id,
                report_user_reason_id = reason.report_user_reason_id,
                count = 1,
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now(),
                created_by = user1.user_id
            )
            response = sendUserReportMailToUser(user2.username, user2.email, reason.report_user_reason_name)
            reportUser.save()
            if response:
                return ReportUserMutation(message="successfully reported the provided user", reasonId=reasonId, userId=userId)


    
class Mutation(graphene.ObjectType):
    report_post = ReportPostMutation.Field()
    report_user = ReportUserMutation.Field()


