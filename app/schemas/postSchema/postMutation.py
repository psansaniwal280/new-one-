import graphene
from graphene_file_upload.scalars import Upload

from app.utilities import Verification
from app.utilities.errors import *
from app.models import *
from django.conf import settings
from app.utilities.uploadFileToAws import upload_to_aws
from app.utilities.extractWord import extract_tags_mentions
from django.db.models import Q
from django.db.models import Max, Avg
import datetime
import os
import io
from app.schemas.commonObjects.objectTypes import *
from app.utilities.toBigInt import BigInt
from app.utilities.standardizemethods import standardize_roundOf
from app.utilities.compressVideo import compress_video
from app.schemas.postSchema.postType import *

"""
    Add Post 
"""


# class InputPostType(graphene.InputObjectType):
# title = graphene.String()
# #media = graphene.String()
# user_rating = graphene.Float()
# is_verified_booking = graphene.Boolean()
# user_id = graphene.Int()
# description = graphene.String()
# venue_id = graphene.String()

class CreatePostMutation(graphene.Mutation):
    message = graphene.String()
    post_id = graphene.Int()
    user_id = graphene.String()
    media = graphene.Field(MediaPostType)
    thumbnail = graphene.String()
    title = graphene.String()
    user_rating = graphene.Float()

    class Arguments:
        title = graphene.String()
        userRating = graphene.Float()
        isVerifiedBooking = graphene.Boolean()
        userId = graphene.Int()
        description = graphene.String()
        venueId = graphene.Int()
        media = Upload()
        thumbnail = Upload()

    def mutate(self, info, **kwargs):
        title = kwargs.get('title')
        userRating = kwargs.get('userRating')
        isVerifiedBooking = kwargs.get('isVerifiedBooking')
        userId = kwargs.get('userId')
        description = kwargs.get('description')
        venueId = kwargs.get('venueId')
        media = kwargs.get('media')
        thumbnail = kwargs.get('thumbnail')
        uid = userId

        video_file = info.context.FILES.get('0')
       
        file_path =  os.path.abspath(os.path.dirname(__file__)).split("/app")[0] + "/app/temp_files/video_file.mp4"
        
        with open(file_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

        if title is not None:
            pass
        else:
            raise BadRequestException("invalid request; title provided is invalid", 400)

        if isVerifiedBooking is not None:
            pass
        else:
            isVerifiedBooking = False

        if uid is not None:
            try:
                user = User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("buserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

        if venueId is not None:
            try:
                venue = Venue.objects.using('default').get(venue_id=venueId)
            except Venue.DoesNotExist:
                raise NotFoundException("venueId provided not found", 404)
        else:
            raise BadRequestException("invalid request; venueId provided is invalid", 400)

        # upload the media into the S3 bucket

        if media is not None:
            last_post = Post.objects.all().aggregate(Max('post_id'))
            print(last_post['post_id__max'] + 1)
            post_id = last_post['post_id__max'] + 1
            aws_link = settings.AWS_LINK
            folder_name1 = "post-media/video-original/"
            folder_name2 = "post-media/video-optimized/"

            file_name1 = "post_video_" + str(post_id) + ".mp4"
            file_name2 = "post_video_optimized_" + str(post_id) + ".mp4"
            media_link1 = aws_link + folder_name1 + file_name1
            media_link2 = aws_link + folder_name2 + file_name2
                
            with open(file_path, 'rb') as f:
                file = f.read()
            success_upload = upload_to_aws(io.BytesIO(file), settings.AWS_STORAGE_BUCKET_NAME, folder_name1, file_name1)

            if success_upload:
                compressVideo = compress_video(file_path, folder_name2, file_name2)
            print(success_upload, compressVideo)
            print(media_link1)
            print(media_link2)
        else:
            raise BadRequestException("invalid request; media provided is invalid", 400)

        # upload the thumbnail into the S3 bucket
        if thumbnail is not None:
            thumbnail_folder_name = "thumbnail/"
            thumbnail_file_name = "post_thumbnail_" + str(post_id) + ".jpg"
            thumbnail_media_link = aws_link + thumbnail_folder_name + thumbnail_file_name
            thumbnail_success_upload = upload_to_aws(thumbnail, settings.AWS_STORAGE_BUCKET_NAME, thumbnail_folder_name, thumbnail_file_name)
            print(thumbnail_success_upload)
            print(thumbnail_media_link)
        else:
            raise BadRequestException("invalid request; thumbnail provided is invalid", 400)

        if userRating is not None:
            userRating = round(userRating * 2.0) / 2.0
        else:
            raise BadRequestException("invalid request; userRating provided is invalid", 400)
        # add to the post model with all the details of the post.
        if success_upload and compressVideo:
            media_post = MediaPost.objects.create(
                media_post_url=media_link2,
                media_post_raw_url=media_link1,
                created_on=datetime.datetime.now(),
            )

            if media_post.media_post_id is not None:
                post = Post.objects.create(
                    media_post_id=media_post.media_post_id,
                    title=title,
                    user_rating=userRating,
                    is_verified_booking=isVerifiedBooking,
                    created_on=datetime.datetime.now(),
                    modified_on=datetime.datetime.now(),
                    created_by=userId,
                    user_id=userId,
                    post_description=description,
                    venue_id=venueId,
                    thumbnail=thumbnail_media_link
                )

        # extracting the hashtags word and mentioned usernames separatly
        hashtag_list, mentioned_list = extract_tags_mentions(description)
        # adding the hashtag words into the respective tables in DB.
        for word in hashtag_list:
            try:
                go = Tag.objects.using('default').get(tag_name=word)
                try:
                    PostTag.objects.using('default').get(post_id=post_id, tag_id=go.tag_id)
                except PostTag.DoesNotExist:
                    PostTag.objects.create(
                        post_id=post_id,
                        tag_id=go.tag_id,
                        created_on=datetime.datetime.now(),
                        modified_on=datetime.datetime.now(),
                        created_by=userId)
            except Tag.DoesNotExist:
                go = Tag.objects.create(
                    tag_name=word,
                    created_on=datetime.datetime.now(),
                    modified_on=datetime.datetime.now(),
                    created_by=userId
                )
                try:
                    PostTag.objects.using('default').get(post_id=post_id, tag_id=go.tag_id)
                except PostTag.DoesNotExist:
                    PostTag.objects.create(
                        post_id=post_id,
                        tag_id=go.tag_id,
                        created_on=datetime.datetime.now(),
                        modified_on=datetime.datetime.now(),
                        created_by=userId)

        # #adding the mentions username into the respective tables in DB.
        for username in mentioned_list:
            try:
                userObjList = User.objects.using('default').values('user_id', 'username')
                for usr in userObjList:
                    if usr['username'] == username:
                        PostMention.objects.create(
                            post_id=post_id,
                            user_id=usr['user_id'],
                            created_on = datetime.datetime.now(),
                            modified_on = datetime.datetime.now(),
                            created_by = userId )
            except User.DoesNotExist:
                pass

        return CreatePostMutation(message="Successully created the post", post_id=post.post_id, user_id=userId, title=title, user_rating=userRating, media=MediaPostType(media_post_id=media_post.media_post_id, media_post_url=media_post.media_post_url, media_post_raw_url=media_post.media_post_raw_url), thumbnail=thumbnail_media_link)


"""
    Update Post
"""


class EditPostMutation(graphene.Mutation):
    message = graphene.String()
    postId = graphene.Int()
    userId = graphene.Int()
    description = graphene.String()

    class Arguments():
        userId = graphene.Argument(BigInt)
        postId = graphene.Argument(BigInt)
        description = graphene.String()

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        postId = kwargs.get('postId')
        description = kwargs.get('description')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

        if post.user_id == userId:
            pass
        else:
            raise AuthorizationException("userId provided is not authorized to edit this post", 401)

        if description is not None:
            if description == "":
                description = None
            post.post_description = description 
            post.save()

            # extract hastags and mentions
            hashtag_words, mention_words = [], []
            hashtag_words, mention_words = extract_tags_mentions(description)
            for word in hashtag_words:
                try:
                    tag_obj = Tag.objects.using('default').get(tag_name=word)
                except Tag.DoesNotExist:
                    tag_obj = Tag.objects.create(tag_name=word)
                    tag_obj.save()
                try:
                    post_tag_obj = PostTag.objects.using('default').get(Q(tag_id=tag_obj.tag_id) & Q(post_id=postId))
                except PostTag.DoesNotExist:
                    post_tag_obj = PostTag.objects.create(
                        tag_id=tag_obj.tag_id,
                        post_id=postId,
                        created_on=datetime.datetime.now(),
                        modified_on=datetime.datetime.now(),
                        created_by=userId

                    )
                    post_tag_obj.save()

            for word in mention_words:
                try:
                    userObjList = User.objects.using('default').values('user_id', 'username')
                    for go in userObjList:
                        if go['username'] == word:
                            try:
                                mention_obj = PostMention.objects.using('default').get(user_id=go['user_id'], post_id=postId)
                            except PostMention.DoesNotExist:
                                mention_obj = PostMention.objects.create(
                                    user_id=userId,
                                    post_id=postId,
                                    created_on=datetime.datetime.now(),
                                    modified_on=datetime.datetime.now(),
                                    created_by=userId)
                                mention_obj.save()
                except User.DoesNotExist:
                    pass
        else:
            raise BadRequestException("invalid request; description provided is invalid", 400)
        return EditPostMutation(message="Successfully edited the post.", postId=post.post_id, userId=userId, description=description)


"""
    Delete Post
"""


class DeletePostMutation(graphene.Mutation):
    message = graphene.String()
    post_id = graphene.Int()
    user_id = graphene.Int()

    class Arguments():
        postId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        postId = kwargs.get('postId')
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)

                if post.user_id == userId:
                    post.delete()
                    return DeletePostMutation(message="Successfully deleted the post", post_id=postId, user_id=userId)
                else:
                    raise AuthorizationException("userId provided is not authorized to delete this post", 401)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)


