import graphene
import re
from app.utilities.errors import *
from app.models import *
from app.utilities.standardizemethods import encrypt_password
from app.utilities.errors import *
from app.utilities.sendMail import *
from app.utilities.toBigInt import BigInt
from app.utilities.uploadFileToAws import upload_to_aws
from django.db import IntegrityError
from django.conf import settings
from app.schemas.commonObjects.objectTypes import *
from django.db.models import Max, Avg
from app.schemas.commonObjects.objectTypes import *
from app.schemas.searchSchema.searchType import LocationObject,locationObject
from app.schemas.userSchema.userType import ProfileTagObjectType
from app.utilities.extractWord import extract_tags_mentions
from app.utilities import Verification
from app.schemas.searchSchema.searchType import CityObjectType, CountryObjectType, StateObjectType



"""
    Follow User 
"""
class FollowUserMutation(graphene.Mutation):
    message = graphene.String()
    followingAggregate = graphene.Field(aggregateOutputObjectType)
    authUserId = graphene.Int()
    recipientUserId = graphene.Int()
    

    class Arguments:
        authUserId = graphene.Argument(BigInt)
        recipientUserId = graphene.Argument(BigInt)
    
    def mutate(self, info, **kwargs):
        authUserId = kwargs.get('authUserId')
        recipientUserId = kwargs.get('recipientUserId')
        Verification.user_verify(authUserId)
        Verification.user_verify(recipientUserId)

        if authUserId == recipientUserId:
            raise ConflictException("conflict in request; user unable to follow themself", 409)

        if UserBlocked.objects.using('default').filter(user_id=authUserId, block_user_id=recipientUserId).exists():
            raise ConflictException("conflict in request; you have blocked the recipientUserId, you have to unblock this recipient user id", 409)

        if UserBlocked.objects.using('default').filter(user_id=recipientUserId, block_user_id=authUserId).exists():
            raise ConflictException("conflict in request; you can't follow this user as you are blocked by this recipient user ID", 409)

        # try:
        #     follower_table = UserFollower.objects.using('default').get(user_id=recipientUserId, follower_user_id=authUserId, is_followed=True)
        #     raise ConflictException("conflict in request; recipientUserId is already a follower of authUserId", 409)
        # except UserFollower.DoesNotExist:
        #     follower_table = UserFollower.objects.using('default').update_or_create(user_id=recipientUserId, follower_user_id=authUserId, created_by=authUserId, defaults={"is_followed": True, "unfollowed_date": None})

        try:
            following_table = UserFollowing.objects.using('default').get(user_id=authUserId, following_user_id=recipientUserId)
            if following_table.is_following:
                raise ConflictException("conflict in request; authUserId already follows recipientUserId", 409)
            else:
                following_table.is_following = True
                following_table.modified_by = authUserId
                following_table.modified_on = datetime.datetime.now()
                following_table.unfollowing_date = None
                following_table.save()
        except UserFollowing.DoesNotExist:
            following_table = UserFollowing.objects.using('default').update_or_create(user_id=authUserId, following_user_id=recipientUserId, created_by=authUserId, modified_on = datetime.datetime.now(), modified_by = authUserId, defaults={"is_following": True, "unfollowing_date": None})

        following_count = UserFollowing.objects.using('default').filter(user_id=authUserId, is_following=True).count()
        return FollowUserMutation(message="Successfully followed provided recipientUserId", followingAggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=following_count)), recipientUserId=recipientUserId, authUserId=authUserId)

