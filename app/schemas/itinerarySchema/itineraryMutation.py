import graphene
from graphene_file_upload.scalars import Upload
from app.models import *
from app.utilities.errors import *
from app.utilities.extractWord import extract_tags_mentions
from app.utilities.uploadFileToAws import upload_to_aws
import datetime
from django.conf import settings
from django.db.models import Max
from app.utilities import Verification
from app.utilities.toBigInt import BigInt


"""
    Add - Itinerary 
"""

class CreateItineraryMutation(graphene.Mutation):
    user_shared_itinerary_id = graphene.Int()

    class Arguments:
        userId = graphene.Int()
        title = graphene.String()
        thumbnail = Upload()
        postIds = graphene.List(graphene.Int)
        tags = graphene.List(graphene.String)
        description = graphene.String()
        
    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        name = kwargs.get('title')
        thumbnail = kwargs.get('thumbnail')
        postIds = kwargs.get('postIds')
        tags = kwargs.get('tags')
        description = kwargs.get('description')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if name is not None:
            if name and name.strip():
                pass
            else:
                raise BadRequestException("invalid request; title provided is empty")
        else:
            raise BadRequestException("invalid request; title provided is invalid")
        if postIds is not None:
            if postIds == []:
                raise BadRequestException("invalid request; postIds provided is empty")
            else:
                postObjs = []
                for each in postIds:
                    try:
                        postObj = Post.objects.using('default').get(post_id=each)
                        postObjs.append(postObj)
                    except Post.DoesNotExist:
                        raise NotFoundException("postId "+str(each)+" provided is not found")
        else:
            raise BadRequestException("invalid request; postIds provided is invalid")
        if tags is not None:
            # if tags == []:
            #     raise BadRequestException("invalid request; tags provided is empty")
            # else:
            tagObjs = []
            for eachtag in tags:
                try:
                    
                    tagObj = Tag.objects.using('default').get(tag_name = eachtag)
                except Tag.DoesNotExist:
                    last_tag = Tag.objects.using('default').all().aggregate(Max('tag_id'))
                    tagId = last_tag['tag_id__max']+1 if last_tag['tag_id__max'] else 1
                    tagObj = Tag.objects.using('default').create(
                        tag_name = eachtag
                    )
                    tagObj.save()
                tagObjs.append(tagObj)
        else:
            raise BadRequestException("invalid request; tags provided is invalid")
        if description is not None:
            pass 
        else:
            raise BadRequestException("invalid request; description provided is invalid")

        #Insert into UserSharedItinerary
        last_user_shared_itinerary = UserSharedItinerary.objects.using('default').all().aggregate(Max('user_shared_itinerary_id'))
        userSharedItineraryId = last_user_shared_itinerary['user_shared_itinerary_id__max']+1 if last_user_shared_itinerary['user_shared_itinerary_id__max'] else 1

        #upload the thumbnail into the S3 bucket
        print(thumbnail)
        aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
        thumbnail_folder_name = "itinerary_media/"
        thumbnail_file_name = "itinerary_thumbnail_"+str(userSharedItineraryId)+".jpg"
        thumbnail_media_link = aws_link+thumbnail_folder_name+thumbnail_file_name
        thumbnail_success_upload = upload_to_aws(thumbnail, settings.AWS_STORAGE_BUCKET_NAME, thumbnail_folder_name, thumbnail_file_name)
        print(thumbnail_success_upload)
        print(thumbnail_media_link)


        user_shared_itinerary = UserSharedItinerary.objects.using('default').create(
            user_id = user.user_id,
            user_shared_itinerary_name = name,
            thumbnail = thumbnail_media_link,
            user_shared_itinerary_description = description,
            created_on =  datetime.datetime.now(),
            modified_on =  datetime.datetime.now(),
            created_by = user.user_id,
        )
        user_shared_itinerary.save()

        #extracting the hashtags word and mentioned usernames separatly
        hashtag_list, mentioned_list = extract_tags_mentions(description)
        print(mentioned_list)
        #adding the hashtag words into the respective tables in DB.
        for word in hashtag_list:
            try:
                go = Tag.objects.using('default').get(tag_name=word)
                try:
                    UserSharedItineraryTag.objects.using('default').get(user_shared_itinerary_id=userSharedItineraryId, tag_id=go.tag_id)
                except UserSharedItineraryTag.DoesNotExist:
                    # last_user_shared_itinerary_tag = UserSharedItineraryTag.objects.using('default').all().aggregate(Max('user_shared_itinerary_tag_id'))
                    # userSharedItineraryTagId = last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max']+1 if last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max'] else 1
                    UserSharedItineraryTag.objects.using('default').create(user_shared_itinerary_id=userSharedItineraryId, tag_id=go.tag_id)
            except Tag.DoesNotExist:
                go = Tag.objects.create( 
                    tag_name=word,   
                    created_on = datetime.datetime.now(),
                    modeified_on = datetime.datetime.now(),
                    created_by=userId)
                try:
                    UserSharedItineraryTag.objects.using('default').get(user_shared_itinerary_id=userSharedItineraryId, tag_id=go.tag_id)
                except UserSharedItineraryTag.DoesNotExist:
                    # last_user_shared_itinerary_tag = UserSharedItineraryTag.objects.using('default').all().aggregate(Max('user_shared_itinerary_tag_id'))
                    # userSharedItineraryTagId = last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max']+1 if last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max'] else 1
                    UserSharedItineraryTag.objects.using('default').create(user_shared_itinerary_id=userSharedItineraryId, tag_id=go.tag_id)

        # #adding the mentions username into the respective tables in DB.
        for username in mentioned_list:
            print(username)
            try:
                user = User.objects.using('default').get(username=username)    
                UserSharedItineraryMention.objects.using('default').create(user_shared_itinerary_id=userSharedItineraryId, user_id=user.user_id)
            except User.DoesNotExist:
                pass 
        #Separate Tags fields
        if tagObjs != []:
            for eachTagObj in tagObjs:
                # last_user_shared_itinerary_tag = UserSharedItineraryTag.objects.using('default').all().aggregate(Max('user_shared_itinerary_tag_id'))
                # userSharedItineraryTagId = last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max']+1 if last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max'] else 1
                user_shared_itinerary_tag = UserSharedItineraryTag.objects.using('default').create(
                    # user_shared_itinerary_tag_id = userSharedItineraryTagId,
                    user_shared_itinerary_id = userSharedItineraryId,
                    tag_id = eachTagObj.tag_id
                )
                user_shared_itinerary_tag.save()
        else:
            pass
        
        if postObjs !=[]:
            for eachPostObj in postObjs:
                # last_user_shared_itinerary_post = UserSharedItineraryPost.objects.using('default').all().aggregate(Max('user_shared_itinerary_post_id'))
                # userSharedItineraryPostId = last_user_shared_itinerary_post['user_shared_itinerary_post_id__max']+1 if last_user_shared_itinerary_post['user_shared_itinerary_post_id__max'] else 1
                user_shared_itinerary_post = UserSharedItineraryPost.objects.using('default').create(
                    # user_shared_itinerary_post_id = userSharedItineraryPostId,
                    user_shared_itinerary_id = userSharedItineraryId,
                    post_id = eachPostObj.post_id
                )
                user_shared_itinerary_post.save()
        else:
            raise NotFoundException("no posts found for provided postIds")

        return CreateItineraryMutation(user_shared_itinerary_id=userSharedItineraryId)


class DeleteItineraryMutation(graphene.Mutation):
    message = graphene.String()
    user_shared_itinerary_id = graphene.Int()
    user_id = graphene.Int()

    class Arguments():
        userSharedItineraryId = graphene.Argument(BigInt)
        userId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        userSharedItineraryId = kwargs.get('userSharedItineraryId')
        userId = kwargs.get('userId')
        Verification.user_verify(userId)

        if userSharedItineraryId is not None:
            try:
                itinerary = UserSharedItinerary.objects.using('default').get(user_shared_itinerary_id=userSharedItineraryId)

                if itinerary.user_id == userId:
                    itinerary.delete()
                    return DeleteItineraryMutation(message="Successfully deleted the itinerary", user_shared_itinerary_id=userSharedItineraryId, user_id=userId)
                else:
                    raise AuthorizationException("userId provided is not authorized to delete this itinerary", 401)
            except UserSharedItinerary.DoesNotExist:
                raise NotFoundException("userSharedItineraryId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userSharedItineraryId provided is invalid", 400)

class Mutation(graphene.ObjectType):
    create_itinerary = CreateItineraryMutation.Field()
    delete_itinerary = DeleteItineraryMutation.Field()