"""
    Add Post Like
"""


class CreateAddPostLikeMutation(graphene.Mutation):
    post_likes_aggregate = graphene.Field(aggregateOutputObjectType)
    message = graphene.String()
    post_id = graphene.Int()
    user_id = graphene.Int()

    class Arguments:
        postId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        postId = kwargs.get('postId')

        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

        try:
            post_like = PostLike.objects.using('default').get(user_id=user.user_id, post_id=post.post_id)
            raise NoContentException("conflict in request; unable to like post that is already liked", 409)

        except PostLike.DoesNotExist:
            # last_post_like_id = PostLike.objects.using('default').all().aggregate(Max('post_like_id'))
            # lastPostLikeId = last_post_like_id['post_like_id__max']+1 if last_post_like_id['post_like_id__max'] else 1
            post_like = PostLike.objects.create(
                # post_like_id = lastPostLikeId,
                post_id=post.post_id,
                user_id=user.user_id,
                created_on=datetime.datetime.now(),
                modified_on=datetime.datetime.now(),
                created_by=userId
            )
            post.save()
            post_like.save()
            number_of_likes = PostLike.objects.using('default').filter(post_id=post.post_id).values_list('post_id', flat=True).count()
            return CreateAddPostLikeMutation(post_likes_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=number_of_likes)), message="successfully liked post", post_id=postId, user_id=userId)