"""
    Unfollow User
"""
class UnfollowUserMutation(graphene.Mutation):
    message = graphene.String()
    followingAggregate = graphene.Field(aggregateOutputObjectType)
    authUserId = graphene.Int()
    recipientUserId = graphene.Int()

    class Arguments:
        authUserId = graphene.Argument(BigInt)
        recipientUserId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        authUserId = kwargs.get('authUserId')
        recipientUserId = kwargs.get('recipientUserId')
        Verification.user_verify(authUserId)
        Verification.user_verify(recipientUserId)
        # try:
        #     follower_table = UserFollower.objects.using('default').get(user_id=recipientUserId, follower_user_id=authUserId, is_followed=True)
        #     follower_table.is_followed = False
        #     follower_table.unfollowed_date = datetime.datetime.now()
        #     follower_table.save()
        # except UserFollower.DoesNotExist:
        #     raise ConflictException("conflict in request; authUserId unable to remove recipientUserId that is not being followed", 409)
        try:
            following_table = UserFollowing.objects.using('default').get(user_id=authUserId, following_user_id=recipientUserId, is_following=True)
            following_table.is_following = False
            following_table.modified_on = datetime.datetime.now()
            following_table.modified_by = authUserId
            following_table.unfollowing_date = datetime.datetime.now()
            following_table.save()
        except UserFollowing.DoesNotExist:
            raise ConflictException("conflict in request; authUserId unable to remove recipientUserId that is not being followed", 409)
        following_count = UserFollowing.objects.using('default').filter(user_id=authUserId, is_following=True).count()
        return UnfollowUserMutation(message="Successfully unfollowed provided recipientUserId", followingAggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=following_count)), recipientUserId=recipientUserId, authUserId=authUserId)


"""
    Remove Follower
"""
class RemoveFollowerUserMutation(graphene.Mutation):
    message = graphene.String()
    followerAggregate = graphene.Field(aggregateOutputObjectType)
    authUserId = graphene.Int()
    recipientUserId = graphene.Int()

    class Arguments:
        authUserId = graphene.Argument(BigInt)
        recipientUserId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        authUserId = kwargs.get('authUserId')
        recipientUserId = kwargs.get('recipientUserId')
        Verification.user_verify(authUserId)
        Verification.user_verify(recipientUserId)
        # try:
        #     follower_table = UserFollower.objects.using('default').get(user_id=authUserId, follower_user_id=recipientUserId,is_followed=True)
        #     follower_table.is_followed = False
        #     follower_table.unfollowed_date = datetime.datetime.now()
        #     follower_table.save()
        # except UserFollower.DoesNotExist:
        #     raise ConflictException("conflict in request; authUserId unable to unfollow recipientUserId that is not being followed", 409)
        try:
            following_table = UserFollowing.objects.using('default').get(user_id=recipientUserId, following_user_id=authUserId, is_following=True)
            following_table.is_following = False
            following_table.modified_on = datetime.datetime.now()
            following_table.modified_by = authUserId
            following_table.unfollowing_date = datetime.datetime.now()
            following_table.save()
        except UserFollowing.DoesNotExist:
            raise ConflictException("conflict in request; authUserId unable to unfollow recipientUserId that is not being followed", 409)
        follower_count = UserFollowing.objects.using('default').filter(following_user_id=authUserId,is_following=True).count()
        return RemoveFollowerUserMutation(message="successfully removed provided recipientUserId from followers", followerAggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=follower_count)), recipientUserId=recipientUserId, authUserId=authUserId)


