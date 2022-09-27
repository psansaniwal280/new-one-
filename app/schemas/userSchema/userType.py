import graphene
from graphene_django import DjangoObjectType
from app.models import *
from app.utilities.toBigInt import BigInt
from app.schemas.commonObjects.objectTypes import *
from app.utilities.extractWord import extract_tags_mentions
from app.utilities.errors import *
from app.schemas.commonObjects.objectTypes import PageInfoObject

class UserListType(graphene.ObjectType):
    user_id= graphene.Int()   


class ProfileTagObjectType(DjangoObjectType):
    class Meta:
        model = UserProfileTag
    user_tag_id = graphene.Int()
    name = graphene.String()
    def resolve_user_tag_id(self, info):
        return self.user_profile_tag_id
    def resolve_name(self, info):
        return self.user_profile_tag_name

class UserProfileType(DjangoObjectType):
    class Meta:
        model = UserProfile
    profile_id = graphene.Field(BigInt)
    user_id = graphene.Field(BigInt)
    bio = graphene.String()
    city = graphene.String()
    featured_video = graphene.String()
    bio_link = graphene.Field(BigInt)

class UserType(DjangoObjectType):
    class Meta:
        model = User
    user_id = graphene.Int()
    username = graphene.String()
    avatar = graphene.String()
    level = graphene.Int()
    phone_number = graphene.Field(BigInt)
    
class UserPersonalInfoObjectType(graphene.ObjectType):
    email = graphene.String()
    username = graphene.String()
    phone_number = graphene.Field(BigInt)
    gender = graphene.String()
    dob = graphene.Date()   



class UserMainProfile(graphene.ObjectType):
    # class Meta:
    #     model = UserProfile
    user_id = graphene.Int()
    username = graphene.String()
    profile_name = graphene.String()
    avatar = graphene.String()
    level = graphene.Int()
    city = graphene.String()
    country = graphene.String()
    bio = graphene.Field(bioSection)
    featured_video = graphene.String()
    bio_link = graphene.String()
    # follower = graphene.Field(BigInt)
    # following = graphene.Field(BigInt)
    # trips_booked = graphene.Field(BigInt)
    tags = graphene.List(ProfileTagObjectType)
    isFollowing = graphene.Boolean()
    isBlocked = graphene.Boolean()
    isFollowedBy = graphene.Boolean()

    def resolve_username(self, info):
        user = User.objects.using('default').get(user_id=self.user_id) 
        print(user.username)                    
        return user.username
    def resolve_profile_name(self, info):
        try:
            userProfile = UserProfile.objects.using('default').get(user_id=self.user_id)
            return userProfile.user_profile_name   
        except UserProfile.DoesNotExist:
            return None
    def resolve_level(self, info):
        user = User.objects.using('default').get(user_id=self.user_id)
        return user.level 
    def resolve_avatar(self, info):
        user = User.objects.using('default').get(user_id=self.user_id)
        return user.avatar 
    def resolve_city(self, info):
        try:
            location_obj = UserProfile.objects.using('default').get(user_id=self.user_id)
            city = City.objects.using('default').get(city_id=location_obj.city_id)
            return city.city_name
        except City.DoesNotExist:
            return None
        except UserProfile.DoesNotExist:
            return None
        
    def resolve_country(self, info):
        try:
            location_obj = UserProfile.objects.using('default').get(user_id=self.user_id)
            city = City.objects.using('default').get(city_id=location_obj.city_id)
            state = States.objects.using('default').get(state_id=city.state_id)
            country = Country.objects.using('default').get(country_id=state.country_id)

            return country.country_name

        except City.DoesNotExist:
            return None
        except UserProfile.DoesNotExist:
            return None
    def resolve_bio(self, info):
        try:
            bio_content = UserProfile.objects.using('default').get(user_id=self.user_id).bio
            hashtag_words, hashtags = [], []
            mention_words, mentions = [], []
            hashtag_words, mention_words = extract_tags_mentions(bio_content)
            if hashtag_words == []:
                hashtags = []
            for one_hashtag in hashtag_words:
                try:
                    tag_obj = Tag.objects.using('default').get(tag_name=one_hashtag)
                    hashtags.append(hashtagSection(tag_obj.tag_name, tag_obj.tag_id))
                except Tag.DoesNotExist:
                    tag_obj = Tag.objects.create(name=one_hashtag)   
                    hashtags.append(hashtagSection(tag_obj.tag_name, tag_obj.tag_id))  
            
            if mention_words == []:
                mentions = []
            for one_mention in mention_words:
                try:
                    user = User.objects.using('default').get(username=one_mention)            
                    mentions.append(mentionSection(user.username, user.user_id))
                except User.DoesNotExist:
                    mentions.append(mentionSection(one_mention, None))
            return bioSection(bio_content, hashtags, mentions)
        except UserProfile.DoesNotExist:
            return bioSection(None, None, None)
        
    # def resolve_follower(self, info):
    #     return UserFollowing.objects.using('default').filter(following_user_id=self.user_id).count()
    # def resolve_following(self, info):
    #     return UserFollowing.objects.using('default').filter(user_id=self.user_id).count()
    # def resolve_trips_booked(self, info):
    #     return UserTrip.objects.using('default').filter(user_id=self.user_id).count()
    def resolve_tags(self, info):
        try:
            tags_ids = UserTag.objects.using('default').filter(user_id=self.user_id, is_active=True).values_list("user_profile_tag_id",flat=True)
            if len(tags_ids) <= 5:
                return list(UserProfileTag.objects.using('default').filter(user_profile_tag_id__in=tags_ids))
            else:
                tagsInOrder = []
                tagsToReturn = []
                for tag in UserTag.objects.using('default').filter(user_id=self.user_id, is_active=True):
                    if len(tagsInOrder) == 0:
                        tagsInOrder.append(tag)
                    # failsafe for tags being too big
                    else:
                        inserted = False
                        for i in range(len(tagsInOrder)):
                            if (tagsInOrder[i].created_on < tag.created_on):
                                tagsInOrder.insert(i, tag)
                                inserted = True
                                break
                        if not inserted:
                            tagsInOrder.append(tag)
                for i in range(5):  
                    tagsToReturn.append(UserProfileTag.objects.using('default').get(user_profile_tag_id=tagsInOrder[i].user_profile_tag_id))
                return tagsToReturn
        except UserTag.DoesNotExist:
            return []
    
    # def isFollowing(self, info):