"""
    Delete Post Like
"""


class UpdatePostLikeMutation(graphene.Mutation):
    message = graphene.String()
    post_likes_aggregate = graphene.Field(aggregateOutputObjectType)
    post_id = graphene.Int()
    user_id = graphene.Int()

    class Arguments:
        postId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        postId = kwargs.get('postId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

        try:
            post_like = PostLike.objects.using('default').get(post_id=postId, user_id=userId)
            post.save()
            post_like.delete()
            number_of_likes = PostLike.objects.using('default').filter(post_id=postId).values_list('post_id', flat=True).count()
            return UpdatePostLikeMutation(post_likes_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=number_of_likes)), message="successfully unliked post", post_id=postId, user_id=userId)
        except PostLike.DoesNotExist:
            raise NoContentException("conflict in request; unable to unlike post that is not liked", 409)


"""
    Add Post Saved
"""


class SavePostMutation(graphene.Mutation):
    message = graphene.String()
    post_saves_aggregate = graphene.Field(aggregateOutputObjectType)
    post_id = graphene.Int()
    user_id = graphene.Int()

    class Arguments:
        postId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        postId = kwargs.get('postId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

        try:
            post_save = PostSaved.objects.using('default').get(post_id=post.post_id, user_id=user.user_id)
            raise NoContentException("conflict in reuqest; unable to save post that is already saved", 409)
        except PostSaved.DoesNotExist:
            # last_post_save_id = PostSaved.objects.using('default').all().aggregate(Max('post_saved_id'))
            # lastPostSaveId = last_post_save_id['post_saved_id__max']+1 if last_post_save_id['post_saved_id__max'] else 1
            post_save = PostSaved.objects.create(
                # post_saved_id = lastPostSaveId,
                post_id=postId,
                user_id=userId,
                created_on=datetime.datetime.now(),
                modified_on=datetime.datetime.now(),
                created_by=userId
            )
            post_save.save()
            number_of_saves = PostSaved.objects.using('default').filter(post_id=post.post_id).values_list('post_id', flat=True).count()
            return SavePostMutation(message="successfully saved post", post_saves_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=number_of_saves)), post_id=postId, user_id=userId)


"""
    Delete Post Saved
"""