"""
    Upload Featured Video into User Profile
"""
class UploadFeaturedVideoMutation(graphene.Mutation):
    message = graphene.String()
    url = graphene.String()

    class Arguments():
        userId = graphene.Int()
        media = Upload()

    def mutate(self, info, **kwargs):
        uid = kwargs.get('userId')
        media = kwargs.get('media')
        Verification.user_verify(uid)
        try:
            user_profile = UserProfile.objects.using('default').get(user_id=uid)
        except UserProfile.DoesNotExist:
            userprofile = UserProfile.objects.using('default').create(user_id=uid, created_by=uid, modified_on=datetime.datetime.now(), modified_by=uid)
            userprofile.save()

        aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
        folder_name = "user-profile-media/"
        file_name = "featured_video_"+str(uid)+".mp4"
        media_link = aws_link+folder_name+file_name
        success_upload = upload_to_aws(media, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
        if success_upload:
            user_profile = UserProfile.objects.using('default').get(user_id=uid)
            # media_user = MediaUser.objects.create(media_user_id=MediaUser.objects.all().aggregate(Max('media_user_id'))+1 if MediaUser.objects.count() != 0 else: 1)
            user_profile.featured_video = media_link
            user_profile.modified_on = datetime.datetime.now()
            user_profile.save()
            print(success_upload)
            print(media_link)
            return UploadFeaturedVideoMutation(message="Successfully uploaded the video", url = media_link)
        return UploadFeaturedVideoMutation(message="Unsuccessful upload")


"""
    Edit Username in User Profile
"""

class EditUserProfileMutation(graphene.Mutation):
    message = graphene.String()
    userId = graphene.Field(BigInt)
    name = graphene.String()
    city = graphene.Field(CityObjectType)
    bio = graphene.String()
    bioLink = graphene.String()

    class Arguments:
        userId = graphene.Argument(BigInt)
        name = graphene.String()
        cityId = graphene.Int()
        bio = graphene.String()
        bioLink = graphene.String()

    def mutate(self, info, **kwargs):
        uid = kwargs.get('userId')
        name = kwargs.get('name')
        cityId = kwargs.get('cityId')
        bio = kwargs.get('bio')
        bio_link = kwargs.get('bioLink')

        user = None
        userprofile = None
        city_obj = None

        # ---------validating user ID in User and UserProfile table ------------
        if uid is not None:
            try:
                user = User.objects.using('default').get(user_id=uid)
                if not user.is_active:
                    raise BadRequestException("invalid request; userId provided is inactive")
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)

            try:
                userprofile = UserProfile.objects.using('default').get(user_id=uid)
            except UserProfile.DoesNotExist:
                userprofile = UserProfile.objects.using('default').create(user_id=uid, created_by=uid, modified_on=datetime.datetime.now(), modified_by=uid)
                userprofile.save()

        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

        # ------------editing name -------------
        if name is not None and userprofile.user_profile_name != name:
            print("name editing")
            userprofile.user_profile_name = name

        # -------------editing bio --------------
        if bio is not None and userprofile.bio != bio:
            print("bio editing")
            hashtag_list, mentioned_list = extract_tags_mentions(bio)

            # ------- BIO : adding the hashtag words into the respective tables in DB.---------
            for word in hashtag_list:
                try:
                    go = Tag.objects.using('default').get(tag_name=word)
                    try:
                        user_profile_tag = UserBioTag.objects.using('default').get(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)
                    except UserBioTag.DoesNotExist:
                        UserBioTag.objects.create(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)
                except Tag.DoesNotExist:
                    go = Tag.objects.create(tag_name=word)
                    try:
                        user_profile_tag = UserBioTag.objects.using('default').get(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)
                    except UserBioTag.DoesNotExist:
                        UserBioTag.objects.create(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)

            # -------BIO : adding the mentions' username into the respective tables in DB-----------.
            for m_username in mentioned_list:
                try:
                    user = User.objects.using('default').get(username=m_username)
                    try:
                        UserBioMention.objects.using('default').get(user_profile_id=userprofile.profile_id, user_id=user.user_id)
                    except UserBioMention.DoesNotExist:
                        UserBioMention.objects.create(user_profile_id=userprofile.profile_id, user_id=user.user_id)
                except User.DoesNotExist:
                    pass

            # --------updating the bio in user profile after changing tags and mentions ---------
            userprofile.bio = bio

        # -------- editing bio link -----------------
        if bio_link is not None and userprofile.bio_link != bio_link:
            print("bio link editing")
            userprofile.bio_link = bio_link

        # ---------- editing city --------------------
        if cityId is not None and userprofile.city_id != cityId:
            try:
                print("city editing")
                city_obj = City.objects.using('default').get(city_id=cityId)
                userprofile.city_id = city_obj.city_id

            except City.DoesNotExist():
                raise BadRequestException("invalid request; city provided is invalid", 400)

        # ---------- saving the edited user profile data -----------
        print("saving")
        userprofile.save()

        # ------------checking if city is not None for user profile and getting the new/old city id ------------
        if userprofile.city_id:
            city_obj = CityObjectType(
                city_id=userprofile.city.city_id,
                city_name=userprofile.city.city_name,
                latitude=userprofile.city.latitude,
                longitude=userprofile.city.longitude,
                state=StateObjectType(
                    state_id=userprofile.city.state_id,
                    state_name=userprofile.city.state.state_name,
                    state_code=userprofile.city.state.state_code,
                    country=CountryObjectType(
                        country_id=userprofile.city.state.country_id,
                        country_name=userprofile.city.state.country.country_name,
                        country_code_two_char=userprofile.city.state.country.country_code_two_char,
                        country_code_three_char=userprofile.city.state.country.country_code_three_char
                    )
                )
            )

        # --------------checking if name is not None for user profile and getting the new/old name --------
        if userprofile.user_profile_name:
            name = userprofile.user_profile_name

        # ----------checking if bio is not None for user profile and getting the new/old bio ---
        if userprofile.bio:
            bio = userprofile.bio

        # ------checking if bio link is not None for user profile and getting the new/old bio link -----
        if userprofile.bio_link:
            bio_link = userprofile.bio_link

        return EditUserProfileMutation(message="Successfully edited the profile provided", userId=uid, name=name, bio=bio, city=city_obj, bioLink=bio_link)