class UserReasonDetailObjectType(graphene.ObjectType):
    reason = graphene.String()
    description = graphene.String()
    report_user_reason_id = graphene.Int()    

class BlockedUsersListType(graphene.ObjectType):
    user_id = graphene.Int()

class userObject(graphene.ObjectType):
    is_following = graphene.Boolean()
    is_followedBy = graphene.Boolean()
    user_id = graphene.Int()
    # username = graphene.String()
    # name = graphene.String()
    # avatar = graphene.String()
    # level = graphene.Int()

    # def resolve_username(self, info):
    #     user = User.objects.using('default').get(user_id=self.user_id)
    #     return user.username
    # def resolve_level(self, info):
    #     user = User.objects.using('default').get(user_id=self.user_id)
    #     return user.level 
    # def resolve_avatar(self, info):
    #     user = User.objects.using('default').get(user_id=self.user_id)
    #     return user.avatar

class userPageObjectType(graphene.ObjectType):
    users = graphene.List(userObject)
    page_info = graphene.Field(PageInfoObject)


"""
    Profile Tag Object
"""
class profileTagObject(graphene.ObjectType):
    profileTagId = graphene.Int()
    name = graphene.String()


class inputProfileTagObject(graphene.InputObjectType):
    profileTagIdList = graphene.List(BigInt)

"""
    Get list of profile tags
"""
def getProfileTagsList(userId):
    tags_list = []
    if userId is not None:
        try:
            User.objects.using('default').get(user_id=userId)
            try:
                user_tag_objs = UserTag.objects.using('default').filter(user_id=userId)
            except UserTag.DoesNotExist:
                raise ConflictException("conflict in request; provided userId has no user profile tag found", 409)
        except User.DoesNotExist:
            raise NotFoundException("userId provided not found", 404)
    for each in user_tag_objs:
        try:
            tag = UserProfileTag.objects.using('default').get(user_profile_tag_id=each.user_profile_tag_id)
            tags_list.append(profileTagObject(tag.user_profile_tag_id, tag.user_profile_tag_name))
        except UserProfileTag.DoesNotExist:
            raise NotFoundException("userProfileTagId provided not found", 404)
    return tags_list


class UserRecommendedListType(graphene.ObjectType):
    user_id = graphene.Int()
    relevancy_score = graphene.Float()
    
class UserRecommendedPageListType(graphene.ObjectType):
    users = graphene.List(UserRecommendedListType)
    page_info = graphene.Field(PageInfoObject)