class UnSavePostMutation(graphene.Mutation):
    message = graphene.String()
    post_saves_aggregate = graphene.Field(aggregateOutputObjectType)
    post_id = graphene.Int()
    user_id = graphene.Int()

    class Arguments:
        postId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        postId = kwargs.get('postId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

        try:
            post_save = PostSaved.objects.using('default').get(post_id=postId, user_id=userId)
            post_save.delete()
            number_of_saves = PostSaved.objects.using('default').filter(post_id=post.post_id).values_list('post_id', flat=True).count()
            return UnSavePostMutation(message="successfully unsaved post", post_saves_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=number_of_saves)), post_id=postId, user_id=userId)
        except PostSaved.DoesNotExist:
            raise NoContentException("conflict in request; unable to unsave post that is not saved", 409)


# """
#     Add Post Share 
# """
# class InputSharePostType(graphene.InputObjectType):
# post_id = graphene.Field(BigInt)
# user_id = graphene.Field(BigInt)
# to_user_id = graphene.Field(BigInt)

# class SharePostMutation(graphene.Mutation):
# message = graphene.String()


# class Arguments:
#     post_data = InputSharePostType()


# def mutate(self, info, post_data):
#     try:
#         if post_data.post_id is not None:m
#             post = Post.objects.using('default').get(post_id=post_data.post_id)
#             post.total_shares = post.total_shares+1
#     except Post.DoesNotExist:
#         raise NotFoundException("post does not exist",404)

#     try:
#         user = User.objects.using('default').get(user_id=post_data.user_id)
#     except User.DoesNotExist:
#         raise NotFoundException("user does not exist", 404)

#     share_post = models.PostShared.objects.create(
#         post_shared_id = PostShared.objects.count()+1,
#         post_id = post_data.post_id,
#         sender_user_id = post_data.user_id,
#         receiver_user_id = post_data.to_user_id
#     )

#     post.save()
#     share_post.save()
#     return SharePostMutation(message="Successfully shared post")

"""
    Add Post Comment
"""


# class InputAddPostCommentType(graphene.InputObjectType):
# post_comment_id = graphene.Field(BigInt)
# user_id = graphene.Field(BigInt)
# post_id = graphene.Field(BigInt)
# comment = graphene.String()
# comment_reply_id = graphene.Field(BigInt)