class EditUsernameMutation(graphene.Mutation):
    message = graphene.String()
    username = graphene.String()
    user_id = graphene.Int()
    class Arguments():
        userId = graphene.Argument(BigInt)
        username = graphene.String()
    def mutate(self, info, **kwargs):
        uid =kwargs.get('userId')
        username = kwargs.get('username')
        if uid is not None:
            try:
                user = User.objects.using('default').get(user_id=uid)
                if not user.is_active:
                    raise BadRequestException("invalid request; userId provided is inactive")
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
            #try:
                #userprofile = UserProfile.objects.using('default').get(user_id=uid)
            if username is not None:
                if (username and username.strip()):
                    try:
                        usr = User.objects.using('default').get(username=username)

                        if usr and usr.user_id!=uid :
                            raise ConflictException("conflict in request; username provided already used", 409)
                        user.modified_on = datetime.datetime.now()
                        user.email = str(user.email)
                        return EditUsernameMutation(message="Successfully updated username", username= username, user_id=uid)
                    except User.DoesNotExist:
                        user.username = username
                        user.modified_on = datetime.datetime.now()
                        user.email = str(user.email)
                        user.save()
                        return EditUsernameMutation(message="Successfully updated username", username= username, user_id=uid)
                else:
                    raise BadRequestException("invalid request; username provided is empty", 400)
            else:
                raise BadRequestException("invalid request; username provided is invalid", 400)
            #except UserProfile.DoesNotExist:
            #    raise NotFoundException("user profile for provided userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        

# """
#     Update User Profile
# """
# class EditUserProfileMutation(graphene.Mutation):
#     message = graphene.String()
#     userId = graphene.Field(BigInt)
#     name = graphene.String()
#     location = graphene.Field(LocationObject)
#     bio = graphene.String()
#     bioLink = graphene.String()

#     class Arguments():
#         userId = graphene.Argument(BigInt)
#         name = graphene.String()
#         location = locationObject()
#         bio = graphene.String()
#         bioLink = graphene.String()

#     def mutate(self, info, **kwargs):
#         uid = kwargs.get('userId')
#         name = kwargs.get('name')
#         # username = username
#         location = kwargs.get('location')
#         bio = kwargs.get('bio')
#         bio_link = kwargs.get('bioLink')
#         if uid is not None:
#             try:
#                 User.objects.using('default').get(user_id=uid)
#             except User.DoesNotExist:
#                 raise NotFoundException("userId provided not found", 404)
#         else:
#             raise BadRequestException("invalid request; userId provided is invalid", 400)
#         try:
#             UserProfile.objects.using('default').get(user_id=uid)
#         except UserProfile.DoesNotExist:
#             raise NotFoundException("user profile for provided userId not found", 404)
#         if name is not None:
#             pass
#         else:
#             raise BadRequestException("invalid request; name provided is invalid", 400)
        
#         if location is not None:
#             pass
#         else:
#             raise BadRequestException("invalid request; location provided is invalid", 400)

        
#         if uid is not None:
#             user = User.objects.using('default').get(user_id=uid)
#             userprofile = UserProfile.objects.using('default').get(user_id=uid)
#             # #username edited
#             # if username != user.username:
#             #     user.username = username
#             # else:
#             #     pass

#             #name edited
#             if name != userprofile.user_profile_name:
#                 userprofile.user_profile_name = name
#             else:
#                 pass

#             #bio
#             if bio is not None:
#                 #bio edited
#                 userprofile.bio = bio
#                 #extract hastags and mentions 
#                 hashtag_list, mentioned_list = extract_tags_mentions(bio)
#                 #adding the hashtag words into the respective tables in DB.
#                 for word in hashtag_list:
#                     try:
#                         go = Tag.objects.using('default').get(tag_name=word)
#                         try:
#                             user_profile_tag = UserBioTag.objects.using('default').get(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)
#                         except UserBioTag.DoesNotExist:

