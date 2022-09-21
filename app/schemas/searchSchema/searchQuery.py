from email.policy import default
import graphene
from pyparsing import empty
import mcdm
from .searchType import *
from app.schemas.userAccountSchema.userAccountType import stringType
from app.schemas.commonObjects.objectTypes import APIPlacesListType
from app.utilities.errors import *
from app.models import *
import math
from app.utilities.redis import *
import datetime
import geopy.distance
from django.db.models import Q
from operator import getitem
from app.utilities.cache_lru import LRUCache
from datetime import  date, timedelta
import datetime
from app.utilities.filterVenueObjs import *
from app.utilities.filterDateVenueObjs import *
from app.schemas.postSchema.postType import PostListType
import requests
from app.utilities.locationPagination import locationPagination

from ..commonObjects.objectTypes import PageInfoObject
from ...utilities import Verification
from ...utilities.Verification import exp_availability_timeslot_checker


class Query(graphene.ObjectType):
    # Search Queries
    """getRecentSearch = graphene.List(RecentSearchType, user_id=graphene.Int())"""
    searchAllSuggestions = graphene.Field(AllSearchSuggestionsType, user_id=graphene.Int(), search_content=graphene.String(), latitude=graphene.Float(), longitude=graphene.Float(), page=graphene.Int(), limit=graphene.Int())
    searchAll = graphene.Field(AllSearchType, userId=graphene.Int(), searchContent=graphene.String(),
                               checkInDate=graphene.String(), checkOutDate=graphene.String(), location=locationObject())
    userResults = graphene.Field(SearchUserPageListType, userId=graphene.Int(), searchContent=graphene.String(),
                                 page=graphene.Int(), limit=graphene.Int())
    userResultsConcat = graphene.List(SearchUserListType, userId=graphene.Int(), searchContent=graphene.String(),
                                 page=graphene.Int(), limit=graphene.Int())
    stayResults = graphene.List(SearchStaysFilterValueType, userId=graphene.Int(), location=graphene.String(),
                                searchContent=graphene.String(), filterContent=staysFilterObject(),
                                checkInDate=graphene.String(), checkOutDate=graphene.String())
    transportationResults = graphene.List(SearchAllCarRentalType, userId=graphene.Int(),
                                          pickupLocation=locationObject(), dropoffLocation=locationObject(),
                                          searchContent=graphene.String(), filterContent=transportationsFilterObject(),
                                          checkInDate=graphene.String(), checkInTime=graphene.String(),
                                          checkOutDate=graphene.String(), checkOutTime=graphene.String())
    experienceResults = graphene.Field(SearchAllExperienceListType, userId=graphene.Int(), location=graphene.String(),
                                       searchContent=graphene.String(), filterContent=experiencesFilterObject(),
                                       startDate=graphene.String(), endDate=graphene.String(),
                                       page=graphene.Int(), limit=graphene.Int())
    experienceResultsConcat = graphene.List(SearchListTemplateType, userId=graphene.Int(), location=graphene.String(),
                                       searchContent=graphene.String(), filterContent=experiencesFilterObject(),
                                       startDate=graphene.String(), endDate=graphene.String(),
                                       page=graphene.Int(), limit=graphene.Int())
    searchTags = graphene.Field(SearchTagsValueListType, userId=graphene.Int(), searchContent=graphene.String(),
                                page=graphene.Int(), limit=graphene.Int())
    searchTagsConcat = graphene.List(SearchTagsValueType, userId=graphene.Int(), searchContent=graphene.String(),
                                page=graphene.Int(), limit=graphene.Int())
    searchVenues = graphene.Field(SearchPlacesValueListType, userId=graphene.Int(), searchContent=graphene.String(),
                                  page=graphene.Int(), limit=graphene.Int())
    searchVenuesConcat = graphene.List(SearchPlacesValueType, userId=graphene.Int(), searchContent=graphene.String(),
                                  page=graphene.Int(), limit=graphene.Int())
    searchHistory = graphene.List(SearchHistoryType, userId=graphene.Int())
    searchRecommendations = graphene.Field(AllSearchSuggestionsType, userId=graphene.Int(),
                                           searchContent=graphene.String())

    searchLocations = graphene.Field(SearchLocationObjectType, searchContent=graphene.String(), latitude = graphene.Float(), 
                                    longitude = graphene.Float(), page=graphene.Int(), limit=graphene.Int())
    searchLocationsConcat = graphene.Field(SearchLocationObjectConcatType, searchContent=graphene.String(), latitude = graphene.Float(), 
                                    longitude = graphene.Float(), page=graphene.Int(), limit=graphene.Int())
    
    # add search history term
    addSearchHistoryTerm = graphene.Field(stringType, userId=graphene.Int(), searchTerm=graphene.String())

    # Delete Search History Term
    deleteSearchHistoryTerm = graphene.Field(stringType, userId=graphene.Int(), searchTerm=graphene.String())
    # Delete Search History
    deleteSearchHistory = graphene.Field(stringType, userId=graphene.Int())
    # Get Post by Hashtag Id
    tagPosts = graphene.Field(SearchTagsValuePostListType, userId=graphene.Int(), tagId=graphene.Int(),
                              page=graphene.Int(), limit=graphene.Int())
    tagPostsConcat = graphene.List(PostListType, userId=graphene.Int(), tagId=graphene.Int(),
                              page=graphene.Int(), limit=graphene.Int())

    # Query Places -- Google API.
    queryPlaces = graphene.List(APIPlacesListType, userId=graphene.Int(), searchContent=graphene.String())

    # Search Users
    """
        This API takes in input from user their user id and serach keyword to display the users who have created user profiles in the application.
    """

    def resolve_userResults(parent, info, **kwagrs):
        authUserId = kwagrs.get('userId')
        search_content = kwagrs.get('searchContent')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if authUserId is not None:
            try:
                user = User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid", 400)

        if len(search_content) == 0:
            raise BadRequestException("invalid request; empty search string", 400)

        # if search_content is not None :
        #     if (search_content and search_content.strip()):
        #         client = redis_connect()
        #         search_history_cache = get_hashmap_from_cache(client, str(uid)+"_search_history")
        #         search_history_cache.put(search_content, datetime.datetime.now())
        #         print(search_history_cache.getAll())
        #         state = set_hashmap_to_cache(client, str(uid)+ "_search_history", search_history_cache)
        #         print(state)
        #     else:
        #         raise BadRequestException("invalid request; searchContent provided is empty", 400)
        # else:
        #     raise BadRequestException("invalid request; searchContent provided is invalid", 400)

        username_objs = []

        if authUserId is not None and search_content is not None:
            username_objs += User.objects.using('default').filter(Q(username__icontains=search_content) | Q(
                userprofile__user_profile_name__icontains=search_content)).values_list('user_id', flat=True)

        if authUserId in username_objs:
            username_objs.remove(authUserId)
        

        if not username_objs:
            raise NotFoundException("No user found with given search string", 400)

        # set the intial value of relevancy score for each Search_User object
        rel_score = {}
        for each in username_objs:
            rel_score[each] = 0

        # search for follower in the list
        follower_list = []
        follower_list += UserFollowing.objects.using('default').filter(user_id=authUserId).values_list('following_user',
                                                                                                       flat=True)
        following = {}
        for each in username_objs:
            if each in follower_list:
                following[each] = 1
                rel_score[each] += 10  # update the relevancy score if followed by Current_user
            else:
                following[each] = 0
       

        # Check if Search_user messeged by Current_user
        is_recipient = {}
        for each in username_objs:
            is_recipient[each] = ChatMessage.objects.using('default').filter(sender=authUserId,
                                                                             chatmessagerecipient__user_id=each).count()
            if is_recipient[each] is not None:
                rel_score[each] = rel_score[each] + is_recipient[each] * 0.1
       
        # Find the mutual following and update the rel_score

        for each in username_objs:
            following_by = []
            mutual = 0
            following_by += UserFollowing.objects.using('default').filter(user_id=each).values_list('following_user',
                                                                                                    flat=True)
            mutual = len(list(set.intersection(set(follower_list), set(following_by))))
            if mutual > 0:
                rel_score[each] = rel_score[each] + mutual * .8

        # Check if user commented on the post of search_user and update the rel_score
        no_of_comments = {}
        for each in username_objs:
            post_comment_list = Post.objects.filter(user_id=each, postcomment__user_id=authUserId).count()
            total_comments = post_comment_list
            no_of_comments[each] = total_comments
            rel_score[each] += total_comments * .4
        

        # Check if user liked the post of search_user and update the rel_score
        no_of_likes = {}
        for each in username_objs:
            post_likes_list = Post.objects.filter(user_id=each, postlike__user_id=authUserId).count()
            total_likes = post_likes_list
            no_of_likes[each] = total_likes
            rel_score[each] += total_likes * .4

        # check if user saved the post of search_user and update the rel_score
        no_of_saved = {}
        for each in username_objs:
            post_saved_list = Post.objects.filter(user_id=each, postsaved__user_id=authUserId).count()
            total_saved = post_saved_list
            no_of_saved[each] = total_saved
            rel_score[each] += total_saved * .4

        # check if user have the same city in location as of search_user and update the rel_score
        city_uid = UserProfile.objects.filter(user_id=authUserId).values('city_id')
        location_user = {}
        for each in username_objs:
            loc = UserProfile.objects.filter(user_id=each).values('city_id')
            if loc:
                location_user[each] = loc[0]
                if city_uid[0] == location_user[each]:
                    rel_score[each] = rel_score[each] + 1


        # check for the user_tag
        tag_uid = []
        common_tag = {}
        tag_uid += UserTag.objects.filter(user_id=authUserId).values_list('user_profile_tag', flat=True)
        for each in username_objs:
            tags = []
            tags += UserTag.objects.filter(user_id=each).values_list('user_profile_tag', flat=True)

            common_tag[each] = len(list(set.intersection(set(tags), set(tag_uid))))
            rel_score[each] = rel_score[each] + common_tag[each] * 0.6

        sorted_rel = sorted(rel_score, key=rel_score.get)
        sorted_rel.reverse()
        
        result = []
        for each in sorted_rel:
            result.append({"user_id": each, "relevancy_score": round(rel_score[each], 2)})

        if len(result) > 0:
            if page and limit:
                totalPages = math.ceil(len(result) / limit)
                if page <= totalPages:
                    start = limit * (page - 1)
                    result = result[start:start + limit]

                    return SearchUserPageListType(users=result, page_info=PageInfoObject(
                        nextPage=page + 1 if page + 1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return SearchUserPageListType(users=result, page_info=PageInfoObject(nextPage=None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")

        else:
            return SearchUserPageListType(users=[], page_info=PageInfoObject(nextPage=None, limit=None))
    
    def resolve_userResultsConcat(parent, info, **kwagrs):
        authUserId = kwagrs.get('userId')
        search_content = kwagrs.get('searchContent')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if authUserId is not None:
            try:
                user = User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid", 400)

        if len(search_content) == 0:
            raise BadRequestException("invalid request; empty search string", 400)

        # if search_content is not None :
        #     if (search_content and search_content.strip()):
        #         client = redis_connect()
        #         search_history_cache = get_hashmap_from_cache(client, str(uid)+"_search_history")
        #         search_history_cache.put(search_content, datetime.datetime.now())
        #         print(search_history_cache.getAll())
        #         state = set_hashmap_to_cache(client, str(uid)+ "_search_history", search_history_cache)
        #         print(state)
        #     else:
        #         raise BadRequestException("invalid request; searchContent provided is empty", 400)
        # else:
        #     raise BadRequestException("invalid request; searchContent provided is invalid", 400)

        username_objs = []

        if authUserId is not None and search_content is not None:
            username_objs += User.objects.using('default').filter(Q(username__icontains=search_content) | Q(
                userprofile__user_profile_name__icontains=search_content)).values_list('user_id', flat=True)

        if authUserId in username_objs:
            username_objs.remove(authUserId)
        # print("Search_user:",username_objs)
        # username_objs += [20210008]

        if not username_objs:
            raise NotFoundException("No user found with given search string", 400)

        # set the intial value of relevancy score for each Search_User object
        rel_score = {}
        for each in username_objs:
            rel_score[each] = 0

        # search for follower in the list
        follower_list = []
        follower_list += UserFollowing.objects.using('default').filter(user_id=authUserId).values_list('following_user',
                                                                                                       flat=True)
        following = {}
        for each in username_objs:
            if each in follower_list:
                following[each] = 1
                rel_score[each] += 10  # update the relevancy score if followed by Current_user
            else:
                following[each] = 0
        # print("following: ",following)
        # print("\nafter user you follow rel_score:", rel_score)

        # Check if Search_user messeged by Current_user
        is_recipient = {}
        for each in username_objs:
            is_recipient[each] = ChatMessage.objects.using('default').filter(sender=authUserId,
                                                                             chatmessagerecipient__user_id=each).count()
            if is_recipient[each] is not None:
                rel_score[each] = rel_score[each] + is_recipient[each] * 0.1
        # print("msg count: ", is_recipient)        

        # print("After you messeged users rel_score:", rel_score)

        # Find the mutual following and update the rel_score

        for each in username_objs:
            following_by = []
            mutual = 0
            following_by += UserFollowing.objects.using('default').filter(user_id=each).values_list('following_user',
                                                                                                    flat=True)
            mutual = len(list(set.intersection(set(follower_list), set(following_by))))
            # print(each, ": ", mutual)
            if mutual > 0:
                rel_score[each] = rel_score[each] + mutual * .8
        # print("\n after mutual follow: rel_score:", rel_score)

        # Check if user commented on the post of search_user and update the rel_score
        no_of_comments = {}
        for each in username_objs:
            post_comment_list = Post.objects.filter(user_id=each, postcomment__user_id=authUserId).count()
            total_comments = post_comment_list
            no_of_comments[each] = total_comments
            rel_score[each] += total_comments * .4
        # print("\n no of comments:", no_of_comments)    
        # print("after comment check: rel_score:", rel_score)

        # Check if user liked the post of search_user and update the rel_score
        no_of_likes = {}
        for each in username_objs:
            post_likes_list = Post.objects.filter(user_id=each, postlike__user_id=authUserId).count()
            total_likes = post_likes_list
            no_of_likes[each] = total_likes
            rel_score[each] += total_likes * .4
        # print("\n no of likes:", no_of_likes)    
        # print("after likes check: rel_score:", rel_score)

        # check if user saved the post of search_user and update the rel_score
        no_of_saved = {}
        for each in username_objs:
            post_saved_list = Post.objects.filter(user_id=each, postsaved__user_id=authUserId).count()
            total_saved = post_saved_list
            no_of_saved[each] = total_saved
            rel_score[each] += total_saved * .4
        # print("\n no of Saved post:", no_of_saved)    
        # print("after saved post: rel_score:", rel_score)

        # check if user have the same city in location as of search_user and update the rel_score
        city_uid = UserProfile.objects.filter(user_id=authUserId).values('city_id')
        # print(city_uid[0])
        location_user = {}
        for each in username_objs:
            loc = UserProfile.objects.filter(user_id=each).values('city_id')
            # print("loc",loc)
            if loc:
                location_user[each] = loc[0]
                if city_uid[0] == location_user[each]:
                    rel_score[each] = rel_score[each] + 1

        # print("\n location of each user: ",location_user)
        # print("after city check rel_score:", rel_score)

        # check for the user_tag
        tag_uid = []
        common_tag = {}
        tag_uid += UserTag.objects.filter(user_id=authUserId).values_list('user_profile_tag', flat=True)
        for each in username_objs:
            tags = []
            tags += UserTag.objects.filter(user_id=each).values_list('user_profile_tag', flat=True)

            common_tag[each] = len(list(set.intersection(set(tags), set(tag_uid))))
            rel_score[each] = rel_score[each] + common_tag[each] * 0.6

        # print("\n common_tag:",common_tag)
        # print("rel_score after common_tag:", rel_score)
        sorted_rel = sorted(rel_score, key=rel_score.get)
        sorted_rel.reverse()
        # print("sorted keys:", sorted_rel)
        result = []
        for each in sorted_rel:
            result.append({"user_id": each, "relevancy_score": round(rel_score[each], 2)})

        if len(result) > 0:
            if page and limit:
                totalPages = math.ceil(len(result) / limit)
                if page <= totalPages:
                    start = limit * (page - 1)
                    result = result[start:start + limit]

                    return SearchUserPageListType(users=result, page_info=PageInfoObject(
                        nextPage=page + 1 if page + 1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return result
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")

        else:
            return []


    # Search All Suggestions
    """
       This API takes in input userId, search_content, Longitude and Latitude of the user, page and limit and provides
       search suggestion for user, venue and hashtags with their id and rel_score
    """
    def resolve_searchAllSuggestions(parent, info, **kwagrs):
        authUserId = kwagrs.get('user_id')
        search_content = kwagrs.get('search_content')
        auth_lat = kwagrs.get('latitude')
        auth_long = kwagrs.get('longitude')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        
        authUser_city =[]
        if authUserId is not None:
            try:
                user= User.objects.using('default').filter(user_id=authUserId)
                #userProfile = UserProfile.objects.using('default').filter(user_id=authUserId)
                authUser_city += UserProfile.objects.using('default').filter(user_id = authUserId).values_list('city_id',flat = True)
                
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
            #except UserProfile.DoesNotExist:
                #raise NotFoundException("userId provided has not created a profile")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        
        if search_content is not None and len(search_content) == 0:
            raise BadRequestException("invalid request; empty search string", 400)
        
        if auth_lat is not None and auth_long is not None:
                    auth_cord = (auth_lat, auth_long)
        venues =[]
        venues_dict ={}
        if search_content is not None: 
            # Get the venues matching the search content      
            venues_obj = VenueInternal.objects.using('default').filter(venue_internal_name__icontains = search_content).values('venue_id','venue_internal_name')
            # print(venues_obj)
            for each in venues_obj:
                venues_dict[each['venue_id']] = each['venue_internal_name']
                venues.append(each['venue_id'])
            post_venue_count_lifetime={}
            post_view_count_lifetime ={}
            post_like_count_lifetime = {}
            booking_purchase_count_lifetime= {}
            post_venue_count_trending = {}
            post_view_count_trending = {}
            venue_lat = {}
            venue_long = {}
            post_like_count_trending = {}
            booking_purchase_count_trending= {}
            venue_cord = {}
            distance = {}
            for each in venues:
                distance[each] = -1
            end = datetime.datetime.now()   #start date and end date for trending
            start = end -timedelta(days=10)
            venue_feature_list =[]     # Feature matrix for calculating the MCDM
            
            for each in venues:
                temp_feature_list = []
                # total count of post for the venue
                post_venue_count_lifetime[each] = Post.objects.using('default').filter(venue_id = each).count()
                temp_feature_list.append(post_venue_count_lifetime[each]+1)
                # count of post in trending time
                post_venue_count_trending[each] = Post.objects.using('default').filter(venue_id = each, created_on__range = (start,end)).count()
                temp_feature_list.append(post_venue_count_trending[each]+1)
                # total post_view for the venue
                post_view_count_lifetime[each] = PostView.objects.using('default').filter(post__venue_id = each).count()
                temp_feature_list.append(post_view_count_lifetime[each]+1)
                # total post_view for the venue in trending time
                post_view_count_trending[each] = PostView.objects.using('default').filter(post__venue_id = each,created_on__range = (start,end) ).count()
                temp_feature_list.append(post_view_count_trending[each]+1)
                # total post_like for the venue
                post_like_count_lifetime[each] = PostLike.objects.using('default').filter(post__venue_id = each).count()
                temp_feature_list.append(post_like_count_lifetime[each]+1)
                # total post_like for the venue in trending time
                post_like_count_trending[each] = PostLike.objects.using('default').filter(post__venue_id = each,created_on__range = (start,end)).count()
                temp_feature_list.append(post_like_count_trending[each]+1) 
                # total bookings for the venue
                booking_purchase_count_lifetime[each] = BookingPurchase.objects.using('default').filter(venue_id = each).count()
                temp_feature_list.append(booking_purchase_count_lifetime[each]+1)
                # total booking for the venue in trending time
                booking_purchase_count_trending[each] = BookingPurchase.objects.using('default').filter(venue_id = each, created_on__range = (start,end)).count()
                temp_feature_list.append(booking_purchase_count_trending[each]+1)
                #latitude and longitude of the venue to calculate the distance from the user
                venue_lat[each] = VenueInternal.objects.using('default').filter(venue_id = each).values_list('address__city__latitude',flat=True)
                venue_long[each] = VenueInternal.objects.using('default').filter(venue_id = each).values_list('address__city__longitude',flat=True)
                
                #calculating distance of venue from the auth user's location
                venue_cord[each] = (venue_lat[each][0], venue_long[each][0])
                if auth_lat is not None and auth_long is not None:
                    distance[each] = geopy.distance.distance(auth_cord, venue_cord[each]).miles
                if(distance[each] > 0):
                    dist = distance[each]   
                elif(distance[each] == 0):
                    dist = 10
                else:
                    dist = .01
                temp_feature_list.append(dist)
                # adding all feature values of the venue to the list to create matrix
                venue_feature_list.append(temp_feature_list)
            
            # Creating weight vector to reflect the importance of any feature of the venue
            post_venue_count_lifetime_weight = 0.1
            post_venue_count_trending_weight = 0.15 
            post_view_count_lifetime_weight = 0.1
            post_view_count_trending_weight = 0.15 
            post_like_count_lifetime_weight = 0.1
            post_like_count_trending_weight = 0.15
            booking_purchase_count_lifetime_weight = 0.1
            booking_purchase_count_trending_weight = 0.1
            distance_weight =0.05

            w_vector = [post_venue_count_lifetime_weight,
                            post_venue_count_trending_weight,
                                post_view_count_lifetime_weight,
                                    post_view_count_trending_weight,
                                        post_like_count_lifetime_weight,
                                            post_like_count_trending_weight,
                                                booking_purchase_count_lifetime_weight,
                                                    booking_purchase_count_trending_weight,
                                                        distance_weight]
            
            # Calculating the relevancy score of each venue using multiplicative exponential weighting (MEW) method of Multi Criteria Decision Making (MCDM)
            if(len(venue_feature_list)>0):
                venues_rank = mcdm.rank(venue_feature_list, alt_names=venues, n_method="Linear1", w_vector=w_vector, s_method="MEW")
                
            else:
                venues_rank = []
            
            
            # Extract the tags having the search content as substring in tag_name
            tags = []
            tags_dict = {}
            tags_obj= Tag.objects.using('default').filter(tag_name__icontains = search_content).values('tag_id','tag_name')
            for each in tags_obj:
                tags_dict[each['tag_id']] = each['tag_name']
                tags.append(each['tag_id'])

            tag_post_view_count_lifetime = {}
            tag_post_view_count_trending = {}
            tag_post_count_lifetime = {}
            tag_post_count_trending = {}
            tag_post_count_authuser = {}
        
            tag_feature_list = []
            
            for each in tags:
                temp_feature_list = []
                # total count of post_view for the tag
                tag_post_view_count_lifetime[each] = PostView.objects.using('default').filter(post__posttag__tag_id = each).count()
                temp_feature_list.append(tag_post_view_count_lifetime[each]+1)
                # total count of the post_view for the tag in trending time
                tag_post_view_count_trending[each] = PostView.objects.using('default').filter(post__posttag__tag_id = each, created_on__range = (start,end)).count()
                temp_feature_list.append(tag_post_view_count_trending[each]+1)
                # total count of post for the tag
                tag_post_count_lifetime[each] = Post.objects.using('default').filter(posttag__tag_id = each).count()
                temp_feature_list.append(tag_post_count_lifetime[each]+1)
                # total count of post for the tag in trending time
                tag_post_count_trending[each] = Post.objects.using('default').filter(posttag__tag_id = each, created_on__range = (start,end)).count()
                temp_feature_list.append(tag_post_count_trending[each]+1)
                # total count of the post created by authuser with the tag
                tag_post_count_authuser[each] = Post.objects.using('default').filter(posttag__tag_id = each, user_id = authUserId).count()
                temp_feature_list.append(tag_post_count_authuser[each]+1)
                
                #add the features to the list to create matrix
                tag_feature_list.append(temp_feature_list)
            # Creating weight vector to reflect the importance of any feature of the tag    
            tag_post_view_count_lifetime_weight = 0.1
            tag_post_view_count_trending_weight = 0.25
            tag_post_count_lifetime_weight = 0.1
            tag_post_count_trending_weight = 0.25
            tag_post_count_authuser_weight = 0.3

            w_vector = [tag_post_view_count_lifetime_weight,
                            tag_post_view_count_trending_weight,
                                tag_post_count_lifetime_weight,
                                    tag_post_count_trending_weight,
                                        tag_post_count_authuser_weight]
            # Calculating the relevancy score of each hashtag using multiplicative exponential weighting (MEW) method of Multi Criteria Decision Making (MCDM)
            if(len(tag_feature_list)>0):
                tag_rank = mcdm.rank(tag_feature_list, alt_names=tags, n_method="Linear1",w_vector= w_vector, s_method="MEW")
                
            else:
                tag_rank = []
            
            
            # Extracting users whose profile_name matched with search_content
            usernames =[]
            if authUserId is not None and search_content is not None:
                usernames += UserProfile.objects.using('default').filter(user_profile_name__icontains=search_content).values('user_id','user_profile_name')
            username_objs= []
            username_dict = {}
            for x in usernames:
                username_dict[x['user_id']] = x['user_profile_name']
                username_objs.append(x['user_id'])

            if authUserId in username_objs:
                username_objs.remove(authUserId)

            #if not username_objs:
                #raise NotFoundException("No user found with given search string", 400)

            # search for follower in the list
            follower_list = []
            follower_list += UserFollowing.objects.using('default').filter(user_id=authUserId).values_list('following_user',
                                                                                                        flat=True)
            following = {}
            for each in username_objs:
                if each in follower_list:
                    following[each] = 1
                else:
                    following[each] = 0

            # Check if Search_user messeged by Current_user
            is_recipient = {}
            for each in username_objs:
                is_recipient[each] = ChatMessage.objects.using('default').filter(sender=authUserId,
                                                                                chatmessagerecipient__user_id=each).count()
 
            # Find the mutual following 
            mutual = {}
            for each in username_objs:
                following_by = []
                mutual[each] = 0
                following_by += UserFollowing.objects.using('default').filter(user_id=each).values_list('following_user',
                                                                                                        flat=True)
                mutual[each] = len(list(set.intersection(set(follower_list), set(following_by))))

            # Check if user commented on the post of search_user 
            no_of_comments = {}
            # check if user saved the post of search_user 
            no_of_saved = {}
            # Check if user liked the post of search_user 
            no_of_likes = {}
            for each in username_objs:
                no_of_comments[each] = Post.objects.filter(user_id=each, postcomment__user_id=authUserId).count()
                no_of_likes[each] = Post.objects.filter(user_id=each, postlike__user_id=authUserId).count()
                no_of_saved[each] = Post.objects.filter(user_id=each, postsaved__user_id=authUserId).count()
                
            # check if user have the same city in location as of search_user and update the rel_score
            city_uid = UserProfile.objects.filter(user_id=authUserId).values('city_id')
            
            same_location_user = {}
            for each in username_objs:
                loc = UserProfile.objects.filter(user_id=each).values('city_id')
                if loc:
                    same_location_user[each] = 1
                    if city_uid and loc and city_uid[0] == loc[0]:
                        same_location_user[each]=10

            # check for the user_tag
            tag_uid = []
            common_tag = {}
            tag_uid += UserTag.objects.filter(user_id=authUserId).values_list('user_profile_tag', flat=True)
            for each in username_objs:
                tags = []
                tags += UserTag.objects.filter(user_id=each).values_list('user_profile_tag', flat=True)
                common_tag[each] = len(list(set.intersection(set(tags), set(tag_uid))))
            #add the features to the list to create matrix for user
            user_feature_list = []
            for each in username_objs:
                temp_feature_list = []
                temp_feature_list.append(following[each]+1)
                temp_feature_list.append(is_recipient[each]+1)
                temp_feature_list.append(mutual[each]+1)
                temp_feature_list.append(no_of_comments[each]+1)
                temp_feature_list.append(no_of_likes[each]+1)
                temp_feature_list.append(no_of_saved[each]+1)
                temp_feature_list.append(same_location_user[each])
                temp_feature_list.append(common_tag[each]+1)
                user_feature_list.append(temp_feature_list)
            # Creating weight vector to reflect the importance of any feature of the user
            following_weight = 0.2
            msg_recipient_weight = 0.1
            mutual_follow_weight = 0.2
            no_of_comments_weight = 0.1
            no_of_likes_weight = 0.1
            no_of_saved_weight = 0.1
            location_weight =0.1
            common_tag_weight = 0.1
            w_vector = [following_weight,
                            msg_recipient_weight,
                                mutual_follow_weight,
                                    no_of_comments_weight,
                                        no_of_likes_weight,
                                            no_of_saved_weight,
                                                location_weight,
                                                    common_tag_weight]
            
            # Calculating the relevancy score of each hashtag using multiplicative exponential weighting (MEW) method of Multi Criteria Decision Making (MCDM)
            if(len(user_feature_list) > 0):
                user_rank = mcdm.rank(user_feature_list, alt_names=username_objs, n_method="Linear1", w_vector=w_vector, s_method="MEW")  
            else:
                user_rank = []

            results = []
            # Adding users to the result
            for each in user_rank:
                result = SearchSuggestionsType(each[0],username_dict[each[0]],round(each[1],2),'user')
                results.append(result)
            # Adding venues to the result
            for each in venues_rank:
                result = SearchSuggestionsType(each[0],venues_dict[each[0]],round(each[1],2),'venue')
                results.append(result)
            # Adding hashtags to the result
            for each in tag_rank:
                result = SearchSuggestionsType(each[0],tags_dict[each[0]],round(each[1],2),'hashtag')
                results.append(result)
            
            # sorting all results based on rel_score in descending order
            results.sort(key = lambda x : x.rel_score, reverse= True)
            
            # Sending results with pagination
            if len(results) > 0:
                if page and limit:
                    totalPages = math.ceil(len(results) / limit)
                    if page <= totalPages:
                        start = limit * (page - 1)
                        results = results[start:start + limit]

                        return AllSearchSuggestionsType(results=results, page_info=PageInfoObject(
                            nextPage=page + 1 if page + 1 <= totalPages else None, limit=limit))
                    else:
                        raise BadRequestException("invalid request; page provided exceeded total")
                elif page == limit == None:
                    return AllSearchSuggestionsType(results=results, page_info=PageInfoObject(nextPage=None, limit=None))
                elif page is None:
                    raise BadRequestException("invalid request; limit cannot be provided without page")
                elif limit is None:
                    raise BadRequestException("invalid request; page cannot be provided without limit")
            else:
                return AllSearchSuggestionsType(results=[], page_info=PageInfoObject(nextPage=None, limit=None))
        return None

    # Search Recommendations
    def resolve_searchRecommendations(self, info, **kwagrs):
        def calculate_distance_between_points(location_a, location_b):
            address_loc = Address.objects.using('default').get(address_id=1)
            zip = ZipCode.objects.using('default').get(zip_code_id=address_loc.zip_code_id)
            location_a = City.objects.using('default').get(city_id=zip.city_id)
            location_b = City.objects.using('default').get(city_id=location_b)

            if location_a is None or location_b is None:
                raise BadRequestException("user has not provided location access")
            if location_a.latitude is not None or location_a.longitude is not None or location_b.latitude is not None or location_b.longitude is not None:
                cord_a = (location_a.latitude, location_a.longitude)
                cord_b = (location_b.latitude, location_b.longitude)
                return geopy.distance.distance(cord_a, cord_b).miles
            else:
                raise BadRequestException("user has not provided location access")

        uid = kwagrs.get('userId')
        search_content = kwagrs.get('searchContent')
        if uid is not None:
            try:
                user = User.objects.using('default').get(user_id=uid)
                profileTags = UserTag.objects.using('default').filter(user_id=uid).values_list('user_profile_tag_id', flat=True)
                userProfile = UserProfile.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
            except UserProfile.DoesNotExist:
                userProfile = None
            except UserTag.DoesNotExist:
                profileTags = []
                # raise NotFoundException("useId provided has not added profile tags")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if search_content is not None:
            if search_content.strip():
                pass
            else:
                raise BadRequestException("searchContent provided is empty")
            json_search_content = {}
            json_content = {}

            # To collect all the Venue objects
            venues_obj_list = {}
            json_content = {}
            profileTagNames = []
            # for i in VenueExternal.objects.using('default').filter(venue_external_name__icontains=search_content):
            #     json_content[i.venue_id] = i
            for i in VenueInternal.objects.using('default').filter(venue_internal_name__icontains=search_content):
                json_content[i.venue_id] = i

            if profileTags != [] and profileTags:
                profileTagNames += UserProfileTag.objects.using('default').filter(
                    user_profile_tag_id__in=profileTags).values_list('user_profile_tag_name',flat=True)
            else:
                profileTagNames = []
            # for k, v in json_content.items():
            #     section = SearchAllSuggestionsVenueType(k, v.name)
            #     venues_obj_list.append(section)

            # location with location weight --- minimum weight is the best
            for k, v in json_content.items():
                json_content[k] = {'object': v, 'location_weight': calculate_distance_between_points(v.address_id,
                                                                                                     userProfile.city_id) if userProfile is not None else 0}
                # json_content['location_weight']= calculate_distance_between_points(json_content[i][1].location, )

            # weigh by number of profile tags present in object --- maximum value is best
            for k, v in json_content.items():
                # print(profileTagNames)
                # print(v['object'].name.split())
                set_profile_tags = set(v['object'].venue_internal_name.split()) & set(profileTagNames)
                if len(set_profile_tags) > 0:
                    json_content[k]['profile_tags_weight'] = len(set_profile_tags)
                else:
                    json_content[k]['profile_tags_weight'] = 0

            # weigh by mutual interest with friends --- how much
            followingUsers = []
            followingUsers += UserFollowing.objects.using('default').filter(user_id=uid).values_list(
                'following_user_id')
            followingUsers = [each[0] for each in followingUsers]
            # print(followingUsers)
            # get following user's post
            followingUsersPosts = []
            followingUsersProfileTagIds = []
            followingUsersProfileTags = []
            followingUsersPosts += Post.objects.using('default').filter(user_id__in=followingUsers).values_list(
                'post_id', 'venue_id')
            followingUsersProfileTagIds += UserTag.objects.using('default').filter(
                user_id__in=followingUsers).values_list('user_profile_tag_id', flat=True)
            print("followingUsersProfileTagIds",followingUsersProfileTagIds) 
            followingUsersProfileTagIds = [each for each in followingUsersProfileTagIds]
            followingUsersProfileTagIds = [j for j in followingUsersProfileTagIds]
            # print(followingUsersProfileTagIds)
            followingUsersProfileTags += UserProfileTag.objects.using('default').filter(
                user_profile_tag_id__in=followingUsersProfileTagIds).values_list('user_profile_tag_name', flat=True)

            # To collect all the following users venue objects
            following_venues_obj_list = {}
            following_json_content = {}
            followingUsersProfileTagNames = []
            venueids = []
            json_search_content["venues"] = []
            venueids = [each[1] for each in followingUsersPosts]
            # for i in VenueExternal.objects.using('default').filter(Q(venue_external_name__icontains=search_content)&Q(venue_id__in=venueids)):
            #     following_json_content[i.venue_id] = i
            for i in VenueInternal.objects.using('default').filter(
                    Q(venue_internal_name__icontains=search_content) & Q(venue_id__in=venueids)):
                following_json_content[i.venue_id] = i

            # location with location weight --- minimum weight is the best
            for k, v in following_json_content.items():
                # print(calculate_distance_between_points(v.location, userProfile.location))
                following_json_content[k] = {'object': v,
                                             'location_weight': calculate_distance_between_points(v.address_id,
                                                                                                  userProfile.city_id) if userProfile is not None else 0}
                # json_content['location_weight']= calculate_distance_between_points(json_content[i][1].location, )

            # weigh by number of profile tags present in object --- maximum value is best
            for k, v in following_json_content.items():
                # print(followingUsersProfileTags)
                # print(v['object'].name.split())
                following_set_profile_tags = set(v['object'].venue_internal_name.split()) & set(
                    followingUsersProfileTags)
                # print(following_set_profile_tags)
                if len(following_set_profile_tags) > 0:
                    following_json_content[k]['profile_tags_weight'] = len(following_set_profile_tags)
                else:
                    following_json_content[k]['profile_tags_weight'] = 0

            venues_obj_list = {**following_json_content, **json_content}

            ##Sorting the venue objects on location
            venues_obj_list = sorted(venues_obj_list.items(), key=lambda x: (
                getitem(x[1], 'location_weight'), (-getitem(x[1], 'profile_tags_weight'))))
            # for k,v in venue_obj_list.items():
            for k, v in venues_obj_list:
                json_search_content["venues"].append(
                    SearchAllSuggestionsVenueType(v['object'].venue_id, v['object'].venue_internal_name))

            # json_search_content["venues"]=venues_obj_list

            # To collect all the Tag objects
            tags_obj_list = []
            json_content = {}
            for i in Tag.objects.using('default').filter(tag_name__icontains=search_content):
                json_content[i.tag_id] = i.tag_name
            for k, v in json_content.items():
                section = SearchAllSuggestionsHashTagType(k, v)
                tags_obj_list.append(section)
            json_search_content["hashtags"] = tags_obj_list

            # To collect all the User objects
            users_obj_list = []
            json_content = {}
            userFollowing = []
            for i in User.objects.using('default').filter(username__icontains=search_content):
                # json_content[i.user_id] = {"username":i.username, "following_weight":0}
                try:
                    userFollowing += UserFollowing.objects.using('default').filter(user_id=uid,
                                                                                   following_user_id=i.user_id).values_list(
                        'following_user_id', flat=True)
                    if userFollowing != []:
                        json_content[i.user_id] = {"username": i.username, "following_weight": 1}
                    else:
                        raise Exception
                except:
                    json_content[i.user_id] = {"username": i.username, "following_weight": 0}
            # Sort the json_content
            json_content = dict(sorted(json_content.items(), key=lambda x: (-getitem(x[1], 'following_weight'))))
            for k, v in json_content.items():
                section = SearchAllSuggestionsUsersType(k, v["username"])
                users_obj_list.append(section)
            json_search_content["users"] = users_obj_list

            # Converting to graphql format
            section = AllSearchSuggestionsType(json_search_content["hashtags"], json_search_content["venues"],
                                               json_search_content["users"])

            return section
        else:
            raise BadRequestException("searchContetnt provided is invalid")
        return None

    # Search All
    def resolve_searchAll(parent, info, **kwagrs):

        def getCurrentCity(lat, lon):
            location = {
                "city": "Maple Grove",
                "state": "MN",
                "country": "US"
            }
            return location

        # def calculateVenueStayPrice(obj, date_venue_objs):

        #     for x in date_venue_objs:
        #         if x['venue_id'] == obj.venue_id:
        #             price = str(x['price'])

        #     return price

        def createGrapheneTypeObject(obj):

            if obj['user'] is not None:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'],
                                                 SearchFilterLocationType(obj['location']['city'],
                                                                          obj['location']['country'],
                                                                          obj['location']['lat'],
                                                                          obj['location']['long']),
                                                 SearchFilterVenueObjectType(obj['venue']['venue_id'],
                                                                             obj['venue']['venue_type_id'],
                                                                             obj['venue']['venue_type_name']),
                                                 obj['thumbnail'], obj['name'],
                                                 SearchFilterUserType(obj['user']['user_id'], obj['user']['username'],
                                                                      obj['user']['avatar'], obj['user']['level'],
                                                                      obj['user']['rating']))
            else:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'],
                                                 SearchFilterLocationType(obj['location']['city'],
                                                                          obj['location']['country'],
                                                                          obj['location']['lat'],
                                                                          obj['location']['long']),
                                                 SearchFilterVenueObjectType(obj['venue']['venue_id'],
                                                                             obj['venue']['venue_type_id'],
                                                                             obj['venue']['venue_type_name']),
                                                 obj['thumbnail'], obj['name'], None)
            return one

        uid = kwagrs.get('userId')
        search_content = kwagrs.get('searchContent')
        if uid is not None:
            pass
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if search_content is not None:
            # pass
            if (search_content and search_content.strip()):
                client = redis_connect()
                search_history_cache = get_hashmap_from_cache(client, str(uid) + "_search_history")
                if search_history_cache:
                    search_history_cache.put(search_content, datetime.datetime.now())
                    state = set_hashmap_to_cache(client, str(uid) + "_search_history", search_history_cache)
                else:
                    key = str(uid) + "_search_history"
                    search_history_cache = LRUCache(35)
                    # search_history_cache.put()
                    search_cache = set_hashmap_to_cache(client, key, search_history_cache)
                    search_history_cache.put(search_content, datetime.datetime.now())
                    state = set_hashmap_to_cache(client, key, search_history_cache)
            else:
                raise BadRequestException("invalid request; searchContent provided is empty", 400)


        else:
            raise BadRequestException("invalid request; searchContent provided is invalid", 400)

        check_in_date = kwagrs.get('checkInDate')
        if check_in_date is not None:
            pass
        else:
            raise BadRequestException("invalid request;  checkInDate provided is invalid", 400)
        if (check_in_date and check_in_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkInDate provided is empty", 400)

        check_out_date = kwagrs.get('checkOutDate')
        if check_out_date is not None:
            pass
        else:
            raise BadRequestException("invalid request;  checkOutDate provided is invalid", 400)
        if (check_out_date and check_out_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkOutDate provided is empty", 400)
        location = kwagrs.get('location')
        try:
            user = UserProfile.objects.using('default').get(user_id=uid)
        except UserProfile.DoesNotExist:
            raise NotFoundException("userId provided not found", 404)

        json_content = {}
        usr_obj_list = []
        stay_obj_list = []
        experience_obj_list = []
        hashtag_obj_list = []
        lat, lon = 45.1037, -93.4478
        default_location = {}
        default_location = location  # getCurrentCity(lat,lon)
        if default_location is None:
            raise NotFoundException("location is incorrect", 404)
        today = date.today()
        tomorrow = today + timedelta(days=1)
        check_in_date, check_out_date = date(int(check_in_date.split('-')[0]), int(check_in_date.split('-')[1]),
                                             int(check_in_date.split('-')[2])), date(int(check_out_date.split('-')[0]),
                                                                                     int(check_out_date.split('-')[1]),
                                                                                     int(check_out_date.split('-')[2]))
        default_dates = [check_in_date, check_out_date]

        if uid is not None and search_content is not None:
            """
                User Results
            """
            username_objs = []
            username_objs += User.objects.using('default').filter(username__icontains=search_content).values_list(
                'user_id', flat=True)
            # obj_list = UserProfile.objects.using('default').filter(Q(user_id__in = username_objs) | Q(name__icontains=search_content))
            json_content["users"] = username_objs

            # Stays Results

            # locations = Location.objects.using('default').filter(city=default_location["city"], country=default_location["country"]).values('location_id')

            # search_venue_objs = []
            # location_obj = []
            # json_result = []
            # venue_objs = []
            # search_venue_objs = []
            # date_venue_objs = []
            # filter_date_objs = []
            # location_venue_objs = []
            # post_objs = []

            # #Collecting Venue_Id with respect to search keywords
            # for i in VenueInternal.objects.using('default').filter(name__icontains=search_content, type_id=2).values_list('venue_id'):
            #     search_venue_objs.append(i[0])
            # for i in VenueExternal.objects.using('default').filter(name__icontains=search_content, type_id=2).values_list('venue_id'):
            #     search_venue_objs.append(i[0])

            # #Collectting venue_id with respect to the location given    
            # for i in VenueInternal.objects.using('default').filter(location_id__in=locations,type_id=2).values_list('venue_id') :
            #     location_venue_objs.append(i[0])
            # for i in VenueExternal.objects.using('default').filter(location_id__in=locations, type_id=2).values_list('venue_id'):
            #     location_venue_objs.append(i[0])

            # #Collecting venue_id with respect to the date given 
            # venue_type = "Stays"
            # filter_date_objs, date_venue_objs = getDateFilteredVenueObjects(default_dates, venue_type)

            # #Finding the common venue_id which is match the search keywords,
            # #location given and date availablitiy.

            # venue_objs = list(set(search_venue_objs).intersection(set(location_venue_objs)))
            # venue_objs = list(set(venue_objs).intersection(set(date_venue_objs)))

            # # #Creating Json Objects for each result
            # json_result = []

            # for obj in venue_objs:

            #     try:
            #         obj = VenueExternal.objects.using('default').get(venue_id=obj)
            #     except VenueExternal.DoesNotExist:
            #         obj = VenueInternal.objects.using('default').get(venue_id=obj)
            #     print(obj)

            #     try:

            #         post_objs = Post.objects.using('default').filter(venue_id=obj.venue_id)
            #         print(post_objs)
            #         if post_objs.exists():
            #             for obj_post in post_objs:
            #                 location = Location.objects.using('default').get(location_id=obj.location_id)
            #                 user = User.objects.using('default').get(user_id=obj_post.user_id)
            #                 price = calculateVenueStayPrice(obj, filter_date_objs)
            #                 json_obj = {
            #                     "is_post":True,
            #                     "price":str(price) if price is not None else None,
            #                     "location":{
            #                         "city":location.city,
            #                         "country":location.country,
            #                         "lat":str(location.latitude),
            #                         "long":str(location.longitude)
            #                         },
            #                     "name":obj.name,
            #                     "venue":{
            #                         "venue_id":obj.venue_id,
            #                         "venue_type_id":obj.type_id,
            #                         "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
            #                         },
            #                     "thumbnail":obj.thumbnail,
            #                     "user":{
            #                         "user_id":user.user_id,
            #                         "username":user.username,
            #                         "avatar":user.avatar,
            #                         "level":user.level,
            #                         "rating":str(obj_post.user_rating)
            #                         }
            #                 }
            #                 json_result.append(json_obj)
            #         else:
            #             location = Location.objects.using('default').get(location_id=obj.location_id)

            #             price = calculateVenueStayPrice(obj, filter_date_objs)
            #             json_obj = {
            #                     "is_post":False,
            #                     "price":str(price) if price is not None else None,
            #                     "location":{
            #                         "city":location.city,
            #                         "country":location.country,
            #                         "lat":str(location.latitude),
            #                         "long":str(location.longitude)
            #                     },
            #                     "name":obj.name,
            #                     "venue":{
            #                         "venue_id":obj.venue_id,
            #                         "venue_type_id":obj.type_id,
            #                         "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
            #                         },
            #                     "thumbnail":obj.thumbnail,
            #                     "user":None
            #                 }
            #             json_result.append(json_obj)

            #     except (Post.DoesNotExist):
            #         location = Location.objects.using('default').get(location_id=obj.location_id)

            #         price = calculateVenueStayPrice(obj, filter_date_objs)
            #         json_obj = {
            #                 "is_post":False,
            #                 "price":str(price) if price is not None else None,
            #                 "location":{
            #                     "city":location.city,
            #                     "country":location.country,
            #                     "lat":str(location.latitude),
            #                     "long":str(location.longitude)
            #                     },
            #                 "name":obj.name,
            #                 "venue":{
            #                         "venue_id":obj.venue_id,
            #                         "venue_type_id":obj.type_id,
            #                         "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
            #                     },
            #                 "thumbnail":obj.thumbnail,
            #                 "user":None
            #             }
            #         json_result.append(json_obj)
            # json_content["stays"] = json_result
            # print(json_content["stays"])

            # Experiences
            """
                    Things To Do Results
            """
            locations = []
            locations += City.objects.using('default').filter(city_name=default_location["city"]).values_list('city_id',
                                                                                                              flat=True)
            locations += Country.objects.using('default').filter(country_name=default_location["country"]).values_list(
                'country_id', flat=True)
            # locations += Location.objects.using('default').filter(city=default_location["city"], country=default_location["country"]).values_list('location_id', flat=True)
            search_venue_objs = []
            location_obj = []
            json_result = []
            venue_objs = []
            date_venue_objs = []
            filter_date_objs = []
            location_venue_objs = []
            post_objs = []

            # Collecting Venue_Id with respect to search keywords
            for i in VenueInternal.objects.using('default').filter(
                    Q(venue_internal_name__icontains=search_content, venue_type_id=1) | Q(
                        venue_internal_description__icontains=search_content, venue_type_id=1)).values_list(
                'venue_id'):
                search_venue_objs.append(i[0])
            # for i in VenueExternal.objects.using('default').filter(Q(venue_external_name__icontains=search_content, venue_type_id=1 ) |Q(venue_external_description__icontains=search_content, venue_type_id=1)).values_list('venue_id'):
            #     search_venue_objs.append(i[0])

            # Collectting venue_id with respect to the location given
            for i in VenueInternal.objects.using('default').filter(location_id__in=locations,
                                                                   venue_type_id=1).values_list('venue_id'):
                location_venue_objs.append(i[0])
            # for i in VenueExternal.objects.using('default').filter(location_id__in=locations, venue_type_id=1).values_list('venue_id'):
            #     location_venue_objs.append(i[0])

            # Collecting venue_id with respect to the date given
            venue_type = "Experiences"
            filter_date_objs, date_venue_objs = getDateFilteredVenueObjects(default_dates, venue_type)

            # Finding the common venue_id which is match the search keywords,
            # location given and date availablitiy.

            venue_objs = list(set(search_venue_objs).intersection(set(location_venue_objs)))
            venue_objs = list(set(venue_objs).intersection(set(date_venue_objs)))
            # #Creating Json Objects for each result
            json_result = []
            for obj in venue_objs:

                try:
                    obj = VenueExternal.objects.using('default').get(venue_id=obj)
                except VenueExternal.DoesNotExist:
                    obj = VenueInternal.objects.using('default').get(venue_id=obj)

                try:
                    # post_venue_id = PostVenue.objects.using('default').get(venue_id=obj.venue_id)
                    # print(post_venue_id)
                    post_objs = Post.objects.using('default').filter(venue_id=obj.venue_id)
                    # if post_objs.exists():
                    for obj_post in post_objs:
                        # try :
                        #     price = calculateVenueStayPrice(obj, filter_date_objs)

                        # except VenueStayPrice.DoesNotExist:
                        #     price = None

                        location = Location.objects.using('default').get(location_id=obj.location_id)
                        user = User.objects.using('default').get(user_id=obj_post.user_id)
                        price = calculateVenueStayPrice(obj, filter_date_objs)
                        json_obj = {
                            "is_post": True,
                            "template": {
                                "id": str(obj_post.post_id),
                                "type": 1
                            }
                            # "price":str(price) if price is not None else None,
                            # "location":{
                            #     "city":location.city,
                            #     "country":location.country,
                            #     "lat":str(location.latitude),
                            #     "long":str(location.longitude)
                            #     },
                            # "name":obj.name,
                            # "venue":{
                            #     "venue_id":obj.venue_id,
                            #     "venue_type_id":obj.type_id,
                            #     "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                            #     },
                            # "thumbnail":obj.thumbnail,
                            # "user":{
                            #     "user_id":obj_post.user_id,
                            #     # "username":user.username,
                            #     # "avatar":user.avatar,
                            #     # "level":user.level,
                            #     # "rating":str(obj_post.user_rating)
                            #     }
                        }
                        json_result.append(json_obj)

                    location = Location.objects.using('default').get(location_id=obj.location_id)
                    # try :
                    #     # price = VenueStayPrice.objects.using('default').get(venue_id=obj.venue_id)
                    #     # price= price.price
                    #     price = calculateVenueStayPrice(obj, filter_date_objs)

                    # except VenueStayPrice.DoesNotExist:
                    #     price = None
                    price = calculateVenueStayPrice(obj, filter_date_objs)
                    json_obj = {
                        "is_post": False,
                        "template": {
                            "id": obj.venue_id,
                            "type": 2
                        }
                        # "price":str(price) if price is not None else None,
                        # "location":{
                        #     "city":location.city,
                        #     "country":location.country,
                        #     "lat":str(location.latitude),
                        #     "long":str(location.longitude)
                        # },
                        # "name":obj.name,
                        # "venue":{
                        #     "venue_id":obj.venue_id,
                        #     "venue_type_id":obj.type_id,
                        #     "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                        #     },
                        # "thumbnail":obj.thumbnail,
                        # "user":None
                    }
                    json_result.append(json_obj)

                except (Post.DoesNotExist):
                    location = Location.objects.using('default').get(location_id=obj.location_id)
                    # try :
                    #     # price = VenueStayPrice.objects.using('default').get(venue_id=obj.venue_id)
                    #     # price= price.price
                    #     price = calculateVenueStayPrice(obj,filter_date_objs)

                    # except VenueStayPrice.DoesNotExist:
                    #     price = None
                    price = calculateVenueStayPrice(obj, filter_date_objs)
                    json_obj = {
                        "is_post": False,
                        "template": {
                            "id": obj.venue_id,
                            "type": 2
                        }
                        # "price":str(price) if price is not None else None,
                        # "location":{
                        #     "city":location.city,
                        #     "country":location.country,
                        #     "lat":str(location.latitude),
                        #     "long":str(location.longitude)
                        #     },
                        # "name":obj.name,
                        # "venue":{
                        #         "venue_id":obj.venue_id,
                        #         "venue_type_id":obj.type_id,
                        #         "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                        #     },
                        # "thumbnail":obj.thumbnail,
                        # "user":None
                    }
                    json_result.append(json_obj)
            json_content["thingstodo"] = json_result

            # Transportation
            """
                    Car Rentals
            """
            # json_result = []
            # pickup_location = default_location["city"]       
            # dropoff_location = default_location["city"]

            # locations = Location.objects.using('default').filter(city__in=[pickup_location, dropoff_location]).values('location_id')
            # search_venue_objs = []
            # location_obj = []

            # #Collecting Venue_Id with respect to search keywords
            # for i in VenueInternal.objects.using('default').filter(name__icontains=search_content, type_id=3).values_list('venue_id'):
            #     search_venue_objs.append(i[0])
            # for i in VenueExternal.objects.using('default').filter(name__icontains=search_content, type_id=3).values_list('venue_id'):
            #     search_venue_objs.append(i[0])

            # #Collectting venue_id with respect to the location given    
            # for i in VenueInternal.objects.using('default').filter(location_id__in=locations,type_id=3).values_list('venue_id') :
            #     location_venue_objs.append(i[0])
            # for i in VenueExternal.objects.using('default').filter(location_id__in=locations, type_id=3).values_list('venue_id'):
            #     location_venue_objs.append(i[0])

            # #Collecting venue_id with respect to the date given
            # venue_type="Transportations" 
            # default_dates = ["2021-10-15", "2021-10-16", "00:00:00", "01:00:00"]
            # filter_date_objs, date_venue_objs = getDateFilteredVenueObjects(default_dates, venue_type)

            # #Finding the common venue_id which is match the search keywords,
            # #location given and date availablitiy.
            # print("search")
            # print(search_venue_objs)
            # print(location_venue_objs)
            # venue_objs = list(set(search_venue_objs).intersection(set(location_venue_objs)))
            # print(venue_objs)
            # print(date_venue_objs)
            # venue_objs = list(set(venue_objs).intersection(set(date_venue_objs)))
            # print("Car Rentl")
            # print(venue_objs)
            # venue_type = "Transportation"
            # for obj in venue_objs:
            #     try:
            #         obj = VenueExternal.objects.using('default').get(venue_id=obj)
            #     except VenueExternal.DoesNotExist:
            #         obj = VenueInternal.objects.using('default').get(venue_id=obj)

            #     location = Location.objects.using('default').get(location_id=obj.location_id)
            #     price = calculateVenueStayPrice(obj, filter_date_objs)
            #     json_obj = {
            #         "is_post":False,
            #         "price":str(price) if price is not None else None,
            #         "location":{
            #             "city":location.city,
            #             "country":location.country,
            #             "lat":str(location.latitude),
            #             "long":str(location.longitude)
            #             },
            #         "name":obj.name,
            #         "venue":{
            #             "venue_id":obj.venue_id,
            #             "venue_type_id":obj.type_id,
            #             "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
            #             },
            #         "thumbnail":obj.thumbnail,
            #         "user":None
            #         }
            #     json_result.append(json_obj)
            # json_content["transportation"] = json_result

            """
                HashTags
            """
            # To collect all the Tag objects
            # tags_obj_list =[]
            # for i in Tag.objects.using('default').filter(name__icontains=search_content):
            #     json_content[i.tag_id] = i.name
            # for k, v in json_content.items():
            #     section = SearchAllSuggestionsHashTagType(k, v)
            #     tags_obj_list.append(section)
            # json_content["hashtags"]=tags_obj_list

            # Converting into graphene objects

            # result_stays = []
            # for i in json_content["stays"]:
            #     result_stays.append(createGrapheneTypeObject(i))
            # if len(result_stays) > 4:
            #     result_stays = result_stays[0:4]

            result_thingstodo = []
            for i in json_content["thingstodo"]:
                result_thingstodo.append(i)
            if len(result_thingstodo) > 4:
                result_thingstodo = result_thingstodo[0:4]

            # result_transportation = []
            # for i in json_content["transportation"]:
            #     result_transportation.append(createGrapheneTypeObject(i))
            # if len(result_transportation) > 4:
            #     result_transportation = result_transportation[0:4]

            # if len(json_content["users"]) > 3:
            #     json_content["users"] = json_content["users"]
            result_users = []
            for each in json_content["users"]:
                result_users.append({"user_id": each})

            # if len(json_content["hashtags"]) > 3:
            #     json_content["hashtags"] = json_content["hashtags"][0:3]   

            return AllSearchType(result_users, result_thingstodo)

        return None

    # Search Stays with Filter
    def resolve_stayResults(parent, info, **kwagrs):

        def createGrapheneTypeObject(obj):
            if obj['user'] is not None:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'],
                                                 SearchFilterLocationType(obj['location']['city'],
                                                                          obj['location']['country'],
                                                                          obj['location']['lat'],
                                                                          obj['location']['long']),
                                                 SearchFilterVenueObjectType(obj['venue']['venue_id'],
                                                                             obj['venue']['venue_type_id'],
                                                                             obj['venue']['venue_type_name']),
                                                 obj['thumbnail'], obj['name'],
                                                 SearchFilterUserType(obj['user']['user_id'], obj['user']['username'],
                                                                      obj['user']['avatar'], obj['user']['level'],
                                                                      obj['user']['rating']))
            else:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'],
                                                 SearchFilterLocationType(obj['location']['city'],
                                                                          obj['location']['country'],
                                                                          obj['location']['lat'],
                                                                          obj['location']['long']),
                                                 SearchFilterVenueObjectType(obj['venue']['venue_id'],
                                                                             obj['venue']['venue_type_id'],
                                                                             obj['venue']['venue_type_name']),
                                                 obj['thumbnail'], obj['name'], None)
            return one

        # User Id
        uid = kwagrs.get('userId')
        if uid is not None:
            pass
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Search Content
        search_content = kwagrs.get('searchContent')
        if search_content is not None:
            # client = redis_connect()
            # search_history_cache = get_hashmap_from_cache(client, str(uid)+"_search_history")
            # search_history_cache.put(search_content, datetime.datetime.now())
            # print(search_history_cache.getAll())
            # state = set_hashmap_to_cache(client, str(uid)+ "_search_history", search_history_cache)
            # print(state)
            pass
        else:
            raise BadRequestException("invalid request; searchContent provided is invalid", 400)

        if search_content and search_content.strip():
            pass
        else:
            raise BadRequestException("invalid request; searchContent provided is empty", 400)
        # Location
        search_location = kwagrs.get('location')
        if search_location is not None:
            pass
        else:
            raise BadRequestException("invalid request; location provided is invalid", 400)

        if (search_location and search_location.strip()):
            pass
        else:
            raise BadRequestException("invalid request; location provided is empty", 400)
        # Check in Date
        search_checkin_date = kwagrs.get('checkInDate')
        if search_checkin_date is not None and (search_checkin_date and search_checkin_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkInDate provided is invalid", 400)
        # Check Out Date
        search_checkout_date = kwagrs.get('checkOutDate')
        if search_checkout_date is not None and (search_checkout_date and search_checkout_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkOutDate provided is invalid", 400)
        # Filter Content
        filter_content = kwagrs.get('filterContent')
        if filter_content is not None:
            input_json_filter_content = {
                "noOfGuests": filter_content['noOfGuests'],
                "stay_type": filter_content['typeOfStay'],
                "unique_stay": filter_content['uniqueStays'],
                "amenities": filter_content['amenities'],
                "max_price": filter_content['pricing'].max if filter_content['pricing'].max != 10000 else 10000,
                "min_price": filter_content['pricing'].min if filter_content['pricing'].min != 0 else 0,
                "rating": filter_content['userRatings'],
                "sort_by": filter_content['sortBy']

            }

        try:
            user = User.objects.using('default').get(user_id=uid)
        except User.DoesNotExist:
            raise NotFoundException("userId provided not found", 404)

        # Logic
        json_search_content = {}
        json_content = {}
        objs_list = []

        filtered_venue_id_by_amenity = []
        filtered_venue_id_by_staytype = []
        filtered_venue_id_by_price = []

        # Filter by Location
        location_obj = []
        json_result = []
        venue_objs = []
        search_venue_objs = []
        date_venue_objs = []
        filter_date_objs = []
        location_venue_objs = []
        post_objs = []
        locations = []

        city = search_location.split(',')[0]
        state = search_location.split(',')[1].replace(' ', '')
        locations = Location.objects.using('default').filter(city=city, state=state).values('location_id')
        i = 0

        # Collecting Venue_Id with respect to search keywords
        for i in VenueInternal.objects.using('default').filter(name__icontains=kwagrs.get('searchContent'),
                                                               venue_type_id=2).values_list('venue_id'):
            search_venue_objs.append(i[0])
        for i in VenueExternal.objects.using('default').filter(name__icontains=kwagrs.get('searchContent'),
                                                               venue_type_id=2).values_list('venue_id'):
            search_venue_objs.append(i[0])

        # Collectting venue_id with respect to the location given
        for i in VenueInternal.objects.using('default').filter(location_id__in=locations, venue_type_id=2).values_list(
                'venue_id'):
            location_venue_objs.append(i[0])
        for i in VenueExternal.objects.using('default').filter(location_id__in=locations, venue_type_id=2).values_list(
                'venue_id'):
            location_venue_objs.append(i[0])

        # Collecting venue_id with respect to the date given
        dates_in_the_range = dates_between(search_checkin_date, search_checkout_date)
        filter_date_objs, date_venue_objs = getDateFilteredVenueObjects(dates_in_the_range, "Stays")

        # Finding the common venue_id which is match the search keywords,
        # location given and date availablitiy.
        venue_objs = list(set(search_venue_objs).intersection(set(location_venue_objs)))
        venue_objs = list(set(venue_objs).intersection(set(date_venue_objs)))

        for obj in venue_objs:

            try:
                obj = VenueExternal.objects.using('default').get(venue_id=obj)
            except VenueExternal.DoesNotExist:
                obj = VenueInternal.objects.using('default').get(venue_id=obj)

            try:
                post_objs = Post.objects.using('default').filter(venue_id=obj.venue_id)
                if post_objs.exists():
                    for obj_post in post_objs:
                        location = Location.objects.using('default').get(location_id=obj.location_id)
                        user = User.objects.using('default').get(user_id=obj_post.user_id)
                        price = calculateVenueStayPrice(obj, filter_date_objs)
                        json_obj = {
                            "is_post": True,
                            "price": str(price) if price is not None else None,
                            "location": {
                                "city": city,
                                "country": location.country,
                                "lat": str(location.latitude),
                                "long": str(location.longitude)
                            },
                            "name": obj.name,
                            "venue": {
                                "venue_id": obj.venue_id,
                                "venue_type_id": obj.venue_type_id,
                                "venue_type_name": VenueType.objects.using('default').get(
                                    venue_type_id=obj.venue_type_id).venue_type_name
                            },
                            "thumbnail": obj.thumbnail,
                            "user": {
                                "user_id": user.user_id,
                                "username": user.username,
                                "avatar": user.avatar,
                                "level": user.level,
                                "rating": str(obj_post.user_rating)
                            }
                        }
                        json_result.append(json_obj)
                else:
                    location = Location.objects.using('default').get(location_id=obj.location_id)
                    price = calculateVenueStayPrice(obj, filter_date_objs)
                    json_obj = {
                        "is_post": False,
                        "price": str(price) if price is not None else None,
                        "location": {
                            "city": city,
                            "country": location.country,
                            "lat": str(location.latitude),
                            "long": str(location.longitude)
                        },
                        "name": obj.name,
                        "venue": {
                            "venue_id": obj.venue_id,
                            "venue_type_id": obj.venue_type_id,
                            "venue_type_name": VenueType.objects.using('default').get(
                                venue_type_id=obj.venue_type_id).venue_type_name
                        },
                        "thumbnail": obj.thumbnail,
                        "user": None
                    }
                    json_result.append(json_obj)

            except (Post.DoesNotExist):
                location = Location.objects.using('default').get(location_id=obj.location_id)
                price = calculateVenueStayPrice(obj, filter_date_objs)
                json_obj = {
                    "is_post": False,
                    "price": str(price) if price is not None else None,
                    "location": {
                        "city": city,
                        "country": location.country,
                        "lat": str(location.latitude),
                        "long": str(location.longitude)
                    },
                    "name": obj.name,
                    "venue": {
                        "venue_id": obj.venue_id,
                        "venue_type_id": obj.venue_type_id,
                        "venue_type_name": VenueType.objects.using('default').get(
                            venue_type_id=obj.venue_type_id).venue_type_name
                    },
                    "thumbnail": obj.thumbnail,
                    "user": None
                }
                json_result.append(json_obj)

        one_json = filterStayVenueObjs(json_result, input_json_filter_content)
        one_json = [createGrapheneTypeObject(x) for x in one_json]

        return one_json

        return None

    # Search Transportation with Filter
    def resolve_transportationResults(parent, info, **kwagrs):
        def createGrapheneTypeObject(obj):

            if obj['user'] is not None:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'],
                                                 SearchFilterLocationType(obj['location']['city'],
                                                                          obj['location']['country'],
                                                                          obj['location']['lat'],
                                                                          obj['location']['long']),
                                                 SearchFilterVenueObjectType(obj['venue']['venue_id'],
                                                                             obj['venue']['venue_type_id'],
                                                                             obj['venue']['venue_type_name']),
                                                 obj['thumbnail'], obj['name'],
                                                 SearchFilterUserType(obj['user']['user_id'], obj['user']['username'],
                                                                      obj['user']['avatar'], obj['user']['level'],
                                                                      obj['user']['rating']))
            else:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'],
                                                 SearchFilterLocationType(obj['location']['city'],
                                                                          obj['location']['country'],
                                                                          obj['location']['lat'],
                                                                          obj['location']['long']),
                                                 SearchFilterVenueObjectType(obj['venue']['venue_id'],
                                                                             obj['venue']['venue_type_id'],
                                                                             obj['venue']['venue_type_name']),
                                                 obj['thumbnail'], obj['name'], None)
            return one

        # User ID
        uid = kwagrs.get('userId')
        if uid is not None:
            pass
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Search Content
        search_content = kwagrs.get('searchContent')
        if search_content is not None:
            # client = redis_connect()
            # search_history_cache = get_hashmap_from_cache(client, str(uid)+"_search_history")
            # search_history_cache.put(search_content, datetime.datetime.now())
            # print(search_history_cache.getAll())
            # state = set_hashmap_to_cache(client, str(uid)+ "_search_history", search_history_cache)
            # print(state)
            pass
        else:
            raise BadRequestException("invalid request; searchContent provided is invalid", 400)

        if search_content and search_content.strip():
            pass
        else:
            raise BadRequestException("invalid request; searchContent provided is empty", 400)
        # Pick up Location
        pickup_location = kwagrs.get('pickupLocation')
        if pickup_location is not None:
            pass
        else:
            raise BadRequestException("invalid request; pickupLocation provided is invalid", 400)

        # Drop off Location
        dropoff_location = kwagrs.get('dropoffLocation')
        if dropoff_location is not None:
            pass
        else:
            raise BadRequestException("invalid request; dropoffLocation provided is invalid", 400)

        # Check In Date
        search_checkin_date = kwagrs.get('checkInDate')
        if search_checkin_date is not None and (search_checkin_date and search_checkin_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkInDate provided is invalid", 400)
        # Check Out Date
        search_checkout_date = kwagrs.get('checkOutDate')
        if search_checkout_date is not None and (search_checkout_date and search_checkout_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkOutDate provided is invalid", 400)
        # Check In Time
        search_checkin_time = kwagrs.get('checkInTime')
        if search_checkin_time is not None and (search_checkin_time and search_checkin_time.strip()):
            search_checkin_time = datetime.time(int(search_checkin_time.split(':')[0]),
                                                int(search_checkin_time.split(':')[1]),
                                                int(search_checkin_time.split(':')[2]))
        else:
            raise BadRequestException("invalid request; checkInTime provided is invalid", 400)
        # Check Out Time
        search_checkout_time = kwagrs.get('checkOutTime')
        if search_checkout_time is not None and (search_checkout_time and search_checkout_time.strip()):
            search_checkout_time = datetime.time(int(search_checkout_time.split(':')[0]),
                                                 int(search_checkout_time.split(':')[1]),
                                                 int(search_checkout_time.split(':')[2]))
        else:
            raise BadRequestException("invalid request; checkOutTime provided is invalid", 400)
        # Filter Content
        filter_content = kwagrs.get('filterContent')
        if filter_content is not None:
            input_json_filter_content = {

                "vehicle_type": filter_content['vehicleType'],
                "max_price": filter_content['pricing'].max if filter_content['pricing'].max != 10000 else 10000,
                "min_price": filter_content['pricing'].min if filter_content['pricing'].min != 0 else 0,
                "sort_by": filter_content['sortBy'],
                "capacity": filter_content['capacity']

            }

        try:
            user = User.objects.using('default').get(user_id=uid)
        except User.DoesNotExist:
            raise NotFoundException("userId provided not found", 404)

        # Logic
        json_result = []

        locations = Location.objects.using('default').filter(
            city__in=[pickup_location.city, dropoff_location.city]).values('location_id')
        search_venue_objs = []
        location_venue_objs = []

        # Collecting Venue_Id with respect to search keywords
        for i in VenueInternal.objects.using('default').filter(name__icontains=search_content,
                                                               venue_type_id=3).values_list('venue_id'):
            search_venue_objs.append(i[0])
        for i in VenueExternal.objects.using('default').filter(name__icontains=search_content,
                                                               venue_type_id=3).values_list('venue_id'):
            search_venue_objs.append(i[0])

        # Collectting venue_id with respect to the location given
        for i in VenueInternal.objects.using('default').filter(location_id__in=locations, venue_type_id=3).values_list(
                'venue_id'):
            location_venue_objs.append(i[0])
        for i in VenueExternal.objects.using('default').filter(location_id__in=locations, venue_type_id=3).values_list(
                'venue_id'):
            location_venue_objs.append(i[0])

        # Collecting venue_id with respect to the date given
        filter_date_objs, date_venue_objs = getDateFilteredVenueObjects(
            [search_checkin_date, search_checkout_date, search_checkout_time, search_checkout_time], "Transportations")

        # Finding the common venue_id which is match the search keywords,
        # location given and date availablitiy.
        venue_objs = list(set(search_venue_objs).intersection(set(location_venue_objs)))
        venue_objs = list(set(venue_objs).intersection(set(date_venue_objs)))

        for obj in venue_objs:
            try:
                obj = VenueExternal.objects.using('default').get(venue_id=obj)
            except VenueExternal.DoesNotExist:
                obj = VenueInternal.objects.using('default').get(venue_id=obj)

            location = Location.objects.using('default').get(location_id=obj.location_id)
            price = calculateVenueStayPrice(obj, filter_date_objs)
            json_obj = {
                "is_post": False,
                "price": str(price) if price is not None else None,
                "location": {
                    "city": location.city,
                    "country": location.country,
                    "lat": str(location.latitude),
                    "long": str(location.longitude)
                },
                "name": obj.name,
                "venue": {
                    "venue_id": obj.venue_id,
                    "venue_type_id": obj.venue_type_id,
                    "venue_type_name": VenueType.objects.using('default').get(
                        venue_type_id=obj.venue_type_id).venue_type_name
                },
                "thumbnail": obj.thumbnail,
                "user": None
            }
            json_result.append(json_obj)

        # Filtering Logic
        one_json = filterTransportationVenueObjs(json_result, input_json_filter_content)
        one_json = [createGrapheneTypeObject(x) for x in one_json]
        return one_json

    # Search Tags
    def resolve_searchTags(self, info, **kwargs):
        # User Id
        userId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')

        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Search Content
        search_content = kwargs.get('searchContent')
        if search_content is not None:
            if search_content and search_content.strip():
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

        result = []

        post_tag_objs = PostTag.objects.using('default').filter(tag_id__tag_name__icontains=search_content).values_list(
            'post_tag_id', 'post_id', 'tag_id')
        # print(post_tag_objs)
        post_obj_dict = {}
        for each in post_tag_objs:
            if each[1] >= 35:
                tag_name = Tag.objects.using('default').get(tag_id=each[2])
                try:
                    if tag_name in post_obj_dict.keys():
                        if len(post_obj_dict[tag_name]) < 9:
                            post_obj_dict[tag_name].append(Post.objects.using('default').get(post_id=each[1]))
                            # post_obj_list.append( Post.objects.using('default').get(post_id = each[1]))
                        else:
                            pass
                    else:

                        post_obj_dict[tag_name] = [Post.objects.using('default').get(post_id=each[1])]
                except Post.DoesNotExist:
                    pass
            else:
                pass
        # print(post_obj_dict)
        for each in post_obj_dict.items():
            # print(eac)
            # print(len(each[1]))
            result.append(SearchTagsValueType(each[0].tag_id, each[0].tag_name, each[1]))

        if len(result) > 0:
            if page and limit:
                totalPages = math.ceil(len(result) / limit)
                if page <= totalPages:
                    start = limit * (page - 1)
                    result = result[start:start + limit]

                    return SearchTagsValueListType(tags=result, page_info=PageInfoObject(
                        nextPage=page + 1 if page + 1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return SearchTagsValueListType(tags=result, page_info=PageInfoObject(nextPage=None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")

        else:
            return SearchTagsValueListType(tags=[], page_info=PageInfoObject(nextPage=None, limit=None))
    
    # Search Tags
    def resolve_searchTagsConcat(self, info, **kwargs):
        # User Id
        userId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')

        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Search Content
        search_content = kwargs.get('searchContent')
        if search_content is not None:
            if search_content and search_content.strip():
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

        result = []

        post_tag_objs = PostTag.objects.using('default').filter(tag_id__tag_name__icontains=search_content).values_list(
            'post_tag_id', 'post_id', 'tag_id')
        # print(post_tag_objs)
        post_obj_dict = {}
        for each in post_tag_objs:
            if each[1] >= 35:
                tag_name = Tag.objects.using('default').get(tag_id=each[2])
                try:
                    if tag_name in post_obj_dict.keys():
                        if len(post_obj_dict[tag_name]) < 9:
                            post_obj_dict[tag_name].append(Post.objects.using('default').get(post_id=each[1]))
                            # post_obj_list.append( Post.objects.using('default').get(post_id = each[1]))
                        else:
                            pass
                    else:

                        post_obj_dict[tag_name] = [Post.objects.using('default').get(post_id=each[1])]
                except Post.DoesNotExist:
                    pass
            else:
                pass
        # print(post_obj_dict)
        for each in post_obj_dict.items():
            # print(eac)
            # print(len(each[1]))
            result.append(SearchTagsValueType(each[0].tag_id, each[0].tag_name, each[1]))

        if len(result) > 0:
            if page and limit:
                totalPages = math.ceil(len(result) / limit)
                if page <= totalPages:
                    start = limit * (page - 1)
                    result = result[start:start + limit]

                    return result
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return result
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")

        else:
            return []

    # Search Tag Posts
    def resolve_tagPosts(self, info, **kwargs):
        # User Id
        userId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Tag Id
        tagId = kwargs.get('tagId')
        if tagId is not None:
            try:
                Tag.objects.using('default').get(tag_id=tagId)
            except Tag.DoesNotExist:
                raise NotFoundException("tagId provided is not found")
        else:
            raise BadRequestException("invalid request; tagId provided is invalid", 400)

        tag_name = Tag.objects.using('default').get(tag_id=tagId)
        post_tag_objs = PostTag.objects.using('default').filter(tag_id__tag_id=tagId).values_list('post_tag_id',
                                                                                                  'post_id', 'tag_id')
        posts = []
        for each in post_tag_objs:
            try:
                posts.append(PostListType(Post.objects.using('default').get(post_id=each[1]).post_id))
                # post_obj_list.append( Post.objects.using('default').get(post_id = each[1]))
            except Post.DoesNotExist:
                pass
        result = posts
        if len(result) > 0:
            if page and limit:
                totalPages = math.ceil(len(result) / limit)
                if page <= totalPages:
                    start = limit * (page - 1)
                    result = result[start:start + limit]

                    return SearchTagsValuePostListType(tag_id=tag_name.tag_id, hashtag=tag_name.tag_name, posts=result,
                                                       page_info=PageInfoObject(
                                                           nextPage=page + 1 if page + 1 <= totalPages else None,
                                                           limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return SearchTagsValuePostListType(tag_id=tag_name.tag_id, hashtag=tag_name.tag_name, posts=result,
                                                   page_info=PageInfoObject(nextPage=None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")

        else:
            return SearchTagsValuePostListType(tag_id=tag_name.tag_id, hashtag=tag_name.tag_name, posts=[],
                                               page_info=PageInfoObject(nextPage=None, limit=None))
        return SearchTagsValueType(tag_name.tag_id, tag_name.tag_name, posts)
    
    # Search Tag Posts
    def resolve_tagPostsConcat(self, info, **kwargs):
        # User Id
        userId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Tag Id
        tagId = kwargs.get('tagId')
        if tagId is not None:
            try:
                Tag.objects.using('default').get(tag_id=tagId)
            except Tag.DoesNotExist:
                raise NotFoundException("tagId provided is not found")
        else:
            raise BadRequestException("invalid request; tagId provided is invalid", 400)

        tag_name = Tag.objects.using('default').get(tag_id=tagId)
        post_tag_objs = PostTag.objects.using('default').filter(tag_id__tag_id=tagId).values_list('post_tag_id',
                                                                                                  'post_id', 'tag_id')
        posts = []
        for each in post_tag_objs:
            try:
                posts.append(PostListType(Post.objects.using('default').get(post_id=each[1]).post_id))
                # post_obj_list.append( Post.objects.using('default').get(post_id = each[1]))
            except Post.DoesNotExist:
                pass
        result = posts
        if len(result) > 0:
            if page and limit:
                totalPages = math.ceil(len(result) / limit)
                if page <= totalPages:
                    start = limit * (page - 1)
                    result = result[start:start + limit]

                    return result
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return result
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")

        else:
            return []
        return None

    # Search Venues
    def resolve_searchVenues(self, info, **kwargs):
        # User Id
        userId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Search Content
        search_content = kwargs.get('searchContent')
        if search_content is not None:
            if search_content and search_content.strip():
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

        result = []
        venue_internal_objs = []
        venue_external_objs = []
        venue_internal_objs = VenueInternal.objects.using('default').filter(
            venue_internal_name__icontains=search_content).values_list('venue_id', 'address_id', 'venue_type_id',
                                                                       'venue_internal_name', 'max_guests')
        # venue_external_objs = VenueExternal.objects.using('default').filter(venue_external_name__icontains= search_content).values_list('venue_id', 'location_id', 'venue_type_id', 'name', 'thumbnail', 'max_guests')


        posts = []
        for each in venue_internal_objs:
            type = VenueType.objects.using('default').get(venue_type_id=each[2]).venue_type_name
            addLoc = Address.objects.using('default').get(address_id=1)
            zip = ZipCode.objects.using('default').get(zip_code_id=addLoc.zip_code_id)
            city = City.objects.using('default').get(city_id=zip.city_id)
            state = States.objects.using('default').get(state_id=city.state_id)
            country = Country.objects.using('default').get(country_id=state.country_id)

            place_obj = PlaceObjectType(each[0], each[3], type, False,
                                        LocationObjectType(city.city_name, state.state_name, country.country_name,
                                                           city.latitude, city.longitude))
            posts = Post.objects.using('default').filter(venue_id=each[0])
            result.append(SearchPlacesValueType(place_obj, posts[:9]))


        posts = []
        # for each in venue_external_objs:
        #     type = VenueType.objects.using('default').get(venue_type_id=each[2]).venue_type_name
        #     location = Location.objects.using('default').get(location_id =each[1])
        #     print(location)
        #     place_obj = PlaceObjectType(each[0], each[3], type, True, LocationObjectType(location.city, location.state, location.country, location.latitude, location.longitude))
        #     posts = Post.objects.using('default').filter(venue_id=each[0]) 
        #     result.append(SearchPlacesValueType(place_obj,posts[:9]))
        if len(result) > 0:
            if page and limit:
                totalPages = math.ceil(len(result) / limit)
                if page <= totalPages:
                    start = limit * (page - 1)
                    result = result[start:start + limit]

                    return SearchPlacesValueListType(venues=result, page_info=PageInfoObject(
                        nextPage=page + 1 if page + 1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return SearchPlacesValueListType(venues=result, page_info=PageInfoObject(nextPage=None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")

        else:
            return SearchPlacesValueListType(venues=[], page_info=PageInfoObject(nextPage=None, limit=None))
        return result
    
    def resolve_searchVenuesConcat(self, info, **kwargs):
        # User Id
        userId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Search Content
        search_content = kwargs.get('searchContent')
        if search_content is not None:
            if search_content and search_content.strip():
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

        result = []
        venue_internal_objs = []
        venue_external_objs = []
        venue_internal_objs = VenueInternal.objects.using('default').filter(
            venue_internal_name__icontains=search_content).values_list('venue_id', 'address_id', 'venue_type_id',
                                                                       'venue_internal_name', 'max_guests')
        # venue_external_objs = VenueExternal.objects.using('default').filter(venue_external_name__icontains= search_content).values_list('venue_id', 'location_id', 'venue_type_id', 'name', 'thumbnail', 'max_guests')


        posts = []
        for each in venue_internal_objs:
            type = VenueType.objects.using('default').get(venue_type_id=each[2]).venue_type_name
            addLoc = Address.objects.using('default').get(address_id=1)
            zip = ZipCode.objects.using('default').get(zip_code_id=addLoc.zip_code_id)
            city = City.objects.using('default').get(city_id=zip.city_id)
            state = States.objects.using('default').get(state_id=city.state_id)
            country = Country.objects.using('default').get(country_id=state.country_id)

            place_obj = PlaceObjectType(each[0], each[3], type, False,
                                        LocationObjectType(city.city_name, state.state_name, country.country_name,
                                                           city.latitude, city.longitude))
            posts = Post.objects.using('default').filter(venue_id=each[0])
            result.append(SearchPlacesValueType(place_obj, posts[:9]))


        posts = []
        # for each in venue_external_objs:
        #     type = VenueType.objects.using('default').get(venue_type_id=each[2]).venue_type_name
        #     location = Location.objects.using('default').get(location_id =each[1])
        #     print(location)
        #     place_obj = PlaceObjectType(each[0], each[3], type, True, LocationObjectType(location.city, location.state, location.country, location.latitude, location.longitude))
        #     posts = Post.objects.using('default').filter(venue_id=each[0]) 
        #     result.append(SearchPlacesValueType(place_obj,posts[:9]))
        if len(result) > 0:
            if page and limit:
                totalPages = math.ceil(len(result) / limit)
                if page <= totalPages:
                    start = limit * (page - 1)
                    result = result[start:start + limit]

                    return result
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return result
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")

        else:
            return []
        return result


    # Get Search History
    def resolve_searchHistory(self, info, **kwargs):
        userId = kwargs.get('userId')
        Verification.user_verify(userId)
        client = redis_connect()
        user_search_history = {}
        result = []
        search_history_cache = get_hashmap_from_cache(client, str(userId) + "_search_history")
        if search_history_cache:
            user_search_history = json.loads(search_history_cache)
        for date_time in user_search_history:
            obj = {
                "searchTerm":user_search_history[date_time],
                "searchDate": datetime.datetime.fromtimestamp(float(date_time))
            }
            result.append(obj)
        return result

    # Delete Search History Term
    def resolve_deleteSearchHistoryTerm(self, info, **kwargs):
        userId = kwargs.get('userId')
        searchTerm = kwargs.get('searchTerm')
        Verification.user_verify(userId)
        state = Verification.searchContent_verify_redis_delete_term(searchTerm,userId)
        return stringType("successfully deleted the term" if state else "Not in cache")

    # Delete Search History Cache
    def resolve_deleteSearchHistory(self, info, **kwargs):
        userId = kwargs.get('userId')
        Verification.user_verify(userId)
        key = str(userId) + "_search_history"
        client = redis_connect()
        state = delete_routes_from_cache(client, key)
        return stringType("successfully deleted" if state else "not successful")

    # adding search keyword to cache
    def resolve_addSearchHistoryTerm(self,info,**kwargs):
        userId = kwargs.get('userId')
        searchTerm = kwargs.get('searchTerm')
        Verification.user_verify(userId)
        state = Verification.searchContent_verify_redis_add_update_term(searchTerm, userId)
        return stringType("successfully added the term" if state else "not successful")

    # Get Query Place -- Google Maps -- Places API
    def resolve_queryPlaces(self, info, **kwargs):
        userId = kwargs.get('userId')
        searchContent = kwargs.get('searchContent')
        if userId:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if searchContent:
            pass
        else:
            BadRequestException("invalid request; searchContent provided is invalid")
        api_key = 'AIzaSyA75iPmW_ZyumisbTbchYCnTal8_oRFV8M'
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        r = requests.get(url + 'query=' + searchContent + '&key=' + api_key)
        data = r.json()
        result = []

        for i in range(len(data['results'])):
            result.append(APIPlacesListType(name=data['results'][i]['name']))
        return result

    # This query will take location keyword and list out the city, states and count(priority US )

    def resolve_searchLocations(parent, info, **kwargs):
        location_keyword = kwargs.get('searchContent')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        auth_lat = kwargs.get('latitude')   #18.18027
        auth_long = kwargs.get('longitude')    #-66.75266
        country = {}
        state = {}
        city = {}
        if location_keyword is not None:
            city_objs = []
            state_objs = []
            city_results = []
            state_results = []
            country_results = []
            country_objs = []
            location_keyword = location_keyword.strip()

            try:  # Used try except block because of US country as in case if not found
                country_objs_US = Country.objects.using('default').get(country_code_two_char="US")
                city_objs += City.objects.using('default').filter(city_name__istartswith=location_keyword,
                                                                  state_id__country_id=country_objs_US.country_id).values('city_id','city_name','latitude','longitude',
                'state_id','state__country_id','state__state_name','state__state_code','state__country_id','state__country__country_name',
                'state__country__country_code_two_char','state__country__country_code_three_char')
                state_objs += States.objects.using('default').filter(state_name__istartswith=location_keyword,
                                                                     country_id=country_objs_US.country_id)

            except Country.DoesNotExist:
                raise NotFoundException("Default US country not found", 404)
            
            city_ids = []
            for each in city_objs:
                city_ids.append(each['city_id'])

            print("city_ids those in US:", city_ids)
            
            country_objs += Country.objects.using('default').filter(country_name__istartswith=location_keyword)
            state_objs += States.objects.using('default').filter(state_name__istartswith=location_keyword).exclude(
                country_id=country_objs_US.country_id)
            city_objs += City.objects.using('default').filter(city_name__istartswith=location_keyword).exclude(
                state_id__country_id=country_objs_US.country_id).values('city_id','city_name','latitude','longitude',
                'state_id','state__country_id','state__state_name','state__state_code','state__country_id','state__country__country_name',
                'state__country__country_code_two_char','state__country__country_code_three_char')
            
            # initializing the distance for each city
            distance ={}
            for each in city_objs:
                distance[each['city_id']] = -1

            #calculating distance of each city from the auth user's location
            if auth_lat is not None and auth_long is not None:
                auth_cord = (auth_lat, auth_long)
                for each in city_objs:
                    city_cord = (each['latitude'], each['longitude'])
                    distance[each['city_id']] = geopy.distance.distance(auth_cord, city_cord).miles
            # print("distance:",distance)
            
            # initializing the rel_score for each city
            rel_score = {}
            for each in city_objs:
                rel_score[each['city_id']] = 0
            # Extracting total number of venues for each city
            total_venue = {}
            for each in city_objs:
                # total_venue[each['city_id']] = VenueInternal.objects.filter(address__zip_code__city__city_id = each['city_id']).count()
                total_venue[each['city_id']] = VenueInternal.objects.filter(address__city = each['city_id']).count()
            # print("total_venue:",total_venue)
            # Extracting total number of post for each city
            total_post = {}
            for each in city_objs:
                # total_post[each['city_id']] = Post.objects.filter(venue__venueinternal__address__zip_code__city__city_id = each['city_id']).count()
                total_post[each['city_id']] = Post.objects.filter(venue__venueinternal__address__city = each['city_id']).count()
            # print("total_post:", total_post)
            
            # calculating relevency score for each city
            k = 0
            w1 =.4           # weight to set the importance of total_venues
            w2 =.2           # weight to set the importance of total_post
            for each in city_objs:
                if(distance[each['city_id']] > 0):
                    dist = (1/math.log(distance[each['city_id']]))*100
                elif(distance[each['city_id']] == 0):
                    dist = 100
                else:
                    dist = 0
                rel_score[each['city_id']] = rel_score[each['city_id']]+ total_venue[each['city_id']]  * w1 + total_post[each['city_id']] * w2 + dist
                if each['city_id'] in city_ids:
                    rel_score[each['city_id']] = rel_score[each['city_id']] + 10
                city_objs[k]['rel_score'] = rel_score[each['city_id']]
                k = k + 1    
            city_objs.sort(key=lambda item: item.get("rel_score"))
            city_objs.reverse()
            # print(city_objs) 
            #     cities.append({city: each, rel_score:rel_score[each.city_id]})
            # print("cities:",cities)
            # print("rel_score:",rel_score)
            # print(type(city_objs[0]))
            country_objs1 = locationPagination(country_objs, page, limit)
            if country_objs1['result']:
                for country in country_objs1['result']:
                    country_results.append(
                        CountryObjectType(
                            country_id=country.country_id,
                            country_name=country.country_name,
                            country_code_two_char=country.country_code_two_char,
                            country_code_three_char=country.country_code_three_char)
                    )

            state_objs1 = locationPagination(state_objs, page, limit)

            if state_objs1['result']:
                for state in state_objs1['result']:
                    state_results.append(
                        StateObjectType(
                            state_id=state.state_id,
                            state_name=state.state_name,
                            state_code=state.state_code,
                            country=CountryObjectType(
                                country_id=state.country_id,
                                country_name=state.country.country_name,
                                country_code_two_char=state.country.country_code_two_char,
                                country_code_three_char=state.country.country_code_three_char
                            )
                        )
                    )

            city_objs1 = locationPagination(city_objs, page, limit)

            if city_objs1['result']:
                for city in city_objs1['result']:
                    city_results.append(
                        CityObjectType(
                            city_id=city['city_id'],
                            rel_score = round(city['rel_score'],2),
                            city_name=city['city_name'],
                            latitude=city['latitude'],
                            longitude=city['longitude'],
                            state=StateObjectType(
                                state_id=city['state_id'],
                                state_name=city['state__state_name'],
                                state_code=city['state__state_code'],
                                country=CountryObjectType(
                                    country_id=city['state__country_id'],
                                    country_name=city['state__country__country_name'],
                                    country_code_two_char=city['state__country__country_code_two_char'],
                                    country_code_three_char=city['state__country__country_code_three_char']
                                )
                            )
                        )
                    )

            # country_page_data = locationPagination(country_results, page, limit)
            # state_page_data = locationPagination(state_results, page, limit)
            # city_page_data = locationPagination(city_results, page, limit)



            country = CountryPageListType(
                countries=country_results,
                page_info=PageInfoObject(
                    nextPage=country_objs1['page'],
                    limit=country_objs1["limit"]
                )
            )

            city = CityPageListType(
                cities=city_results,
                page_info=PageInfoObject(
                    nextPage=city_objs1["page"],
                    limit=city_objs1["limit"]
                )
            )

            state = StatePageListType(
                states=state_results,
                page_info=PageInfoObject(
                    nextPage=state_objs1["page"],
                    limit=state_objs1["limit"]
                )
            )

            return SearchLocationObjectType(
                country=country,
                state=state,
                city=city
            )

        else:  # Returning an empty data
            return SearchLocationObjectType(
                country=country,
                state=state,
                city=city
            )
    
    def resolve_searchLocationsConcat(parent, info, **kwargs):
        location_keyword = kwargs.get('searchContent')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        auth_lat = kwargs.get('latitude')   #18.18027
        auth_long = kwargs.get('longitude')    #-66.75266
        country = {}
        state = {}
        city = {}
        if location_keyword is not None:
            city_objs = []
            state_objs = []
            city_results = []
            state_results = []
            country_results = []
            country_objs = []
            location_keyword = location_keyword.strip()

            try:  # Used try except block because of US country as in case if not found
                country_objs_US = Country.objects.using('default').get(country_code_two_char="US")
                city_objs += City.objects.using('default').filter(city_name__istartswith=location_keyword,
                                                                  state_id__country_id=country_objs_US.country_id).values('city_id','city_name','latitude','longitude',
                'state_id','state__country_id','state__state_name','state__state_code','state__country_id','state__country__country_name',
                'state__country__country_code_two_char','state__country__country_code_three_char')
                state_objs += States.objects.using('default').filter(state_name__istartswith=location_keyword,
                                                                     country_id=country_objs_US.country_id)

            except Country.DoesNotExist:
                raise NotFoundException("Default US country not found", 404)
            
            city_ids = []
            for each in city_objs:
                city_ids.append(each['city_id'])

            print("city_ids those in US:", city_ids)
            
            country_objs += Country.objects.using('default').filter(country_name__istartswith=location_keyword)
            state_objs += States.objects.using('default').filter(state_name__istartswith=location_keyword).exclude(
                country_id=country_objs_US.country_id)
            city_objs += City.objects.using('default').filter(city_name__istartswith=location_keyword).exclude(
                state_id__country_id=country_objs_US.country_id).values('city_id','city_name','latitude','longitude',
                'state_id','state__country_id','state__state_name','state__state_code','state__country_id','state__country__country_name',
                'state__country__country_code_two_char','state__country__country_code_three_char')
            
            # initializing the distance for each city
            distance ={}
            for each in city_objs:
                distance[each['city_id']] = -1

            #calculating distance of each city from the auth user's location
            if auth_lat is not None and auth_long is not None:
                auth_cord = (auth_lat, auth_long)
                for each in city_objs:
                    city_cord = (each['latitude'], each['longitude'])
                    distance[each['city_id']] = geopy.distance.distance(auth_cord, city_cord).miles
            # print("distance:",distance)
            
            # initializing the rel_score for each city
            rel_score = {}
            for each in city_objs:
                rel_score[each['city_id']] = 0
            # Extracting total number of venues for each city
            total_venue = {}
            for each in city_objs:
                # total_venue[each['city_id']] = VenueInternal.objects.filter(address__zip_code__city__city_id = each['city_id']).count()
                total_venue[each['city_id']] = VenueInternal.objects.filter(address__city = each['city_id']).count()
            # print("total_venue:",total_venue)
            # Extracting total number of post for each city
            total_post = {}
            for each in city_objs:
                # total_post[each['city_id']] = Post.objects.filter(venue__venueinternal__address__zip_code__city__city_id = each['city_id']).count()
                total_post[each['city_id']] = Post.objects.filter(venue__venueinternal__address__city = each['city_id']).count()
            # print("total_post:", total_post)
            
            # calculating relevency score for each city
            k = 0
            w1 =.4           # weight to set the importance of total_venues
            w2 =.2           # weight to set the importance of total_post
            for each in city_objs:
                if(distance[each['city_id']] > 0):
                    dist = (1/math.log(distance[each['city_id']]))*100
                elif(distance[each['city_id']] == 0):
                    dist = 100
                else:
                    dist = 0
                rel_score[each['city_id']] = rel_score[each['city_id']]+ total_venue[each['city_id']]  * w1 + total_post[each['city_id']] * w2 + dist
                if each['city_id'] in city_ids:
                    rel_score[each['city_id']] = rel_score[each['city_id']] + 10
                city_objs[k]['rel_score'] = rel_score[each['city_id']]
                k = k + 1    
            city_objs.sort(key=lambda item: item.get("rel_score"))
            city_objs.reverse()
            # print(city_objs) 
            #     cities.append({city: each, rel_score:rel_score[each.city_id]})
            # print("cities:",cities)
            # print("rel_score:",rel_score)
            # print(type(city_objs[0]))
            country_objs1 = locationPagination(country_objs, page, limit)
            if country_objs1['result']:
                for country in country_objs1['result']:
                    country_results.append(
                        CountryObjectType(
                            country_id=country.country_id,
                            country_name=country.country_name,
                            country_code_two_char=country.country_code_two_char,
                            country_code_three_char=country.country_code_three_char)
                    )

            state_objs1 = locationPagination(state_objs, page, limit)

            if state_objs1['result']:
                for state in state_objs1['result']:
                    state_results.append(
                        StateObjectType(
                            state_id=state.state_id,
                            state_name=state.state_name,
                            state_code=state.state_code,
                            country=CountryObjectType(
                                country_id=state.country_id,
                                country_name=state.country.country_name,
                                country_code_two_char=state.country.country_code_two_char,
                                country_code_three_char=state.country.country_code_three_char
                            )
                        )
                    )

            city_objs1 = locationPagination(city_objs, page, limit)

            if city_objs1['result']:
                for city in city_objs1['result']:
                    city_results.append(
                        CityObjectType(
                            city_id=city['city_id'],
                            rel_score = round(city['rel_score'],2),
                            city_name=city['city_name'],
                            latitude=city['latitude'],
                            longitude=city['longitude'],
                            state=StateObjectType(
                                state_id=city['state_id'],
                                state_name=city['state__state_name'],
                                state_code=city['state__state_code'],
                                country=CountryObjectType(
                                    country_id=city['state__country_id'],
                                    country_name=city['state__country__country_name'],
                                    country_code_two_char=city['state__country__country_code_two_char'],
                                    country_code_three_char=city['state__country__country_code_three_char']
                                )
                            )
                        )
                    )

            # country_page_data = locationPagination(country_results, page, limit)
            # state_page_data = locationPagination(state_results, page, limit)
            # city_page_data = locationPagination(city_results, page, limit)

            return SearchLocationObjectConcatType(
                countries=country_results,
                states=state_results,
                cities=city_results
            )

        else:  # Returning an empty data
            return SearchLocationObjectConcatType(
                countries=[],
                states=[],
                cities=[]
            )

    # -----------------------------------Search Experiences with Filter -----------------------------------------

    def resolve_experienceResults(parent, info, **kwagrs):
        userId = kwagrs.get('userId')
        search_content = kwagrs.get('searchContent')
        city_id = kwagrs.get('location')
        search_checkin_date = kwagrs.get('startDate')
        search_checkout_date = kwagrs.get('endDate')
        filter_content = kwagrs.get('filterContent')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        search_results = []
        venue_type_id = 1
        venue_id_list = []
        cities = None
        venue_id_cities_list = []
        venue_id_dates_list = []
        venue_id_filtered_list = []
        venue_id_search_content_list = []
        venue_id_dates_price_list = []
        search_results_2 = []
        noOfPeople = 0

        # -----checking if userid given is valid user id or not -------
        Verification.user_verify(userId)

        if filter_content is not None and filter_content.get('noOfGuests') is not None:
            noOfPeople = filter_content.get('noOfGuests')
        else:
            raise BadRequestException("please enter the noOfGuests")

        # ------checking if search content is not none --------
        if search_content and search_content.strip():
            # ------------fetching venue internal ID-------------
            # venue_id_exclude_capacity_zero = ExperienceVenueOption.objects.filter(capacity=0).values_list('venue_internal_id__venue_id', flat=True)  # .annotate(price=Sum('venue_base_price'))
            venue_id_search_content_list = VenueInternal.objects.using('default').filter(
                Q(venue_internal_name__icontains=search_content, venue_type_id=venue_type_id) |
                Q(venue_internal_description__icontains=search_content, venue_type_id=venue_type_id) |
                Q(venue_internal_name__icontains=search_content, venue_internal_description__icontains=search_content, venue_type_id=venue_type_id)).values_list(
                'venue_id', flat=True)

            venue_id_list = list(set(list(venue_id_search_content_list)))

            # ------------fetching venue external ID-------------
            # venue_external_id_list = VenueExternal.objects.using('default').filter(Q(name__icontains=search_content, venue_type_id=venue_type_id )
            # |Q(venue_external_description__istartswith=search_content, venue_type_id=venue_type_id)).values_list('venue_id',flat=True)

        else:
            return SearchAllExperienceListType(
                message="Sorry , No data is found for the keyword {searchcontent}".format(searchcontent=search_content),
                experiences=[],
                page_info=PageInfoObject(
                    nextPage=None,
                    limit=None
                ))

            # ------------checking the location the city-id ------------
        if city_id is not None:
            Verification.city_verify(city_id)
            cities = City.objects.using('default').get(city_id=int(city_id))
            venue_id_cities_list = VenueInternal.objects.using('default').filter(address_id__zip_code_id__city_id = cities.city_id, venue_type_id=venue_type_id).values_list('venue_id', flat=True)
            venue_id_list = list(set(list(venue_id_search_content_list)).intersection(set(list(venue_id_cities_list))))

        # -----getting the dates in range and according to that the venue -----------------
        if search_checkin_date:
            curr_time = datetime.datetime.now()
            curr_date = curr_time.date()
            start_date = date(int(search_checkin_date.split('-')[0]), int(search_checkin_date.split('-')[1]), int(search_checkin_date.split('-')[2]))
            if start_date < curr_date:
                start_date = curr_date

            dates_in_the_range = dates_between(str(start_date.strftime("%Y-%m-%d")), search_checkout_date)
            venue_id_list_2 = getDateFilteredVenueObjects(dates_in_the_range, venue_type_id, search_checkin_date, search_checkout_date,noOfPeople,venue_id_list)
            # venue_id_list_2 = list(set(list(venue_id_list)).intersection(set(list(venue_id_dates_list))))
        else:
            venue_id_list_2 = list(set(list(venue_id_list)))

        venue_id_dates_price_list = ExpVenueOptionPrice.objects.filter(exp_venue_option_id__venue_internal_id__venue_id__in=venue_id_list_2).values('exp_venue_option_id__venue_internal_id__venue_id', 'venue_base_price')  # .annotate(price=Sum('venue_base_price'))

        for venue_id in venue_id_list_2:
            venue = VenueInternal.objects.using("default").get(venue_id=venue_id)
            price = calculateVenueStayPrice(venue, venue_id_dates_price_list)
            venue_rating = Post.objects.using('default').filter(venue_id=venue_id).values('venue_id').annotate(rating=Avg('user_rating'))
            json_obj = {
                "id" : venue_id,
                "price": str(price) if price is not None else None,
                "venue": {
                    "venue_id": venue.venue_id,
                    "venue_type_id": venue.venue_type_id,
                    "venue_type_name": VenueType.objects.using('default').get(
                        venue_type_id=venue.venue_type_id).venue_type_name
                },
                "rating": venue_rating[0].get('rating') if len(venue_rating) > 0 else None,
            }
            search_results.append(json_obj)

        if filter_content:
            input_json_filter_content = {
                "categories": filter_content.get('categories'),
                "max_price": filter_content.get('pricing', {}).get('max') if filter_content.get('pricing', {}).get('max') and filter_content.get('pricing', {}).get('max') <= 10000 else 10000,
                "min_price": filter_content.get('pricing', {}).get('min') if filter_content.get('pricing', {}).get('min') and filter_content.get('pricing', {}).get('min') >= 0 else 0,
                "rating": filter_content.get('userRatings') if filter_content.get('userRatings') and str(filter_content.get('userRatings')).strip() else "any",
                "sort_by": filter_content.get('sortBy')
            }
            one_json = filterExperienceVenueObjs(venue_type_id, search_results, input_json_filter_content,
                                                 search_content)
            for each_obj in one_json:
                search_results_2.append({"id": each_obj["id"]})
        else:
            search_results_2 = search_results

        search_results_3 = locationPagination(search_results_2, page, limit)
        return SearchAllExperienceListType(
            message="{count} records matched".format(count=str(len(search_results_2))),
            experiences=search_results_3['result'],
            page_info=PageInfoObject(
                nextPage=search_results_3['page'],
                limit=search_results_3['limit']
            ))

    def resolve_experienceResultsConcat(parent, info, **kwagrs):
        userId = kwagrs.get('userId')
        search_content = kwagrs.get('searchContent')
        city_id = kwagrs.get('location')
        search_checkin_date = kwagrs.get('startDate')
        search_checkout_date = kwagrs.get('endDate')
        filter_content = kwagrs.get('filterContent')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        search_results = []
        venue_type_id = 1
        venue_id_list = []
        cities = None
        venue_id_cities_list = []
        venue_id_dates_list = []
        venue_id_filtered_list = []
        venue_id_search_content_list = []
        venue_id_dates_price_list = []
        search_results_2 = []
        noOfPeople = 0

        # -----checking if userid given is valid user id or not -------
        Verification.user_verify(userId)

        if filter_content is not None and filter_content.get('noOfGuests') is not None:
            noOfPeople = filter_content.get('noOfGuests')
        else:
            raise BadRequestException("please enter the noOfGuests")

        # ------checking if search content is not none --------
        if search_content and search_content.strip():
            # ------------fetching venue internal ID-------------
            # venue_id_exclude_capacity_zero = ExperienceVenueOption.objects.filter(capacity=0).values_list('venue_internal_id__venue_id', flat=True)  # .annotate(price=Sum('venue_base_price'))
            venue_id_search_content_list = VenueInternal.objects.using('default').filter(
                Q(venue_internal_name__icontains=search_content, venue_type_id=venue_type_id) |
                Q(venue_internal_description__icontains=search_content, venue_type_id=venue_type_id) |
                Q(venue_internal_name__icontains=search_content, venue_internal_description__icontains=search_content, venue_type_id=venue_type_id)).values_list(
                'venue_id', flat=True)

            venue_id_list = list(set(list(venue_id_search_content_list)))

            # ------------fetching venue external ID-------------
            # venue_external_id_list = VenueExternal.objects.using('default').filter(Q(name__icontains=search_content, venue_type_id=venue_type_id )
            # |Q(venue_external_description__istartswith=search_content, venue_type_id=venue_type_id)).values_list('venue_id',flat=True)

        else:
            return SearchAllExperienceListType(
                message="Sorry , No data is found for the keyword {searchcontent}".format(searchcontent=search_content),
                experiences=[],
                page_info=PageInfoObject(
                    nextPage=None,
                    limit=None
                ))

            # ------------checking the location the city-id ------------
        if city_id is not None:
            Verification.city_verify(city_id)
            cities = City.objects.using('default').get(city_id=int(city_id))
            venue_id_cities_list = VenueInternal.objects.using('default').filter(address_id__zip_code_id__city_id = cities.city_id, venue_type_id=venue_type_id).values_list('venue_id', flat=True)
            venue_id_list = list(set(list(venue_id_search_content_list)).intersection(set(list(venue_id_cities_list))))

        # -----getting the dates in range and according to that the venue -----------------
        if search_checkin_date:
            curr_time = datetime.datetime.now()
            curr_date = curr_time.date()
            start_date = date(int(search_checkin_date.split('-')[0]), int(search_checkin_date.split('-')[1]), int(search_checkin_date.split('-')[2]))
            if start_date < curr_date:
                start_date = curr_date

            dates_in_the_range = dates_between(str(start_date.strftime("%Y-%m-%d")), search_checkout_date)
            venue_id_list_2 = getDateFilteredVenueObjects(dates_in_the_range, venue_type_id, search_checkin_date, search_checkout_date,noOfPeople,venue_id_list)
            # venue_id_list_2 = list(set(list(venue_id_list)).intersection(set(list(venue_id_dates_list))))
        else:
            venue_id_list_2 = list(set(list(venue_id_list)))

        venue_id_dates_price_list = ExpVenueOptionPrice.objects.filter(exp_venue_option_id__venue_internal_id__venue_id__in=venue_id_list_2).values('exp_venue_option_id__venue_internal_id__venue_id', 'venue_base_price')  # .annotate(price=Sum('venue_base_price'))

        for venue_id in venue_id_list_2:
            venue = VenueInternal.objects.using("default").get(venue_id=venue_id)
            price = calculateVenueStayPrice(venue, venue_id_dates_price_list)
            venue_rating = Post.objects.using('default').filter(venue_id=venue_id).values('venue_id').annotate(rating=Avg('user_rating'))
            json_obj = {
                "id" : venue_id,
                "price": str(price) if price is not None else None,
                "venue": {
                    "venue_id": venue.venue_id,
                    "venue_type_id": venue.venue_type_id,
                    "venue_type_name": VenueType.objects.using('default').get(
                        venue_type_id=venue.venue_type_id).venue_type_name
                },
                "rating": venue_rating[0].get('rating') if len(venue_rating) > 0 else None,
            }
            search_results.append(json_obj)

        if filter_content:
            input_json_filter_content = {
                "categories": filter_content.get('categories'),
                "max_price": filter_content.get('pricing', {}).get('max') if filter_content.get('pricing', {}).get('max') and filter_content.get('pricing', {}).get('max') <= 10000 else 10000,
                "min_price": filter_content.get('pricing', {}).get('min') if filter_content.get('pricing', {}).get('min') and filter_content.get('pricing', {}).get('min') >= 0 else 0,
                "rating": filter_content.get('userRatings') if filter_content.get('userRatings') and str(filter_content.get('userRatings')).strip() else "any",
                "sort_by": filter_content.get('sortBy')
            }
            one_json = filterExperienceVenueObjs(venue_type_id, search_results, input_json_filter_content,
                                                 search_content)
            for each_obj in one_json:
                search_results_2.append({"id": each_obj["id"]})
        else:
            search_results_2 = search_results

        search_results_3 = locationPagination(search_results_2, page, limit)
        return search_results_3['result']