class PostCommentMutation(graphene.Mutation):
    message = graphene.String()
    comment = graphene.String()
    postCommentId = graphene.Int()
    repliedCommentId = graphene.Int()
    userId = graphene.Int()
    postId = graphene.Int()
    post_comments_aggregate = graphene.Field(aggregateOutputObjectType)
    post_comment_replies_aggregate = graphene.Field(aggregateOutputObjectType)
    hashtags = graphene.List(hashtagSection)
    mentions = graphene.List(mentionSection)

    class Arguments:
        userId = graphene.Argument(BigInt)
        postId = graphene.Argument(BigInt)
        comment = graphene.String()
        repliedCommentId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        postId = kwargs.get('postId')
        comment = kwargs.get('comment')
        commentReplyId = kwargs.get('repliedCommentId')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException('userId provided is not found')
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException('postId provided is not found')
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)
        if comment is not None:
            pass
        else:
            raise BadRequestException("invalid request; comment provided is invalid", 400)
        if (comment and comment.strip()):
            pass
        else:
            raise BadRequestException("invalid request; comment provided is empty", 400)
        if commentReplyId is not None:
            try:
                reply = PostComment.objects.using('default').get(post_comment_id=commentReplyId, post_id=postId)
                reply_post_id = reply.post_id
            except PostComment.DoesNotExist:
                raise NotFoundException("Unable to reply to non existing comment", 404)
        else:
            reply_post_id = None

        # try:
        #     post = Post.objects.using('default').get(post_id=postId)
        #     post.total_comments = PostComment.objects.using('default').filter(post_id=postId).count()
        # except Post.DoesNotExist:
        #     raise NotFoundException("invalid request; postId provided not found",404)

        # Insert into UserSharedItinerary
        # last_post_comment_id = PostComment.objects.using('default').all().aggregate(Max('post_comment_id'))
        # lastPostCommentId = last_post_comment_id['post_comment_id__max']+1 if last_post_comment_id['post_comment_id__max'] else 1

        comment = PostComment.objects.create(
            # post_comment_id =  lastPostCommentId,
            user_id=userId,
            post_id=postId if reply_post_id == None else reply_post_id,
            comment=comment,
            comment_reply_id=commentReplyId,
            created_on=datetime.datetime.now(),
            modified_on=datetime.datetime.now(),
            created_by=userId
        )
        comment.save()
        # extracting the hashtags word and mentioned usernames separatly
        hashtag_list, mentioned_list = extract_tags_mentions(comment.comment)
        # adding the hashtag words into the respective tables in DB.
        return_hashtags, return_mentions = [], []
        for word in hashtag_list:
            try:
                go = Tag.objects.using('default').get(tag_name=word)
                try:
                    post_comment_tag = PostCommentTag.objects.using('default').get(post_comment_id=comment.post_comment_id, tag_id=go.tag_id)
                except PostCommentTag.DoesNotExist:

                    PostCommentTag.objects.create(
                        post_comment_id=comment.post_comment_id,
                        tag_id=go.tag_id,
                        created_on=datetime.datetime.now(),
                        modified_on=datetime.datetime.now(),
                        created_by=userId)
            except Tag.DoesNotExist:
                go = Tag.objects.create(
                    tag_name=word,
                    created_on=datetime.datetime.now(),
                    modified_on=datetime.datetime.now(),
                    created_by=userId)
                try:
                    post_comment_tag = PostCommentTag.objects.using('default').get(post_comment_id=comment.post_comment_id, tag_id=go.tag_id)
                except PostCommentTag.DoesNotExist:
                    PostCommentTag.objects.create(
                        post_comment_id=comment.post_comment_id,
                        tag_id=go.tag_id,
                        created_on=datetime.datetime.now(),
                        modified_on=datetime.datetime.now(),
                        created_by=userId)
            return_hashtags.append(hashtagSection(go.tag_name, go.tag_id))

        # adding the mentions username into the respective tables in DB.
        for username in mentioned_list:
            try:
                userObjList = User.objects.using('default').values('user_id', 'username')
                for go_user in userObjList:
                    if go_user['username'] == username: 
                        try:
                            PostCommentMention.objects.using('default').get(post_comment_id=comment.post_comment_id, user_id=go_user['user_id'])
                        except PostCommentMention.DoesNotExist:
                            PostCommentMention.objects.using('default').create(post_comment_id=comment.post_comment_id, user_id=go_user['user_id'])
                return_mentions.append(mentionSection(go_user['username'], go_user['user_id']))
        
            except User.DoesNotExist:
                pass

        return_comment = comment.comment

        # commentObj={
        #     "content": return_comment,
        #     "hashtags": return_hashtags,
        #     "mentions": return_mentions
        # }
        post.save()

        return PostCommentMutation(message="successfully added comment on post", comment=return_comment, hashtags=return_hashtags, mentions=return_mentions, postCommentId=comment.post_comment_id, userId=userId, postId=postId, repliedCommentId=commentReplyId if commentReplyId is not None else None, post_comments_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=PostComment.objects.using('default').filter(post_id=postId).count())), post_comment_replies_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=PostComment.objects.using('default').filter(comment_reply_id=commentReplyId).count())))


"""
    Update Post Comment
"""


# class InputUpdatePostCommentType(graphene.InputObjectType):
#     post_comment_id = graphene.Field(BigInt)
#     comment = graphene.String()

class UpdatePostCommentMutation(graphene.Mutation):
    message = graphene.String()
    comment = graphene.String()
    postCommentId = graphene.Int()
    post_comments_aggregate = graphene.Field(aggregateOutputObjectType)

    class Arguments:
        postCommentId = graphene.Int()
        comment = graphene.String()

    def mutate(self, info, postCommentId, comment):
        if postCommentId is not None:
            pass
        else:
            raise BadRequestException("invalid request; postCommentId provided is invalid", 400)
        if comment is not None:
            pass
        else:
            raise BadRequestException("invalid request; comment provided is invalid", 400)
        if (comment and comment.strip()):
            pass
        else:
            raise BadRequestException("invalid request; comment provided is empty", 400)

        try:
            comment_obj = PostComment.objects.using('default').get(post_comment_id=postCommentId)
            postId = comment_obj.post_id
            # extracting the hashtags word and mentioned usernames separatly
            hashtag_list, mentioned_list = extract_tags_mentions(comment)
            # adding the hashtag words into the respective tables in DB.
            for word in hashtag_list:
                try:
                    print(word)
                    go = Tag.objects.using('default').get(tag_name=word)
                    print("try")
                    try:
                        post_comment = PostCommentTag.objects.using('default').get(post_comment_id=comment_obj.post_comment_id, tag_id=go.tag_id)
                    except PostCommentTag.DoesNotExist:
                        PostCommentTag.objects.create(
                            post_comment_id=comment_obj.post_comment_id,
                            tag_id=go.tag_id,
                            created_on=datetime.datetime.now(),
                            modified_on=datetime.datetime.now())
                        pass
                except Tag.DoesNotExist:
                    print("else")
                    # Tag.objects.create( name=word)
                    go = Tag.objects.create(tag_name=word,
                                            created_on=datetime.datetime.now(),
                                            modified_on=datetime.datetime.now(),
                                            )

                    try:
                        post_comment = PostCommentTag.objects.using('default').get(post_comment_id=comment_obj.post_comment_id, tag_id=go.tag_id)
                    except PostCommentTag.DoesNotExist:
                        PostCommentTag.objects.create(
                            post_comment_id=comment_obj.post_comment_id,
                            tag_id=go.tag_id,
                            created_on=datetime.datetime.now(),
                            modified_on=datetime.datetime.now())
                        pass

            # adding the mentions username into the respective tables in DB.
            for username in mentioned_list:
                try:
                    userObjList = User.objects.using('default').values('user_id', 'username')
                    for go in userObjList:
                        if go['username'] == username:
                            try:
                                PostCommentMention.objects.using('default').get(post_comment_id=comment_obj.post_comment_id, user_id=go['user_id'])
                            except PostCommentMention.DoesNotExist:
                                PostCommentMention.objects.create(
                                    post_comment_id=comment_obj.post_comment_id, 
                                    user_id=go['user_id'],
                                    created_on = datetime.datetime.now(),
                                    modified_on = datetime.datetime.now(),
                                    created_by = go['user_id'],
                                    )
                except User.DoesNotExist:
                    pass
            updated_comment = comment
            comment_obj.comment = comment
            comment_obj.save()
            return UpdatePostCommentMutation(message="Successfully updated comment on post", comment=updated_comment, postCommentId=postCommentId, post_comments_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=PostComment.objects.using('default').filter(post_id=postId).count())))
        except PostComment.DoesNotExist:
            raise NotFoundException("postCommentId provided not found", 404)