#                             UserBioTag.objects.create(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)
#                     except Tag.DoesNotExist:
#                         go = Tag.objects.create(tag_name=word)
#                         try:
#                             user_profile_tag = UserBioTag.objects.using('default').get(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)
#                         except UserBioTag.DoesNotExist:
#                             UserBioTag.objects.create(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)


#                 #adding the mentions username into the respective tables in DB.
#                 for m_username in mentioned_list:
#                     try:
#                         go  = User.objects.using('default').get(username=m_username)
#                         try:
#                             UserBioMention.objects.using('default').get(user_profile_id=userprofile.profile_id, user_id=go.user_id)
#                         except UserBioMention.DoesNotExist:
#                             UserBioMention.objects.create(user_profile_id=userprofile.profile_id, user_id=go.user_id)
#                     except User.DoesNotExist:
#                         pass
       
#             else:
#                 raise BadRequestException("invalid request; bio provided is invalid", 400)

#             #Bio Link
#             if bio_link is not None:
#                 userprofile.bio_link = bio_link
#             else:
#                 raise BadRequestException("invalid request; bioLink provided is invalid", 400)
            
#             #location
#             if location is not None:
#                 try:
#                     location_obj = UserProfile.objects.using('default').get(user_id=uid)
                
#                 except Location.DoesNotExist:
#                     if location == {}:
#                         location_obj = None
#                     else:
#                         location_obj = Location.objects.create(
#                             city = location.city,
#                             country = location.country,
#                             latitude = location.latitude,
#                             longitude = location.longitude,
#                             created_by = uid,
#                             created_on = datetime.datetime.now(),
#                             modified_on = datetime.datetime.now(),
#                         )
#                         location_obj.save()
#                 userprofile.location = location_obj
#             #save data 
#             user.save()
#             userprofile.save()

#             return EditUserProfileMutation(message="Successfully edited the profile provided", userId = uid, name=name, bio=bio, location=location, bioLink=bio_link)
# """
#     Edit Profile Picture 
# """
# class UploadProfilePictureMutation(graphene.Mutation):
    # def mutate():
    #     pass 

"""
    Update Profile Tags -- UserProfileTagList
"""
class AddProfileTagsMutation(graphene.Mutation):
    message = graphene.String()
    userTags = graphene.List(ProfileTagObjectType)
    user_id = graphene.Int()
    class Arguments:
        userId = graphene.Argument(BigInt)
        tags = graphene.List(BigInt)

    def mutate(self, info, **kwargs):
        uid = kwargs.get('userId')
        tags_list = kwargs.get('tags')
        Verification.user_verify(uid)
        #try:
        #    UserProfile.objects.using('default').get(user_id=uid)
        #except UserProfile.DoesNotExist:
        #    raise NotFoundException("user profile for provided userId not found", 404)  
        list_tags= []  
        if tags_list is not None:
            if len(tags_list) <= 5:
                for tag in tags_list:
                    try:
                        list_tags.append( UserProfileTag.objects.using('default').get(user_profile_tag_id=tag))
                    except UserProfileTag.DoesNotExist:
                        raise NotFoundException("tagId provided not found", 404)
            else:
                raise ConflictException("conflict in request; more than five tags are selected", 409)
        else:
            raise BadRequestException("invalid request; tags provided is invalid", 400)
        """ for i, tag in enumerate(tags_list):
            try:
                user_profile_tag_obj = UserProfileTag.objects.using('default').get(user_profile_tag_id=tag)
            except UserProfileTag.DoesNotExist:
                user_profile_tag_obj = UserProfileTag.objects.create(user_profile_tag_id=tag)
            user_profile_tag_obj.save()
            try:
                user_tag_obj = UserTag.objects.using('default').get(user_id=uid, user_profile_tag_id=user_profile_tag_obj.user_profile_tag_id)
            except UserTag.DoesNotExist:
                user_tag_list_count = UserTag.objects.using('default').filter(user_id=uid).values_list().count()
                if user_tag_list_count  >= 5:
                    user_tag_objs = UserTag.objects.using('default').filter(user_id=uid).order_by("user_tag_id").values_list("user_tag_id", flat=True)
                    user_tag_obj = UserTag.objects.using('default').get(user_tag_id = user_tag_objs[i])
                    user_tag_obj.user_profile_tag_id = user_profile_tag_obj.user_profile_tag_id
                    user_tag_obj.save()
                else:
                    user_tag_obj = UserTag.objects.create(user_id=uid, user_profile_tag_id=user_profile_tag_obj.user_profile_tag_id)  
            user_tag_obj.save() """
        
        userTags = UserTag.objects.using('default').filter(user_id=uid)
        # Deactivates all tags off of the tag list
        for tag in userTags:
            tag.is_active = tag.user_profile_tag_id in tags_list
            tag.modified_on = datetime.datetime.now()
            tag.modified_by = uid
            tag.save()
        # creates new tags as needed
        for tag in tags_list:
            try:
                UserTag.objects.using('default').get(user_id=uid, user_profile_tag_id=tag)
            except UserTag.DoesNotExist:
                obj = UserTag.objects.create(user_id=uid,user_profile_tag_id=tag,created_by=uid,modified_on=datetime.datetime.now(),modified_by=uid)
                obj.save()
                        
        return AddProfileTagsMutation(message="Successfully added profile tags", userTags=list_tags, user_id=uid)

        
