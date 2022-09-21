import graphene
from .userType import *
from app.schemas.commonObjects.objectTypes import aggregateObjectType
from app.utilities.errors import *
import math
from django.db.models import Q

from ...utilities import Verification, CommonOperations
from ...utilities.pagination import pagination


class Query(graphene.ObjectType):

     #User Profile Tags
    allUserTags = graphene.List(ProfileTagObjectType)

    user = graphene.Field(UserMainProfile, recipientUserId=graphene.Int(), authUserId=graphene.Int())

    usersFollowingAggregate = graphene.Field(aggregateObjectType, authUserId = graphene.Int())

    userFollowersAggregate = graphene.Field(aggregateObjectType, authUserId = graphene.Int())

    tripsBookedAggregate = graphene.Field(aggregateObjectType, userId = graphene.Int())

    userPersonalInfo = graphene.Field(UserPersonalInfoObjectType, userId= graphene.Int())

    #User Followed & Following Queries
    usersFollowing = graphene.Field(userPageObjectType, authUserId= graphene.Int(), recipientUserId =  graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    userFollowers = graphene.Field(userPageObjectType, authUserId= graphene.Int(), recipientUserId = graphene.Int(), page=graphene.Int(), limit=graphene.Int())
            
    usersFollowingResults = graphene.Field(userPageObjectType, userId=graphene.Int(), searchContent = graphene.String(), page=graphene.Int(), limit=graphene.Int())
    userFollowersResults = graphene.Field(userPageObjectType, userId=graphene.Int(), searchContent = graphene.String(), page=graphene.Int(), limit=graphene.Int())

    #Get Blocked User List by User Id
    blockedUsers = graphene.List(BlockedUsersListType, userId = graphene.Int())

    #For user follow recommendations
    userFollowRecommendations = graphene.Field(UserRecommendedPageListType, userId = graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    #For user recommendations
    userRecommendations = graphene.Field(UserRecommendedPageListType, userId = graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    
    #Get All User Tags
    def resolve_allUserTags(parent, info):
        return UserProfileTag.objects.all().order_by('user_profile_tag_name')

     #Get User By userId 
    def resolve_user(parent, info, **kwargs):
        authUserId = kwargs.get('authUserId')
        recipientUserId = kwargs.get('recipientUserId')

        Verification.user_verify(authUserId)
        #Verification.user_profile(authUserId)
        Verification.user_verify(recipientUserId)
        #Verification.user_profile(recipientUserId)

        try:
            result = UserProfile.objects.using('default').get(user_id=recipientUserId)
        except UserProfile.DoesNotExist:
            result = UserMainProfile(user_id=recipientUserId)            

        userFollowing = CommonOperations.default_get_or_none(UserFollowing, user_id=authUserId, following_user_id=recipientUserId)
        result.isFollowing = True if userFollowing is not None and userFollowing.is_following else False

        userBlocked = CommonOperations.default_get_or_none(UserBlocked, user_id=authUserId, block_user_id=recipientUserId)
        result.isBlocked = True if userBlocked is not None else False

        userFollower = CommonOperations.default_get_or_none(UserFollowing, user_id=recipientUserId, following_user_id=authUserId)
        result.isFollowedBy = True if userFollower is not None and userFollower.is_following else False

        return result

 #Get Following Aggregate
    def resolve_usersFollowingAggregate(parent, info, **kwargs):
        userId = kwargs.get('authUserId')
        Verification.user_verify(userId)
        #Verification.user_profile(userId)
        return aggregateObjectType(aggregate(count=UserFollowing.objects.using('default').filter(user_id=userId, is_following=True).count()))

 #Get Follower Aggregate
    def resolve_userFollowersAggregate(parent, info, **kwargs):
        userId = kwargs.get('authUserId')
        Verification.user_verify(userId)
        #Verification.user_profile(userId)
        return aggregateObjectType(aggregate(count=UserFollowing.objects.using('default').filter(following_user_id=userId, is_following=True).count()))

#Get Trips Booked Aggregate
    def resolve_tripsBookedAggregate(parent, info, **kwargs):
        userId = kwargs.get('userId')
        Verification.user_verify(userId)
        return aggregateObjectType(aggregate(count=UserTrip.objects.using('default').filter(user_id=userId).count()))


# Get User Personal Info
    def resolve_userPersonalInfo(self, info, **kwargs):
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
                if user.is_active:
                    try:
                        userProfile = UserProfile.objects.using('default').get(user_id=userId)
                        gender = Gender.objects.using('default').get(gender_id=userProfile.gender_id)
                    except UserProfile.DoesNotExist:
                        gender = None
                    return UserPersonalInfoObjectType(email=user.email, username=user.username, phone_number=user.phone_number, gender=(gender.gender_name if not (gender is None) else None), dob=user.DOB)
                else:
                    raise BadRequestException("invalid request; userId provided is inactive", 400)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")

    # --Get Following Users
    def resolve_usersFollowing(parent, info, **kwargs):
        authId = kwargs.get("authUserId")
        uid = kwargs.get("recipientUserId")
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        Verification.user_verify(authId)
        Verification.user_verify(uid)
        following_user_ids = UserFollowing.objects.using('default').filter(user_id=uid, is_following=True).values_list('following_user_id', flat=True)
        following_user_objs = []
        for each in list(following_user_ids):
            try:
                user = User.objects.get(user_id=each)
                if not user.is_active:
                    continue
            except User.DoesNotExist:
                continue
            #Verification.user_profile(each)
            try:
                UserFollowing.objects.using('default').get(user_id=uid, following_user_id=each, is_following=True)    
                following_user_objs.append(userObject(user_id= each))  # , user.username, userprofile.name, user.avatar, user.level))
             
            except UserFollowing.DoesNotExist:
                # following_user_objs.append(userObject(False, each))  # , user.username, userprofile.name, user.avatar, user.level))
                pass
        
        if authId in following_user_ids:
            following_user_objs.insert(0,userObject(user_id= authId))

        seen = set()
        outputObject=[seen.add(obj.user_id) or obj for obj in following_user_objs if obj.user_id not in seen]
        result = outputObject

        flag, result = pagination(result, page, limit)
        if flag:
            return userPageObjectType(users=result['result'], page_info=PageInfoObject(nextPage=result['page'], limit=result['limit']))
        else:
            raise BadRequestException(result)

    # Get Follower Users
    def resolve_userFollowers(parent, info, **kwargs):
        authId = kwargs.get("authUserId")
        uid = kwargs.get("recipientUserId")
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        Verification.user_verify(authId)
        Verification.user_verify(uid)
        follower_user_ids = UserFollowing.objects.using('default').filter(following_user_id=uid, is_following=True).values_list('user_id', flat=True)
        follower_user_objs = []
        for each in list(follower_user_ids):
            try:
                user = User.objects.get(user_id=each)
                if not user.is_active:
                    continue
            except User.DoesNotExist:
                continue
            #Verification.user_profile(each)
            try:
                UserFollowing.objects.using('default').get(user_id=each, following_user_id=uid, is_following=True)
                follower_user_objs.append(userObject(user_id= each))  # , user.username, userprofile.name, user.avatar, user.level))
            except UserFollowing.DoesNotExist:
                # follower_user_objs.append(userObject(False, each))  # , user.username, userprofile.name, user.avatar, user.level))
                pass


        if authId in follower_user_ids:
            follower_user_objs.insert(0,userObject(user_id= authId))
            
        seen = set()
        outputObject=[seen.add(obj.user_id) or obj for obj in follower_user_objs if obj.user_id not in seen]
        result = outputObject

        flag, result = pagination(result, page, limit)
        if flag:
            return userPageObjectType(users=result['result'], page_info=PageInfoObject(nextPage=result['page'], limit=result['limit']))
        else:
            raise BadRequestException(result)

    # Search Following User
    def resolve_usersFollowingResults(parent, info, **kwagrs):
        uid = kwagrs.get("userId")
        search_content = kwagrs.get("searchContent")
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        Verification.user_verify(uid)
        if search_content is not None :
            if (search_content and search_content.strip()):
                # client = redis_connect()
                # search_history_cache = get_hashmap_from_cache(client, str(uid)+"_search_history")
                # search_history_cache.put(search_content, datetime.datetime.now())
                # print(search_history_cache.getAll())
                # state = set_hashmap_to_cache(client, str(uid)+ "_search_history", search_history_cache)
                # print(state)
                pass
            else:
                raise BadRequestException("invalid request; searchContent provided is empty", 400)
        else:
            raise BadRequestException("invalid request; searchContent provided is invalid", 400)
        
        
        following_user_ids =[]
        following_user_ids += UserFollowing.objects.using('default').filter(user_id=uid).values_list('following_user_id')
        for a in range(len(following_user_ids)):
            following_user_ids[a] = following_user_ids[a][0]
        username_objs = []
        obj_list = []
        username_objs += User.objects.using('default').filter(Q(username__icontains=search_content) & Q(user_id__in=following_user_ids)).values_list('user_id')
        for a in range(len(username_objs)):
            username_objs[a] = username_objs[a][0]
        obj_list = UserProfile.objects.using('default').filter(Q(user_id__in = username_objs) | (Q(user_profile_name__icontains=search_content)& Q(user_id__in=following_user_ids))).values_list('user_id')
        following_user_objs = []
        for each in obj_list:
            # following_user_objs.append(User.objects.using('default').get(user_id=each))   
            # try:
            #     UserFollowing.objects.using('default').get(Q(following_user_id=uid) & Q(user_id=each))
            #userprofile = UserProfile.objects.using('default').get(user_id=each[0])
            user = User.objects.using('default').get(user_id=each[0])
            following_user_objs.append(userObject(True, True, user.user_id))
        # return following_user_objs 
        result = following_user_objs
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return userPageObjectType(users=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return userPageObjectType(users=result,  page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return userPageObjectType(users=[],  page_info=PageInfoObject(nextPage= None, limit=None))
        
 #Search Follower User
    def resolve_userFollowersResults(parent, info, **kwagrs):
        uid = kwagrs.get("userId")
        search_content = kwagrs.get("searchContent")
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        Verification.user_verify(uid)
        if search_content is not None :
            if (search_content and search_content.strip()):
                # client = redis_connect()
                # search_history_cache = get_hashmap_from_cache(client, str(uid)+"_search_history")
                # search_history_cache.put(search_content, datetime.datetime.now())
                # print(search_history_cache.getAll())
                # state = set_hashmap_to_cache(client, str(uid)+ "_search_history", search_history_cache)
                # print(state)
                pass
            else:
                raise BadRequestException("invalid request; searchContent provided is empty", 400)
        else:
            raise BadRequestException("invalid request; searchContent provided is invalid", 400)

        follower_user_ids =[]
        follower_user_ids += UserFollowing.objects.using('default').filter(user_id=uid).values_list('following_user_id')
        for a in range(len(follower_user_ids)):
            follower_user_ids[a] = follower_user_ids[a][0]
        username_objs = []
        obj_list = []
        username_objs += User.objects.using('default').filter(Q(username__icontains=search_content) & Q(user_id__in=follower_user_ids)).values_list('user_id')
        for a in range(len(username_objs)):
            username_objs[a] = username_objs[a][0]
        obj_list = UserProfile.objects.using('default').filter(Q(user_id__in = username_objs) | (Q(user_profile_name__icontains=search_content)& Q(user_id__in=follower_user_ids)))
        result = []
        for one in obj_list:
            try:
               
                UserFollowing.objects.using('default').get(user_id=uid, following_user_id=one.user_id)
                #userprofile = UserProfile.objects.using('default').get(user_id=one.user_id)
                user = User.objects.using('default').get(user_id=one.user_id)
                result.append(userObject(True, True, user.user_id))
            except UserFollowing.DoesNotExist:
                #userprofile = UserProfile.objects.using('default').get(user_id=one.user_id)
                user = User.objects.using('default').get(user_id=one.user_id)
                result.append(userObject(False, False, user.user_id))
                print("Herrrr except",userprofile.user_id)

        # return result 
        # result = follower_user_objs
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return userPageObjectType(users=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return userPageObjectType(users=result,  page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return userPageObjectType(users=[],  page_info=PageInfoObject(nextPage= None, limit=None))



 #Get User Tags
    def resolve_getUserTags(parent, info, **kwagrs):
        uid = kwagrs.get('userId')
        Verification.user_verify(uid)
        try:
            UserProfile.objects.using('default').get(user_id=uid)
        except UserProfile.DoesNotExist:
            raise NotFoundException("user profile for provided userId not found", 404)    
        return getProfileTagsList(uid)

    # -----Get Blocked User List by User Id
    def resolve_blockedUsers(self, info, **kwargs):
        userId = kwargs.get('userId')
        Verification.user_verify(userId)
        blockedList = UserBlocked.objects.using('default').filter(user_id=userId).values_list('block_user_id', flat=True)
        if len(blockedList) > 0:
            return [{'user_id': each} for each in blockedList]
        else:
            return []

    # Get the list of user follow recommondations as follow suggestions with relevancy score    
    def resolve_userFollowRecommendations(parent,info,**kwargs):
        authUserId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        Verification.user_verify(authUserId)
        
        # Find the users with mutual following 
        
        following =[]
        following += UserFollowing.objects.using('default').filter(user_id = authUserId).values_list('following_user',flat=True)
        mutual =[]
        for each in following:
            follower =[]
            follower += UserFollowing.objects.using('default').filter(user_id = each).values_list('following_user',flat=True)
            mutual += follower
        mutual = list(set(mutual))
        if authUserId in mutual:
            mutual.remove(authUserId)
        
        
        # Check if Search_user messeged by Current_user    
        
        msg_recipient = []
        msg_recipient += ChatMessage.objects.using('default').filter(sender = authUserId).values_list('chatmessagerecipient__user_id',flat = True)
        msg_recipient1 = list(set(msg_recipient))
        total_msgs = {}
        for each in msg_recipient1:
            total_msgs[each] = msg_recipient.count(each)
        
        
        # find the all user on whose post user commented
        post_comment = []
        post_comment += PostComment.objects.filter(user_id=authUserId).values_list('post__user_id',flat=True)
        post_comment1 = list(set(post_comment))
        if authUserId in post_comment1:
            post_comment1.remove(authUserId)
        total_comments = {}
        for each in post_comment1:
            total_comments[each] = post_comment.count(each)
        
        # find the all user whose post user saved
        post_saved = []
        post_saved += PostSaved.objects.filter(user_id=authUserId).values_list('post__user_id',flat=True)
        post_saved1 = list(set(post_saved))
        if authUserId in post_saved1:
            post_saved1.remove(authUserId)
        total_saved = {}
        for each in post_saved1:
            total_saved[each] = post_saved.count(each)
        
        # find the all user whose post user liked
        post_liked = []
        post_liked += PostLike.objects.filter(user_id=authUserId).values_list('post__user_id',flat=True)
        post_liked1 = list(set(post_liked))
        if authUserId in post_liked1:
            post_liked1.remove(authUserId)
        total_liked = {}
        for each in post_liked1:
            total_liked[each] = post_liked.count(each)
        
        # Find all the users that live in the same city as authUserId
        city_uid = UserProfile.objects.filter(user_id = authUserId).values('city_id')
        try:
            same_city_users =[]
            same_city_users += UserProfile.objects.filter(city_id = city_uid[0]['city_id']).values_list('user_id', flat=True)
            if authUserId in same_city_users:
                same_city_users.remove(authUserId)
        except:
            pass
        
        #check for the user_tag
        total_tags = {}
        tag_uid = []
        tag_uid += UserTag.objects.filter(user_id = authUserId).values_list('user_profile_tag',flat=True)
        same_tag_users = []
        for each in tag_uid:
            same_tag_users += UserTag.objects.filter(user_profile_tag = each).values_list('user_id',flat=True)
        same_tag_users1 = list(set(same_tag_users))
        if authUserId in same_tag_users1:
            same_tag_users1.remove(authUserId)
        
        for each in same_tag_users1:
            total_tags[each] = same_tag_users.count(each)
        
        # create the list of users for recommendation
        recommended_users = []
        recommended_users += mutual +  msg_recipient1 + post_comment1 + post_saved1 + post_liked1 + same_city_users + same_tag_users1
        recommended_users1 = list(set(recommended_users))
        for each in following:
            if each in recommended_users1:
                recommended_users1.remove(each)
        
        # calculate the relevancy score for each user
        rel_score = {}
        for each in recommended_users1:
            rel_score[each] = 0
            if each in mutual:
                rel_score[each] += 10
            if each in msg_recipient1:
                rel_score[each] += total_msgs[each]
            if each in post_comment1:
                rel_score[each] += total_comments[each]
            if each in post_saved1:
                rel_score[each] += total_saved[each]
            if each in post_liked1:
                rel_score[each] += total_liked[each]
            if each in same_city_users:
                rel_score[each] += 5
            if each in same_tag_users1:
                rel_score[each] += total_tags[each]
                
        
        sorted_rel = sorted(rel_score, key=rel_score.get)
        sorted_rel.reverse()
        
        result =[]
        for each in sorted_rel:
            result.append({"user_id": each, "relevancy_score": round(rel_score[each],2)})
        
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return UserRecommendedPageListType(users=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return UserRecommendedPageListType(users=result, page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return UserRecommendedPageListType(users=[], page_info=PageInfoObject(nextPage= None, limit=None))    
        
    # Get the list of user recommondations with relevancy score    
    def resolve_userRecommendations(parent,info,**kwargs):
        authUserId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if authUserId is not None:
            try:
                user = User.objects.using('default').get(user_id=authUserId)
                if not user.is_active:
                    raise BadRequestException("invalid request; userId provided is inactive", 400)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid", 400)
        
        # Find the users that authUserId follows

        following =[]
        following += UserFollowing.objects.using('default').filter(user_id = authUserId).values_list('following_user',flat=True)
        
        # Find the users with mutual following 
        mutual =[]
        for each in following:
            follower =[]
            follower += UserFollowing.objects.using('default').filter(user_id = each).values_list('following_user',flat=True)
            mutual += follower
        mutual = list(set(mutual))
        if authUserId in mutual:
            mutual.remove(authUserId)
        
        
        # Check if Search_user messeged by Current_user    
        msg_recipient = []
        msg_recipient += ChatMessage.objects.using('default').filter(sender = authUserId).values_list('chatmessagerecipient__user_id',flat = True)
        msg_recipient1 = list(set(msg_recipient))
        total_msgs = {}
        for each in msg_recipient1:
            total_msgs[each] = msg_recipient.count(each)
        
        
        # find the all user on whose post user commented
        post_comment = []
        post_comment += PostComment.objects.filter(user_id=authUserId).values_list('post__user_id',flat=True)
        post_comment1 = list(set(post_comment))
        if authUserId in post_comment1:
            post_comment1.remove(authUserId)
        total_comments = {}
        for each in post_comment1:
            total_comments[each] = post_comment.count(each)
        
        # find the all user whose post user saved
        post_saved = []
        post_saved += PostSaved.objects.filter(user_id=authUserId).values_list('post__user_id',flat=True)
        post_saved1 = list(set(post_saved))
        if authUserId in post_saved1:
            post_saved1.remove(authUserId)
        total_saved = {}
        for each in post_saved1:
            total_saved[each] = post_saved.count(each)
        
        # find the all user whose post user liked
        post_liked = []
        post_liked += PostLike.objects.filter(user_id=authUserId).values_list('post__user_id',flat=True)
        post_liked1 = list(set(post_liked))
        if authUserId in post_liked1:
            post_liked1.remove(authUserId)
        total_liked = {}
        for each in post_liked1:
            total_liked[each] = post_liked.count(each)
        
        # Find all the users that live in the same city as authUserId
        city_uid = UserProfile.objects.filter(user_id = authUserId).values('city_id')
        try:
            same_city_users =[]
            same_city_users += UserProfile.objects.filter(city_id = city_uid[0]['city_id']).values_list('user_id', flat=True)
            if authUserId in same_city_users:
                same_city_users.remove(authUserId)
        except:
            pass
        
        
        #check for the user_tag
        total_tags = {}
        tag_uid = []
        tag_uid += UserTag.objects.filter(user_id = authUserId).values_list('user_profile_tag',flat=True)
        same_tag_users = []
        for each in tag_uid:
            same_tag_users += UserTag.objects.filter(user_profile_tag = each).values_list('user_id',flat=True)
        same_tag_users1 = list(set(same_tag_users))
        if authUserId in same_tag_users1:
            same_tag_users1.remove(authUserId)
        for each in same_tag_users1:
            total_tags[each] = same_tag_users.count(each)
        
        
        # create the list of users for recommendation
        recommended_users = []
        recommended_users += following + mutual +  msg_recipient1 + post_comment1 + post_saved1 + post_liked1 + same_city_users + same_tag_users1
        recommended_users1 = list(set(recommended_users))
        
        
        # calculate the relevancy score for each user
        rel_score = {}
        for each in recommended_users1:
            rel_score[each] = 0
            if each in following:
                rel_score[each] += 15
            if each in mutual:
                rel_score[each] += 7
            if each in msg_recipient1:
                rel_score[each] += total_msgs[each]
            if each in post_comment1:
                rel_score[each] += total_comments[each]
            if each in post_saved1:
                rel_score[each] += total_saved[each]
            if each in post_liked1:
                rel_score[each] += total_liked[each]
            if each in same_city_users:
                rel_score[each] += 4
            if each in same_tag_users1:
                rel_score[each] += total_tags[each]
                
        
        sorted_rel = sorted(rel_score, key=rel_score.get)
        sorted_rel.reverse()
        
        result =[]
        for each in sorted_rel:
            result.append({"user_id": each, "relevancy_score": round(rel_score[each],2)})
        
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return UserRecommendedPageListType(users=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return UserRecommendedPageListType(users=result, page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return UserRecommendedPageListType(users=[], page_info=PageInfoObject(nextPage= None, limit=None))    