"""
    Delete Post Comment
"""


# class InputDeleteCommentLikeType(graphene.InputObjectType):
#     post_comment_id = graphene.Field(BigInt)

class DeletePostCommentMutation(graphene.Mutation):
    message = graphene.String()
    postCommentId = graphene.Int()
    repliedCommentId = graphene.Int()
    post_comments_aggregate = graphene.Field(aggregateOutputObjectType)
    post_comment_replies_aggregate = graphene.Field(aggregateOutputObjectType)

    class Arguments:
        postCommentId = graphene.Argument(BigInt)

    def mutate(self, info, postCommentId):
        if postCommentId is not None:
            pass
        else:
            raise BadRequestException("invalid request; postCommentId provided is invalid", 400)

        try:
            comment = PostComment.objects.using('default').get(post_comment_id=postCommentId)
            repliedCommentId = None
            postId = comment.post_id
            # replies_comments = PostComment.objects.using('using').filter(comment_reply_id=postCommentId)
            # for each in replies_comments:

            if comment.comment_reply_id:
                repliedCommentId = comment.comment_reply_id
            else:
                repliedCommentId = None
            comment.delete()

            return DeletePostCommentMutation(message="successfully deleted comment on post", postCommentId=postCommentId, post_comments_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=PostComment.objects.using('default').filter(post_id=postId).count())), repliedCommentId=repliedCommentId, post_comment_replies_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=PostComment.objects.using('default').filter(comment_reply_id=repliedCommentId).count())))
        except PostComment.DoesNotExist:
            raise NotFoundException("postCommentId provided not found", 404)


"""
    Add Post Comment Like
"""


# class InputCommentLikeType(graphene.InputObjectType):
# post_comment_id = graphene.Field(BigInt)
# user_id = graphene.Field(BigInt)

class CommentLikeMutation(graphene.Mutation):
    message = graphene.String()
    post_comment_likes_aggregate = graphene.Field(aggregateOutputObjectType)
    user_id = graphene.Int()
    post_comment_id = graphene.Int()

    class Arguments:
        postCommentId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, postCommentId, userId):
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

        try:
            if postCommentId is not None:
                comment = PostComment.objects.using('default').get(post_comment_id=postCommentId)
                try:
                    comment_like = PostCommentLike.objects.using('default').get(user_id=userId, post_comment_id=postCommentId)
                    raise NoContentException("conflict in request; unable to like comment that is already liked", 409)
                except PostCommentLike.DoesNotExist:
                    # last_post_comment_like_id = PostCommentLike.objects.using('default').all().aggregate(Max('post_comment_like_id'))
                    # lastPostCommmentLikeId = last_post_comment_like_id['post_comment_like_id__max']+1 if last_post_comment_like_id['post_comment_like_id__max'] else 1
                    comment_like = PostCommentLike.objects.create(
                        # post_comment_like_id = lastPostCommmentLikeId,
                        user_id=userId,
                        post_comment_id=postCommentId,
                        created_on=datetime.datetime.now(),
                        modified_on=datetime.datetime.now(),
                        created_by=userId
                    )
                    comment_like.save()
                comment.save()
                number_of_likes = PostCommentLike.objects.using('default').filter(post_comment_id=postCommentId).count()
                return CommentLikeMutation(message="Successfully liked comment on post", post_comment_likes_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=number_of_likes)), user_id=userId, post_comment_id=postCommentId)
            else:
                raise BadRequestException("invalid request; postCommentId provided is invalid", 400)

        except PostComment.DoesNotExist:
            raise NotFoundException("postCommentId provided not found", 404)