"""
    Add User Profile Tags -- UserProfileTag
"""
class AddUserProfileTagMutation(graphene.Mutation):
    message = graphene.String()
    user_profile_tag_id = graphene.Int()
    name = graphene.String()

    class Arguments:
        name = graphene.String()

    def mutate(self, info, **kwargs):
        name = kwargs.get('name')
        if name:
            if name.strip():
                # last_user_profile_tag = UserProfileTag.objects.using('default').all().aggregate(Max('user_profile_tag_id'))
                # if last_user_profile_tag['user_profile_tag_id__max']:
                #     last_user_profile_tag_id = last_user_profile_tag['user_profile_tag_id__max']+1
                # else:
                #     last_user_profile_tag_id = 1
                try:

                    user_profile_tag = UserProfileTag.objects.using('default').create(
                        # user_profile_tag_id = last_user_profile_tag_id,
                        user_profile_tag_name = name
                    )
                    user_profile_tag.save()
                except IntegrityError:
                    raise NotFoundException("tag name provided already exists")

                return AddUserProfileTagMutation(message="successfully added the tag", user_profile_tag_id=user_profile_tag.user_profile_tag_id, name = name)
            else:
                raise BadRequestException("invalid request; name provided is empty")
        else:
            raise BadRequestException("invalid request; name provided is invalid")