"""
    Delete Post Comment Like 
"""


class CommentUnLikeMutation(graphene.Mutation):
    message = graphene.String()
    post_comment_likes_aggregate = graphene.Field(aggregateOutputObjectType)
    post_comment_id = graphene.Int()
    user_id = graphene.Int()

    class Arguments:
        postCommentId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, postCommentId, userId):
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

        try:
            if postCommentId is not None:
                comment = PostComment.objects.using('default').get(post_comment_id=postCommentId)
                try:
                    comment_like = PostCommentLike.objects.using('default').get(user_id=userId, post_comment_id=postCommentId)
                    comment_like.delete()
                except PostCommentLike.DoesNotExist:
                    raise NoContentException("conflict in request; unable to unlike comment that is already unliked", 409)
                comment.save()
                number_of_likes = PostCommentLike.objects.using('default').filter(post_comment_id=postCommentId).count()
                return CommentLikeMutation(message="Successfully unliked comment on post", post_comment_likes_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=number_of_likes)), post_comment_id=postCommentId, user_id=userId)
            else:
                raise BadRequestException("invalid request; postCommentId provided is invalid", 400)

        except PostComment.DoesNotExist:
            raise NotFoundException("postCommentId provided not found", 404)


"""
    Post view
"""


class PostViewMutation(graphene.Mutation):
    message = graphene.String()
    post_view_id = graphene.Int()
    post_id = graphene.Int()
    user_id = graphene.Int()
    views = graphene.Int()
    watchStartTime = graphene.DateTime()
    watchEndTime = graphene.DateTime()
    watchCompletions = graphene.Int()
    reWatchCount = graphene.Int()
    isImpression = graphene.Boolean()
    viewSourceId = graphene.Int()

    class Arguments:
        postId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)
        watchTime = graphene.Argument(BigInt)
        videoLength = graphene.Argument(BigInt)
        viewSourceId = graphene.Argument(BigInt)
        
    def mutate(self, info, **kwargs):
        postId = kwargs.get("postId")
        userId = kwargs.get("userId")
        watchTime = kwargs.get("watchTime")
        videoLength = kwargs.get("videoLength")
        viewSourceId = kwargs.get("viewSourceId")
        Verification.user_verify(userId)
        Verification.post_verify(postId)
        MIN_WATCH = 500

        if videoLength is not None:
            pass
        else:
            raise BadRequestException("invalid request; duration provided is invalid", 400)

        # prevents uploader from viewing more than once
        try:
            post = Post.objects.get(post_id=postId)
            if post.user_id == userId:
                postView = PostView.objects.filter(user_id=userId, post_id=postId)
                if len(postView) != 0:
                    return PostViewMutation(message = "Uploader can only view their own video once.", post_id=postId, user_id=userId)
        except PostView.DoesNotExist:
            pass


        views = 0
        watchCompletion = 0
        reWatchCount = 0
        extraView = 0
        initialView = 1
        isImpression = False
        videoStartTime = datetime.datetime.now() - datetime.timedelta(milliseconds=watchTime)
        videoEndTime = videoStartTime + datetime.timedelta(milliseconds=watchTime)
        if watchTime is not None and watchTime >= MIN_WATCH:
            if watchTime >= videoLength:
                

                remaingTime = watchTime - videoLength

                extraWatchTime = remaingTime % videoLength
                if extraWatchTime > MIN_WATCH:
                    extraView = 1
                else:
                    extraView = 0

                completeWatchTime = remaingTime - extraWatchTime
                watchCompletions = completeWatchTime / videoLength
                watchCompletion = watchCompletions + initialView
                reWatchCount = watchCompletions + extraView
                reWatchValueDecay = reWatchCount
                actualViews = reWatchCount + initialView
                if post.user_id == userId:
                    views = 1
                else:
                    views = initialView + reWatchValueDecay

            else:   
                actualViews = 1
                views = 1
                watchCompletion = 0
                reWatchCount = 0
            try:
                postView = PostView.objects.using("default").create(
                    post_id=postId,
                    user_id=userId,
                    video_start_time=videoStartTime,
                    video_end_time=videoEndTime,
                    video_duration=videoLength,
                    created_on=datetime.datetime.now(),
                    modified_on=datetime.datetime.now(),
                    created_by=userId,
                    view_source_id=viewSourceId
                )
            except PostView.DoesNotExist:
                pass

            return PostViewMutation(message="Successfully created post view", post_view_id=postView.post_view_id, post_id=postId, user_id=userId, views=views, isImpression=isImpression, watchStartTime=videoStartTime, watchEndTime=videoEndTime, reWatchCount=reWatchCount, watchCompletions=watchCompletion)
        else:
            isImpression = True
            try:
                postView = PostView.objects.using("default").create(
                    post_id=postId,
                    user_id=userId,
                    video_start_time=videoStartTime,
                    video_end_time=videoEndTime,
                    video_duration=videoLength,
                    created_on=datetime.datetime.now(),
                    modified_on=datetime.datetime.now(),
                    created_by=userId,
                    view_source_id=viewSourceId
                )
            except PostView.DoesNotExist:
                pass
            return PostViewMutation(message="Successfully created post view", post_view_id = postView.post_view_id, post_id=postId, user_id=userId, views=views, isImpression=isImpression, watchStartTime=videoStartTime, watchEndTime=videoEndTime, reWatchCount=reWatchCount, watchCompletions=watchCompletion)