"""
    Update Personal Info -- Email, Phone Number, Gender, Date of Birth.
"""
def validateEmail(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(re.fullmatch(regex, email)):
        pass
    else:
        raise Exception

def validatePhoneNumber(phoneNumber):
    if (re.fullmatch('[1-9][0-9]{9}', str(int(phoneNumber)))):
        pass
    else:
        raise Exception


class UpdatePersonalInfoMutation(graphene.Mutation):
    message = graphene.String()
    user_id = graphene.Int()
    email = graphene.String()
    phoneNumber = graphene.Int()
    gender = graphene.String()
    dob = graphene.Date()

    class Arguments:
        userId = graphene.Argument(BigInt)
        email = graphene.String()
        phoneNumber = graphene.Argument(BigInt)
        genderId = graphene.Int()
        dob = graphene.Date()

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        email = kwargs.get('email')
        phoneNumber = kwargs.get('phoneNumber')
        genderId = kwargs.get('genderId')
        dob = kwargs.get('dob')

        try:
            user = User.objects.using('default').get(user_id=userId)
            if not user.is_active:
                raise BadRequestException("invalid request; userId provided is inactive")
        except User.DoesNotExist:
            raise NotFoundException("userId provided not found", 404)
        if email is not None:
            try:
                validateEmail(email)
            except:
                raise BadRequestException("invalid request; email provided is invalid")
        if phoneNumber is not None:
            try:
                validatePhoneNumber(phoneNumber)
            except:
                raise BadRequestException("invalid request; phoneNumber provided is invalid")
        
        gender = None
        if email is not None or user.email is None:
            user.email = email
        if phoneNumber is not None or user.phone_number is None:
            user.phone_number = phoneNumber
        if genderId is not None:
            try:
                gender = Gender.objects.using('default').get(gender_id=genderId)
            except Gender.DoesNotExist:
                raise NotFoundException("invalid request; genderId provided is not found")
            try:
                userProfile = UserProfile.objects.using('default').get(user_id=userId)
                userProfile.gender_id = genderId
                userProfile.modified_by = userId
                userProfile.modified_on = datetime.datetime.now()
            except UserProfile.DoesNotExist:
                userProfile = UserProfile.objects.using('default').create(user_id=userId, gender_id=genderId, created_by=userId, modified_by=userId, modified_on=datetime.datetime.now())
            userProfile.save()
        if user.DOB is None or dob is not None:
            user.DOB = dob
        user.save()

        return UpdatePersonalInfoMutation(message="successfully updated provided personal info to the provided userId",user_id=userId, email=email, phoneNumber=phoneNumber, gender=gender, dob=dob)

        
        

"""
    Block User 
"""
class BlockUserMutation(graphene.Mutation):
    message= graphene.String()
    authUserId = graphene.Int()
    recipientUserId = graphene.Int()

    class Arguments:
        authUserId = graphene.Int()
        recipientUserId = graphene.Int()

    def mutate(self, info, **kwargs):
        authUserId = kwargs.get('authUserId')
        recipientUserId = kwargs.get('recipientUserId')

        Verification.user_verify(authUserId)
        Verification.user_verify(recipientUserId)

        user_blocked, is_already_blocked = UserBlocked.objects.using('default').get_or_create(
            user_id=authUserId,
            block_user_id=recipientUserId
        )

        if is_already_blocked is False:
            raise BadRequestException("recipientUserId provided is already blocked")
        else:
            following_auth_rec = UserFollowing.objects.using("default").filter(user_id=authUserId, following_user_id=recipientUserId).update(is_following=False, unfollowing_date=datetime.datetime.now())
            following_rec_auth = UserFollowing.objects.using("default").filter(user_id=recipientUserId, following_user_id=authUserId).update(is_following=False, unfollowing_date=datetime.datetime.now())
            # follower_auth_rec = UserFollower.objects.using("default").filter(user_id=authUserId, follower_user_id=recipientUserId).update(is_followed=False, unfollowed_date=datetime.datetime.now())
            # follower_rec_auth = UserFollower.objects.using("default").filter(user_id=recipientUserId, follower_user_id=authUserId).update(is_followed=False, unfollowed_date=datetime.datetime.now())

            return BlockUserMutation(message="successfully blocked the provided recipientUserId", authUserId=authUserId, recipientUserId=recipientUserId)


"""
    Remove Blocked User
"""
class RemoveBlockUserMutation(graphene.Mutation):
    message = graphene.String()
    authUserId = graphene.Int()
    recipientUserId = graphene.Int()

    class Arguments:
        authUserId = graphene.Int()
        recipientUserId = graphene.Int()

    def mutate(self, info, **kwargs):
        authUserId = kwargs.get('authUserId')
        blockUserId = kwargs.get('recipientUserId')

        Verification.user_verify(authUserId)
        Verification.user_verify(blockUserId)
        try:
            removeBlock = UserBlocked.objects.using('default').get(user_id=authUserId, block_user_id=blockUserId)
            removeBlock.delete()
            return RemoveBlockUserMutation(message="successfully removed blocked user provided", authUserId=authUserId, recipientUserId=blockUserId)
        except UserBlocked.DoesNotExist:
            raise ConflictException("conflict in request; recipientUserId provided is not blocked")



class Mutation(graphene.ObjectType):

    # update_user = UpdateUserMutation.Field()

    add_user_follow = FollowUserMutation.Field()
    delete_user_follow = UnfollowUserMutation.Field()
    remove_follower = RemoveFollowerUserMutation.Field()

    upload_featured_video = UploadFeaturedVideoMutation.Field()
    # upload_profile_picture = UploadProfilePictureMutation.Field()

    update_user = EditUserProfileMutation.Field()
    # edit_profile_tags = EditUserProfileTagsMutation.Field()
    update_user_tags = AddProfileTagsMutation.Field()
    update_username = EditUsernameMutation.Field()
    
    add_user_profile_tag = AddUserProfileTagMutation.Field()
    
    update_user_personal_info = UpdatePersonalInfoMutation.Field()

    block_user = BlockUserMutation.Field()
    remove_blocked_user = RemoveBlockUserMutation.Field()