"""
    adding post as not interested
"""


class PostDisInterested(graphene.Mutation):
    message = graphene.String()

    class Arguments:
        postId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        postId = kwargs.get("postId")
        userId = kwargs.get("userId")
        Verification.user_verify(userId)
        Verification.post_verify(postId)
        try:
            post_dis = PostDisinterested.objects.using("default").get(post_id=postId, user_id=userId)
            raise NoContentException("conflict in request; unable to mark post not interested as already marked as not interested", 409)
        except PostDisinterested.DoesNotExist:
            post_dis = PostDisinterested.objects.create(post_id=postId, user_id=userId, created_by=userId)
            post_dis.save()
        return PostDisInterested(message="successfully marked as not interested")


"""
    Tracking Post venue Click 
"""


class PostVenueClickMutation(graphene.Mutation):
    message = graphene.String()
    post_venue_click_id = graphene.Int()
    post_id = graphene.Int()
    user_id = graphene.Int()
    postVenueClickAggregate = graphene.Field(aggregateObjectType)

    class Arguments:
        postId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        postId = kwargs.get("postId")
        userId = kwargs.get("userId")

        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
                if not user.is_active:
                    raise ValueError("invalid request; userId provided is inactive", 400)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

        postVenue_aggregate_output_obj = []
        postVenue_objs = []

        # prevents user from clicking through their own post
        if userId == post.user_id:
            return PostVenueClickMutation(message="Auth click-through not calculated in data.", post_id=postId, user_id=userId)

        postVenueClick = PostVenueClick.objects.using("default").create(
            post_id=postId,
            user_id=userId,
            created_by=userId,
            created_on=datetime.datetime.now(),
            modified_on=datetime.datetime.now()
        )
        postVenue_objs += PostVenueClick.objects.using('default').filter(user_id=userId, post_id=postId).values_list('post_venue_click_id', flat=True)
        if postVenue_objs != []:
            for each in postVenue_objs:
                postVenue_aggregate_output_obj.append(each)
        else:
            postVenue_aggregate_output_obj = []
        return PostVenueClickMutation(message="Successfully added click-through count for post.", post_venue_click_id=postVenueClick.post_venue_click_id, post_id=postId, user_id=userId, postVenueClickAggregate=aggregateObjectType(aggregate(count=len(postVenue_aggregate_output_obj))))


class Mutation(graphene.ObjectType):
    create_post = CreatePostMutation.Field()
    update_post = EditPostMutation.Field()
    delete_post = DeletePostMutation.Field()

    add_post_like = CreateAddPostLikeMutation.Field()
    delete_post_like = UpdatePostLikeMutation.Field()

    add_post_comment = PostCommentMutation.Field()
    update_post_comment = UpdatePostCommentMutation.Field()
    delete_post_comment = DeletePostCommentMutation.Field()
    add_post_comment_like = CommentLikeMutation.Field()
    delete_post_comment_like = CommentUnLikeMutation.Field()

    add_post_save = SavePostMutation.Field()
    delete_post_save = UnSavePostMutation.Field()

    post_venue_click = PostVenueClickMutation.Field()
    post_view = PostViewMutation.Field()
    post_disinterested = PostDisInterested.Field()
