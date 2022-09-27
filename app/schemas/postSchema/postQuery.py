from logging import raiseExceptions
from os import stat
import pandas as pd
import graphene
from app.utilities.errors import *
from app.models import *
from app.utilities.extractWord import extract_tags_mentions
from django.db.models import Q
from app.schemas.commonObjects.objectTypes import *
from .postType import *
from app.schemas.userAccountSchema.userAccountType import *
import math
from app.schemas.searchSchema.searchType import SearchPlacesValuePostListType, LocationObjectType, PlaceObjectType
from app.utilities.pagination import pagination
from ...utilities import Verification, postVideoAnalytics
from datetime import  date, timedelta
import datetime
import mcdm

# milliseconds to video analytics time type function
def msToVideoWatchTime(watchTime):
    remainingWatchTime = int(watchTime)
    days = math.floor(remainingWatchTime/86400000)
    remainingWatchTime = remainingWatchTime % 86400000
    hours = math.floor(remainingWatchTime/3600000)
    remainingWatchTime = remainingWatchTime % 3600000
    minutes = math.floor(remainingWatchTime/60000)
    remainingWatchTime = remainingWatchTime % 60000
    seconds = round(float(remainingWatchTime)/1000, 1)
    return VideoAnalyticsTimeType(days=days, hours=hours, minutes=minutes, seconds=seconds)

class Query(graphene.ObjectType):
    # Posts Queries
    allPosts = graphene.List(PostType)
    post = graphene.Field(PostType, postId=graphene.Int(), userId=graphene.Int())
    savedPosts = graphene.Field(PostPageListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    savedPostsConcat = graphene.List(PostListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    # Comments Queries
    postComments = graphene.List(PostCommentListType, postId=graphene.Int())
    comment = graphene.Field(PostCommentType, postCommentId=graphene.Int(), authUserId=graphene.Int())
    commentReplies = graphene.Field(CommentRepliesListType, postCommentId=graphene.Int(), userId=graphene.Int(), skip=graphene.Int(), limit=graphene.Int())

    # User Profile Queries
    userPosts = graphene.Field(PostPageListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    userPostsConcat = graphene.List(PostListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    # Get Post by Places(Venue Id)
    venuePosts = graphene.Field(SearchPlacesValuePostListType, userId=graphene.Int(), venueId=graphene.String(), isExternal=graphene.Boolean(), page=graphene.Int(), limit=graphene.Int())
    venuePostsConcat = graphene.List(PostListType, userId=graphene.Int(), venueId=graphene.String(), isExternal=graphene.Boolean(), page=graphene.Int(), limit=graphene.Int())

    # Get Post by Itinerary ID
    itineraryPostsConcat = graphene.List(PostListType, userId=graphene.Int(), itineraryId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    # Video Analytics Query
    videoAnalytics = graphene.Field(VideoAnalyticsType, postId=graphene.Int())
    # Get View Source
    allViewSources = graphene.List(ViewSourceType)
    # View Retention Query
    viewRetention = graphene.Field(ViewRetentionType, postId=graphene.Int())

    # Get All Posts
    def resolve_allPosts(parent, info):
        return Post.objects.all()

    # Get Post Ids List by User Id
    def resolve_userPosts(parent, info, **kwargs):
        id = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        # if info.context.session[str(id)] == {}:
        #     raise AuthorizationException("Please login to access", 401)

        if id is not None:
            result = []
            try:
                if User.objects.using('default').get(user_id=id):
                    for i in Post.objects.using('default').filter(user_id=id).order_by('-created_on'):
                        result.append(PostListType(i.post_id))
                    result.sort(key=lambda x: x.post_id, reverse=True)
                    if len(result) > 0:
                        if page and limit:
                            totalPages = math.ceil(len(result) / limit)
                            if page <= totalPages:
                                start = limit * (page - 1)
                                result = result[start:start + limit]

                                return PostPageListType(posts=result, page_info=PageInfoObject(nextPage=page + 1 if page + 1 <= totalPages else None, limit=limit))
                            else:
                                raise BadRequestException("invalid request; page provided exceeded total")
                        elif page == limit == None:
                            return PostPageListType(posts=result, page_info=PageInfoObject(nextPage=None, limit=None))
                        elif page is None:
                            raise BadRequestException("invalid request; limit cannot be provided without page")
                        elif limit is None:
                            raise BadRequestException("invalid request; page cannot be provided without limit")

                    else:
                        return PostPageListType(posts=[], page_info=PageInfoObject(nextPage=None, limit=None))

                    # else:
                    #     raise NotFoundException("post does not exist", 204) 
            except (User.DoesNotExist, Post.DoesNotExist):
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        return None
    
    # Get Post Ids List by User Id
    def resolve_userPostsConcat(parent, info, **kwargs):
        id = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        # if info.context.session[str(id)] == {}:
        #     raise AuthorizationException("Please login to access", 401)

        if id is not None:
            result = []
            try:
                if User.objects.using('default').get(user_id=id):
                    for i in Post.objects.using('default').filter(user_id=id).order_by('-created_on'):
                        result.append(PostListType(i.post_id))
                    result.sort(key=lambda x: x.post_id, reverse=True)
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

                    # else:
                    #     raise NotFoundException("post does not exist", 204) 
            except (User.DoesNotExist, Post.DoesNotExist):
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        return None

    # Get Post By Id
    def resolve_post(parent, info, **kwargs):
        userId = kwargs.get('userId')
        id = kwargs.get('postId')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if id is not None:
            try:
                if Post.objects.using('default').get(post_id=id):
                    result = Post.objects.using('default').filter(post_id=id).values()
                    post = result[0]
                    isLiked = False
                    post['isLiked'] = None
                    try:
                        post_liked = PostLike.objects.using('default').get(Q(post_id=id) & Q(user_id=userId))
                        isLiked = True
                    except PostLike.DoesNotExist:
                        isLiked = False
                    post['isLiked'] = isLiked
                    isSaved = False
                    post['isSaved'] = None
                    try:
                        post_saved = PostSaved.objects.using('default').get(Q(post_id=id) & Q(user_id=userId))
                        isSaved = True
                    except PostSaved.DoesNotExist:
                        isSaved = False
                    post['isSaved'] = isSaved
                    return post
            except Post.DoesNotExist:
                raise NotFoundException('postId provided not found', 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)
        return None
    
    

    # Get Comments By Post Id
    def resolve_postComments(parent, info, **kwagrs):
        id = kwagrs.get('postId')
        if id is not None:
            comments = []
            try:
                post = Post.objects.using('default').get(post_id=id)

                for each in PostComment.objects.using('default').filter(post_id=id):
                    if each.comment_reply_id:
                        pass
                    else:
                        comments.append(PostCommentListType(each.post_comment_id))  # , user_output_obj, each.comment, each.number_of_likes,  each.date_created, len(reply_comment_output_obj), reply_comment_output_obj, hashtags, mentions))
                # comments.sort(key=lambda x:x.date_created, reverse=True)
                return comments
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

    # Get Comments By Post Comment Id
    def resolve_comment(parent, info, **kwagrs):
        id = kwagrs.get('postCommentId')
        authUserId = kwagrs.get('authUserId')

        if id is not None:
            if authUserId:
                try:
                    User.objects.using('default').get(user_id=authUserId)
                except User.DoesNotExist:
                    raise NotFoundException("authUserId provided not found", 404)
            else:
                raise BadRequestException("invalid request; authUserId provided is invalid", 400)
            comments = {}
            hashtags_word, hashtags = [], []
            mentions_word, mentions = [], []
            postIsLiked = False
            try:
                each = PostComment.objects.using('default').get(post_comment_id=id)
                try:
                    postLike = PostCommentLike.objects.using('default').get(post_comment_id=id, user_id=authUserId)
                    print(postLike)
                    postIsLiked = True
                except PostCommentLike.DoesNotExist:
                    print("exception")
                    postIsLiked = False
                # for each in PostComment.objects.using('default').filter(post_id=id):
                reply_comment_output_obj = []
                user_obj = User.objects.using('default').get(user_id=each.user_id)
                user_output_obj = OutputUserType(user_obj.user_id, user_obj.username, user_obj.avatar, user_obj.level)
                reply_comment_objs = []
                reply_comment_objs += PostComment.objects.using('default').filter(comment_reply_id=id).values_list('post_comment_id', flat=True)
                print(reply_comment_objs)
                if reply_comment_objs != []:
                    for each_reply in reply_comment_objs:
                        # each_reply_obj = PostComment.objects.using('default').get(post_comment_id=each_reply)
                        reply_comment_output_obj.append(PostCommentReplyType(each_reply))
                    print(reply_comment_output_obj)
                elif reply_comment_objs == []:
                    reply_comment_output_obj = []
                    # if each.comment_reply_id == None:
                    # Get Hashtags and Mentions
                    hashtags_word, hashtags = [], []
                    mentions_word, mentions = [], []
                    hashtags_word, mentions_word = extract_tags_mentions(each.comment)
                    for one_hashtag in hashtags_word:
                        try:
                            tag_obj = Tag.objects.using('default').get(tag_name=one_hashtag)
                            hashtags.append(hashtagSection(tag_obj.tag_name, tag_obj.tag_id))
                        except Tag.DoesNotExist:
                            pass
                    for one_mention in mentions_word:
                        try:
                            user = User.objects.using('default').get(username=one_mention)                  
                            mentions.append(mentionSection(user.username, user.user_id))
                        except User.DoesNotExist:
                            pass
                            # mentions.append(mentionSection(one_mention, None))
                number_of_likes = PostCommentLike.objects.using('default').filter(post_comment_id=id).values_list('post_comment_id', flat=True)
                comments = PostCommentType(each.post_comment_id, user_output_obj, each.comment, aggregateObjectType(aggregate=aggregate(count=len(number_of_likes))), each.created_on, aggregateObjectType(aggregate=aggregate(count=len(reply_comment_output_obj))), reply_comment_output_obj if len(reply_comment_output_obj) >= 1 else None, hashtags, mentions, postIsLiked, False if len(reply_comment_output_obj) >= 1 else True)

                # comments.sort(key=lambda x:x.date_created, reverse=True)
                return comments
            except PostComment.DoesNotExist:
                raise NotFoundException("postCommentId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postCommentId provided is invalid", 400)

    # Get Saved Posts
    def resolve_savedPosts(parent, info, **kwagrs):
        id = kwagrs.get('userId')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if id is not None:
            result = []
            post_ids = []
            try:
                if User.objects.using('default').get(user_id=id):
                    post_ids += PostSaved.objects.using('default').filter(user_id=id).values_list('post_id')
                    post_ids = [i[0] for i in post_ids]
                    for i in Post.objects.using('default').filter(post_id__in=post_ids).order_by('-created_on'):
                        result.append(PostListType(i.post_id))
                        # result.append(i)
                    result.sort(key=lambda x: x.post_id, reverse=True)
                    # return result
                    if len(result) > 0:
                        if page and limit:
                            totalPages = math.ceil(len(result) / limit)
                            if page <= totalPages:
                                start = limit * (page - 1)
                                result = result[start:start + limit]

                                return PostPageListType(posts=result, page_info=PageInfoObject(nextPage=page + 1 if page + 1 <= totalPages else None, limit=limit))
                            else:
                                raise BadRequestException("invalid request; page provided exceeded total")
                        elif page == limit == None:
                            return PostPageListType(posts=result, page_info=PageInfoObject(nextPage=None, limit=None))
                        elif page is None:
                            raise BadRequestException("invalid request; limit cannot be provided without page")
                        elif limit is None:
                            raise BadRequestException("invalid request; page cannot be provided without limit")

                    else:
                        return PostPageListType(posts=[], page_info=PageInfoObject(nextPage=None, limit=None))
                    # else:
                    #     raise NotFoundException("post does not exist", 204) 
            except (User.DoesNotExist):
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        return None
    
    # Get Saved Posts Concat
    def resolve_savedPostsConcat(parent, info, **kwagrs):
        id = kwagrs.get('userId')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if id is not None:
            result = []
            post_ids = []
            try:
                if User.objects.using('default').get(user_id=id):
                    post_ids += PostSaved.objects.using('default').filter(user_id=id).values_list('post_id')
                    post_ids = [i[0] for i in post_ids]
                    for i in Post.objects.using('default').filter(post_id__in=post_ids).order_by('-created_on'):
                        result.append(PostListType(i.post_id))
                        # result.append(i)
                    result.sort(key=lambda x: x.post_id, reverse=True)
                    # return result
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
                    # else:
                    #     raise NotFoundException("post does not exist", 204) 
            except (User.DoesNotExist):
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        return None

    # Search Venue Posts
    def resolve_venuePosts(self, info, **kwargs):
        # User Id
        userId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        isExternal = kwargs.get('isExternal')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Venue Id
        venueId = kwargs.get('venueId')
        if venueId is not None:
            try:
                Venue.objects.using('default').get(venue_id=venueId)
            except Venue.DoesNotExist:
                raise NotFoundException("venueId provided is not found")
        else:
            raise BadRequestException("invalid request; venueId provided is invalid", 400)
        # is_external

        if isExternal is not None:
            if not isExternal:
                try:
                    venue_obj = VenueInternal.objects.using('default').get(venue_id=venueId)
                except VenueInternal.DoesNotExist:
                    raise BadRequestException("invalid request; venueId provided doesnt correspond with isExternal field")
            else:
                try:
                    venue_obj = VenueExternal.objects.using('default').get(venue_id=venueId)
                except VenueExternal.DoesNotExist:
                    raise BadRequestException("invalid request; venueId provided doesnt correspond with isExternal field")
        else:
            raise BadRequestException("invalid request; isExternal provided provided is invalid", 400)

        type = VenueType.objects.using('default').get(venue_type_id=venue_obj.venue_type_id).venue_type_name
        cityName = None
        stateName = None
        countryName = None
        latitude = None
        longitude = None
        if venue_obj.address_id is not None:
            address = Address.objects.using('default').get(address_id=venue_obj.address_id)
            # zipCode = ZipCode.objects.using('default').get(zip_code_id=1)
            city = City.objects.using('default').get(city_id=address.city_id)
            state = States.objects.using('default').get(state_id=city.state_id)
            country = Country.objects.using('default').get(country_id=state.country_id)
            cityName = city.city_name
            stateName = state.state_name
            countryName = country.country_name
            latitude = city.latitude
            longitude = city.longitude
        place_obj = PlaceObjectType(venue_obj.venue_id, venue_obj.venue_internal_name, type, isExternal, LocationObjectType(cityName, stateName, countryName, latitude, longitude))
        posts = []

        # Extracting post_ids for the given venue 
        posts += Post.objects.using('default').filter(venue_id =venueId).values_list('post_id',flat = True)
        
        if len(posts) > 0:

            end = datetime.datetime.now()
            start = end -timedelta(days=10)

        
            totalRewatch = {}
            perTotalWatchComplete = {}

        

            # Total number of bookings using post - Lifetime and Trending
            dfBookingPurchaseLifetime = pd.DataFrame(list(UserTrip.objects.using('default').filter(referred_post__in = posts).values('referred_post','created_on')))
            if dfBookingPurchaseLifetime.empty:
                dfBookingPurchaseLifetime = pd.DataFrame(columns=['referred_post','created_on'])
            bookingPurchaseCountLifetimeSeries = dfBookingPurchaseLifetime['referred_post'].value_counts()
            dfBookingPurchaseLifetime['created_on'] = pd.to_datetime(dfBookingPurchaseLifetime.created_on).dt.tz_localize(None)
            dfBookingPurchaseTrending = dfBookingPurchaseLifetime[(start <= dfBookingPurchaseLifetime['created_on'])]
            bookingPurchaseCountTrendingSeries = dfBookingPurchaseTrending['referred_post'].value_counts()

            # Total number of post_view count - Lifetime and Trending
            dfPostViewLifetime = pd.DataFrame(list(PostView.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostViewLifetime.empty:
                dfPostViewLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postViewCountLifetimeSeries = dfPostViewLifetime['post_id'].value_counts()
            dfPostViewLifetime['created_on'] = pd.to_datetime(dfPostViewLifetime.created_on).dt.tz_localize(None)
            dfPostViewTrending = dfPostViewLifetime[(start <= dfPostViewLifetime['created_on'])]
            postViewCountTrendingSeries = dfPostViewTrending['post_id'].value_counts()

            # Total number of post_like count - Lifetime    and Trending
            dfPostLikeLifetime = pd.DataFrame(list(PostLike.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostLikeLifetime.empty:
                dfPostLikeLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postLikeCountLifetimeSeries = dfPostLikeLifetime['post_id'].value_counts()
            dfPostLikeLifetime['created_on'] = pd.to_datetime(dfPostLikeLifetime.created_on).dt.tz_localize(None)
            dfPostLikeTrending = dfPostLikeLifetime[(start <= dfPostLikeLifetime['created_on'])]
            postLikeCountTrendingSeries = dfPostLikeTrending['post_id'].value_counts()

            # Total number of post_comment count - Lifetime
            dfPostCommentLifetime = pd.DataFrame(list(PostComment.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostCommentLifetime.empty:
                dfPostCommentLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postCommentCountLifetimeSeries = dfPostCommentLifetime['post_id'].value_counts()

            # Total number of post_Saved count - Lifetime
            dfPostSavedLifetime = pd.DataFrame(list(PostSaved.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostSavedLifetime.empty:
                dfPostSavedLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postSavedCountLifetimeSeries = dfPostSavedLifetime['post_id'].value_counts()

            # Total number of post shared count - Lifetime
            dfPostSharedLifetime = pd.DataFrame(list(Shared.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostSharedLifetime.empty:
                dfPostSharedLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postSharedCountLifetimeSeries = dfPostSharedLifetime['post_id'].value_counts()

            # Total number of post click through count - Lifetime
            dfPostVenueClickLifetime = pd.DataFrame(list(PostVenueClick.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostVenueClickLifetime.empty:
                dfPostVenueClickLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postVenueClickCountLifetimeSeries = dfPostVenueClickLifetime['post_id'].value_counts()
        
            postFeatureList = []
            BIAS = 1
            for each in posts:
                tempFeatureList = []
                
                if each in bookingPurchaseCountLifetimeSeries.index:
                    tempFeatureList.append(bookingPurchaseCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in bookingPurchaseCountTrendingSeries.index:
                    tempFeatureList.append(bookingPurchaseCountTrendingSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postViewCountLifetimeSeries.index:
                    tempFeatureList.append(postViewCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)
                
                if each in postViewCountTrendingSeries.index:
                    tempFeatureList.append(postViewCountTrendingSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postLikeCountLifetimeSeries.index:
                    tempFeatureList.append(postLikeCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postLikeCountTrendingSeries.index:
                    tempFeatureList.append(postLikeCountTrendingSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postCommentCountLifetimeSeries.index:
                    tempFeatureList.append(postCommentCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postSavedCountLifetimeSeries.index:
                    tempFeatureList.append(postSavedCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postSharedCountLifetimeSeries.index:
                    tempFeatureList.append(postSharedCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postVenueClickCountLifetimeSeries.index:
                    tempFeatureList.append(postVenueClickCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if (each in postVenueClickCountLifetimeSeries.index) and (each in postViewCountLifetimeSeries.index):
                    tempFeatureList.append(postVenueClickCountLifetimeSeries[each]/postViewCountLifetimeSeries[each]) # Click count and view count ratio
                else:
                    tempFeatureList.append(BIAS)

                if (each in postLikeCountLifetimeSeries.index) and (each in postViewCountLifetimeSeries.index):
                    tempFeatureList.append(postLikeCountLifetimeSeries[each]/postViewCountLifetimeSeries[each]) # Like count and view count ratio
                else:
                    tempFeatureList.append(BIAS)

                # total rewatch and percentage of watch complete
                watchObj = postVideoAnalytics.videoAnalytics(each)
                totalRewatch[each] = watchObj.views
                perTotalWatchComplete[each] = watchObj.percent_watch_full
                
                tempFeatureList.append(totalRewatch[each])
                tempFeatureList.append(perTotalWatchComplete[each]+1)

                postFeatureList.append(tempFeatureList)
                
            BOOKING_PURCHASE_COUNT_LIFETIME_WEIGHT = 0.1
            BOOKING_PURCHASE_COUNT_TRENDING_WEIGHT = 0.1
            POST_VIEW_COUNT_LIFETIME_WEIGHT = 0.1
            POST_VIEW_COUNT_TRENDING_WEIGHT =0.1
            POST_LIKE_COUNT_LIFETIME_WEIGHT = 0.05
            POST_LIKE_COUNT_TRENDING_WEIGHT = 0.05
            POST_COMMENT_COUNT_LIFETIME_WEIGHT = 0.05
            POST_SAVED_COUNT_LIFETIME_WEIGHT = 0.05
            POST_VENUE_CLICK_COUNT_LIFETIME_WEIGHT = 0.1
            CLICK_THROUGH_VIEWS_RATIO_WEIGHT = 0.1
            POST_SHARED_COUNT_LIFETIME_WEIGHT =0.05
            LIKE_VIEW_RATIO_WEIGHT = 0.05
            TOTAL_REWATCH_WEIGHT = 0.05
            PER_TOTAL_WATCH_COMPLETE_WEIGHT = 0.05
            # Creating weight vector
            w_vector = [BOOKING_PURCHASE_COUNT_LIFETIME_WEIGHT,
                            BOOKING_PURCHASE_COUNT_TRENDING_WEIGHT,
                                POST_VIEW_COUNT_LIFETIME_WEIGHT,
                                    POST_VIEW_COUNT_TRENDING_WEIGHT,
                                        POST_LIKE_COUNT_LIFETIME_WEIGHT,
                                            POST_LIKE_COUNT_TRENDING_WEIGHT,
                                                POST_COMMENT_COUNT_LIFETIME_WEIGHT,
                                                    POST_SAVED_COUNT_LIFETIME_WEIGHT,
                                                           POST_SHARED_COUNT_LIFETIME_WEIGHT,
                                                              POST_VENUE_CLICK_COUNT_LIFETIME_WEIGHT,
                                                                  CLICK_THROUGH_VIEWS_RATIO_WEIGHT,
                                                                    LIKE_VIEW_RATIO_WEIGHT,
                                                                        TOTAL_REWATCH_WEIGHT,
                                                                            PER_TOTAL_WATCH_COMPLETE_WEIGHT]
            
            # applying multi-criteria decision making algorithm named as Multiplicative Exponential weighting.
            if(len(postFeatureList)>0):
                postRank = mcdm.rank(postFeatureList, alt_names=posts, n_method="Linear1", w_vector=w_vector, s_method="MEW")
            else:
                postRank = []
            
            # adding results
            result =[]
            for each in postRank:
                result.append(PostListType(each[0],round(each[1],2)))
        else:
            result = []
        # result = []
        flag, page_data = pagination(result, page, limit)
        if flag:
            return SearchPlacesValuePostListType(venue=place_obj, posts=page_data["result"], page_info=PageInfoObject(
                nextPage=page_data["page"], limit=page_data["limit"]))
        else:
            raise BadRequestException(page_data)

        # return SearchPlacesValueType(place_obj,posts)
    
    # Search Venue Posts
    def resolve_venuePostsConcat(self, info, **kwargs):
        # User Id
        userId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        isExternal = kwargs.get('isExternal')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        # Venue Id
        venueId = kwargs.get('venueId')
        if venueId is not None:
            try:
                Venue.objects.using('default').get(venue_id=venueId)
            except Venue.DoesNotExist:
                raise NotFoundException("venueId provided is not found")
        else:
            raise BadRequestException("invalid request; venueId provided is invalid", 400)
        # is_external

        if isExternal is not None:
            if not isExternal:
                try:
                    venue_obj = VenueInternal.objects.using('default').get(venue_id=venueId)
                except VenueInternal.DoesNotExist:
                    raise BadRequestException("invalid request; venueId provided doesnt correspond with isExternal field")
            else:
                try:
                    venue_obj = VenueExternal.objects.using('default').get(venue_id=venueId)
                except VenueExternal.DoesNotExist:
                    raise BadRequestException("invalid request; venueId provided doesnt correspond with isExternal field")
        else:
            raise BadRequestException("invalid request; isExternal provided provided is invalid", 400)

        type = VenueType.objects.using('default').get(venue_type_id=venue_obj.venue_type_id).venue_type_name
        cityName = None
        stateName = None
        countryName = None
        latitude = None
        longitude = None
        if venue_obj.address_id is not None:
            address = Address.objects.using('default').get(address_id=venue_obj.address_id)
            # zipCode = ZipCode.objects.using('default').get(zip_code_id=1)
            city = City.objects.using('default').get(city_id=address.city_id)
            state = States.objects.using('default').get(state_id=city.state_id)
            country = Country.objects.using('default').get(country_id=state.country_id)
            cityName = city.city_name
            stateName = state.state_name
            countryName = country.country_name
            latitude = city.latitude
            longitude = city.longitude
        place_obj = PlaceObjectType(venue_obj.venue_id, venue_obj.venue_internal_name, type, isExternal, LocationObjectType(cityName, stateName, countryName, latitude, longitude))
        posts = []

        # Extracting post_ids for the given venue 
        posts += Post.objects.using('default').filter(venue_id =venueId).values_list('post_id',flat = True)
        
        if len(posts) > 0:

            end = datetime.datetime.now()
            start = end -timedelta(days=10)

        
            totalRewatch = {}
            perTotalWatchComplete = {}

        

            # Total number of bookings using post - Lifetime and Trending
            dfBookingPurchaseLifetime = pd.DataFrame(list(UserTrip.objects.using('default').filter(referred_post__in = posts).values('referred_post','created_on')))
            if dfBookingPurchaseLifetime.empty:
                dfBookingPurchaseLifetime = pd.DataFrame(columns=['referred_post','created_on'])
            bookingPurchaseCountLifetimeSeries = dfBookingPurchaseLifetime['referred_post'].value_counts()
            dfBookingPurchaseLifetime['created_on'] = pd.to_datetime(dfBookingPurchaseLifetime.created_on).dt.tz_localize(None)
            dfBookingPurchaseTrending = dfBookingPurchaseLifetime[(start <= dfBookingPurchaseLifetime['created_on'])]
            bookingPurchaseCountTrendingSeries = dfBookingPurchaseTrending['referred_post'].value_counts()

            # Total number of post_view count - Lifetime and Trending
            dfPostViewLifetime = pd.DataFrame(list(PostView.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostViewLifetime.empty:
                dfPostViewLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postViewCountLifetimeSeries = dfPostViewLifetime['post_id'].value_counts()
            dfPostViewLifetime['created_on'] = pd.to_datetime(dfPostViewLifetime.created_on).dt.tz_localize(None)
            dfPostViewTrending = dfPostViewLifetime[(start <= dfPostViewLifetime['created_on'])]
            postViewCountTrendingSeries = dfPostViewTrending['post_id'].value_counts()

            # Total number of post_like count - Lifetime    and Trending
            dfPostLikeLifetime = pd.DataFrame(list(PostLike.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostLikeLifetime.empty:
                dfPostLikeLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postLikeCountLifetimeSeries = dfPostLikeLifetime['post_id'].value_counts()
            dfPostLikeLifetime['created_on'] = pd.to_datetime(dfPostLikeLifetime.created_on).dt.tz_localize(None)
            dfPostLikeTrending = dfPostLikeLifetime[(start <= dfPostLikeLifetime['created_on'])]
            postLikeCountTrendingSeries = dfPostLikeTrending['post_id'].value_counts()

            # Total number of post_comment count - Lifetime
            dfPostCommentLifetime = pd.DataFrame(list(PostComment.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostCommentLifetime.empty:
                dfPostCommentLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postCommentCountLifetimeSeries = dfPostCommentLifetime['post_id'].value_counts()

            # Total number of post_Saved count - Lifetime
            dfPostSavedLifetime = pd.DataFrame(list(PostSaved.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostSavedLifetime.empty:
                dfPostSavedLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postSavedCountLifetimeSeries = dfPostSavedLifetime['post_id'].value_counts()

            # Total number of post shared count - Lifetime
            dfPostSharedLifetime = pd.DataFrame(list(Shared.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostSharedLifetime.empty:
                dfPostSharedLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postSharedCountLifetimeSeries = dfPostSharedLifetime['post_id'].value_counts()

            # Total number of post click through count - Lifetime
            dfPostVenueClickLifetime = pd.DataFrame(list(PostVenueClick.objects.using('default').filter(post_id__in = posts).values('post_id','created_on')))
            if dfPostVenueClickLifetime.empty:
                dfPostVenueClickLifetime = pd.DataFrame(columns=['post_id','created_on'])
            postVenueClickCountLifetimeSeries = dfPostVenueClickLifetime['post_id'].value_counts()
        
            postFeatureList = []
            BIAS = 1
            for each in posts:
                tempFeatureList = []
                
                if each in bookingPurchaseCountLifetimeSeries.index:
                    tempFeatureList.append(bookingPurchaseCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in bookingPurchaseCountTrendingSeries.index:
                    tempFeatureList.append(bookingPurchaseCountTrendingSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postViewCountLifetimeSeries.index:
                    tempFeatureList.append(postViewCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)
                
                if each in postViewCountTrendingSeries.index:
                    tempFeatureList.append(postViewCountTrendingSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postLikeCountLifetimeSeries.index:
                    tempFeatureList.append(postLikeCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postLikeCountTrendingSeries.index:
                    tempFeatureList.append(postLikeCountTrendingSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postCommentCountLifetimeSeries.index:
                    tempFeatureList.append(postCommentCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postSavedCountLifetimeSeries.index:
                    tempFeatureList.append(postSavedCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postSharedCountLifetimeSeries.index:
                    tempFeatureList.append(postSharedCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if each in postVenueClickCountLifetimeSeries.index:
                    tempFeatureList.append(postVenueClickCountLifetimeSeries[each]+BIAS)
                else:
                    tempFeatureList.append(BIAS)

                if (each in postVenueClickCountLifetimeSeries.index) and (each in postViewCountLifetimeSeries.index):
                    tempFeatureList.append(postVenueClickCountLifetimeSeries[each]/postViewCountLifetimeSeries[each]) # Click count and view count ratio
                else:
                    tempFeatureList.append(BIAS)

                if (each in postLikeCountLifetimeSeries.index) and (each in postViewCountLifetimeSeries.index):
                    tempFeatureList.append(postLikeCountLifetimeSeries[each]/postViewCountLifetimeSeries[each]) # Like count and view count ratio
                else:
                    tempFeatureList.append(BIAS)

                # total rewatch and percentage of watch complete
                watchObj = postVideoAnalytics.videoAnalytics(each)
                totalRewatch[each] = watchObj.views
                perTotalWatchComplete[each] = watchObj.percent_watch_full
                
                tempFeatureList.append(totalRewatch[each])
                tempFeatureList.append(perTotalWatchComplete[each]+1)

                postFeatureList.append(tempFeatureList)
                
            BOOKING_PURCHASE_COUNT_LIFETIME_WEIGHT = 0.1
            BOOKING_PURCHASE_COUNT_TRENDING_WEIGHT = 0.1
            POST_VIEW_COUNT_LIFETIME_WEIGHT = 0.1
            POST_VIEW_COUNT_TRENDING_WEIGHT =0.1
            POST_LIKE_COUNT_LIFETIME_WEIGHT = 0.05
            POST_LIKE_COUNT_TRENDING_WEIGHT = 0.05
            POST_COMMENT_COUNT_LIFETIME_WEIGHT = 0.05
            POST_SAVED_COUNT_LIFETIME_WEIGHT = 0.05
            POST_VENUE_CLICK_COUNT_LIFETIME_WEIGHT = 0.1
            CLICK_THROUGH_VIEWS_RATIO_WEIGHT = 0.1
            POST_SHARED_COUNT_LIFETIME_WEIGHT =0.05
            LIKE_VIEW_RATIO_WEIGHT = 0.05
            TOTAL_REWATCH_WEIGHT = 0.05
            PER_TOTAL_WATCH_COMPLETE_WEIGHT = 0.05
            # Creating weight vector
            w_vector = [BOOKING_PURCHASE_COUNT_LIFETIME_WEIGHT,
                            BOOKING_PURCHASE_COUNT_TRENDING_WEIGHT,
                                POST_VIEW_COUNT_LIFETIME_WEIGHT,
                                    POST_VIEW_COUNT_TRENDING_WEIGHT,
                                        POST_LIKE_COUNT_LIFETIME_WEIGHT,
                                            POST_LIKE_COUNT_TRENDING_WEIGHT,
                                                POST_COMMENT_COUNT_LIFETIME_WEIGHT,
                                                    POST_SAVED_COUNT_LIFETIME_WEIGHT,
                                                           POST_SHARED_COUNT_LIFETIME_WEIGHT,
                                                              POST_VENUE_CLICK_COUNT_LIFETIME_WEIGHT,
                                                                  CLICK_THROUGH_VIEWS_RATIO_WEIGHT,
                                                                    LIKE_VIEW_RATIO_WEIGHT,
                                                                        TOTAL_REWATCH_WEIGHT,
                                                                            PER_TOTAL_WATCH_COMPLETE_WEIGHT]
            
            # applying multi-criteria decision making algorithm named as Multiplicative Exponential weighting.
            if(len(postFeatureList)>0):
                postRank = mcdm.rank(postFeatureList, alt_names=posts, n_method="Linear1", w_vector=w_vector, s_method="MEW")
            else:
                postRank = []
            
            # adding results
            result =[]
            for each in postRank:
                result.append(PostListType(each[0],round(each[1],2)))
        else:
            result = []
        # result = []
        # flag, page_data = pagination(result, page, limit)
        # if flag:
        #     return SearchPlacesValuePostListType(venue=place_obj, posts=page_data["result"], page_info=PageInfoObject(
        #         nextPage=page_data["page"], limit=page_data["limit"]))
        # else:
        #     raise BadRequestException(page_data)

        flag, page_data = pagination(result, page, limit)
        if flag:
            return page_data['result']
        else:
            raise BadRequestException(page_data)


    # fetching replies for a comment
    def resolve_commentReplies(parent, info, **kwargs):
        userId = kwargs.get('userId')
        postCommentId = kwargs.get('postCommentId')
        skip = kwargs.get('skip')
        limit = kwargs.get('limit')
        commentReplies = []
        Verification.user_verify(userId)
        Verification.post_comment_verify(postCommentId)
        postCommentId_1 = postCommentId

        postCommentIds = list(PostComment.objects.using("default").filter(comment_reply=postCommentId_1).order_by('-created_on').values_list('post_comment_id', flat=True))
        for postComment_Id in postCommentIds:
            commentReplies.append(CommentReply(postCommentId=postComment_Id))
        # print(reply_id)
        # if len(reply_id) > 0 and reply_id[0] is not None:
        #     print("hello")
        #     commentReplies.append(CommentReply(postCommentId=reply_id[0]))
        #     postCommentId_1 = reply_id[0]
        # else:
        #     postCommentId_1 = None
        data = None
        if len(list(commentReplies)) > 0:
            if skip is None and limit is None:
                commentReplies = list(commentReplies)
                data = CommentRepliesListType(
                    postCommentReplies=commentReplies,
                    postCommentId=postCommentId
                )
            elif skip is None and limit is not None:
                if limit <= len(list(commentReplies)):
                    data = CommentRepliesListType(
                        postCommentReplies=list(commentReplies)[0:limit],
                        postCommentId=postCommentId
                    )
                elif limit > len(list(commentReplies)):
                    data = CommentRepliesListType(
                        postCommentReplies=list(commentReplies),
                        postCommentId=postCommentId
                    )

            elif skip is not None and limit is None:
                if skip <= len(list(commentReplies)):
                    data = CommentRepliesListType(
                        postCommentReplies=list(commentReplies)[skip:len(list(commentReplies))],
                        postCommentId=postCommentId
                    )
                elif skip > len(list(commentReplies)):
                    data = CommentRepliesListType(
                        postCommentReplies=[],
                        postCommentId=postCommentId
                    )

            if skip is not None and limit is not None:
                if skip <= len(list(commentReplies)) and limit <= len(list(commentReplies)) and len(list(commentReplies)) >= skip + limit:
                    data = CommentRepliesListType(
                        postCommentReplies=list(commentReplies)[skip: skip + limit],
                        postCommentId=postCommentId
                    )

                elif (skip <= len(list(commentReplies)) < skip + limit and limit <= len(list(commentReplies))) or skip <= len(list(commentReplies)) < limit:
                    data = CommentRepliesListType(
                        postCommentReplies=list(commentReplies)[skip: len(list(commentReplies))],
                        postCommentId=postCommentId
                    )

                else:
                    data = CommentRepliesListType(
                        postCommentReplies=[],
                        postCommentId=postCommentId
                    )

        else:
            data = CommentRepliesListType(
                postCommentReplies=[],
                postCommentId=postCommentId
            )
        return data

    # video analytics API
    def resolve_videoAnalytics(self, info, **kwargs):
        postId = kwargs.get('postId')
        VideoAnalyticsTypeObj = postVideoAnalytics.videoAnalytics(postId)
        return VideoAnalyticsTypeObj
        
        # ensures the post actually exists
    def resolve_allViewSources(self, info, **kwargs):
        return ViewSource.objects.all()
    
    def resolve_viewRetention(self, info, **kwargs):
        postId = kwargs.get('postId')
        
        # checks if the post actually exist
        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided is not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)
        
        retentionIntervals = []
        retentionsPercentages = []

        try:
            impressions = PostView.objects.using('default').filter(post_id=postId)
            videoLen = impressions[0].video_duration
            # creates video retention intervals
            for i in range(0, videoLen, 1000):
                retentionIntervals.append(i)
            retentionIntervals.append(videoLen)
            # creates an array of all views
            viewLengths = []
            nonSelfViews = 0
            for impression in impressions:
                # excludes uploader from retention data
                if (post.user_id == impression.user_id):
                    continue
                watchTimeDT = impression.video_end_time - impression.video_start_time
                watchTime = (watchTimeDT.days*1000*3600*24) + (watchTimeDT.seconds*1000) + (watchTimeDT.microseconds/1000)
                viewLengths.append(watchTime)
                nonSelfViews += 1

            for interval in retentionIntervals:
                retained = 0
                for viewLen in viewLengths:
                    if (viewLen >= interval):
                        retained += 1
                retentionsPercentages.append(round((float(retained)/nonSelfViews) * 100))

        except PostView.DoesNotExist:
            pass
        
        return ViewRetentionType(retention_intervals=retentionIntervals, retention_percentages=retentionsPercentages)
    
    def resolve_itineraryPostsConcat(self, info, **kwargs):
        userId = kwargs.get('userId')
        itineraryId = kwargs.get('itineraryId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')

        Verification.user_verify(userId)
        try:
            if itineraryId is not None:
                itinerary = UserSharedItinerary.objects.using('default').get(user_shared_itinerary_id=itineraryId)
            else:
                raise BadRequestException("itineraryId provided is invalid", 400)
        except UserSharedItinerary.NotFoundException:
            raise NotFoundException("itineraryId provided not found", 404)

        postIds = UserSharedItineraryPost.objects.using('default').filter(user_shared_itinerary_id=itinerary.user_shared_itinerary_id).values_list('post_id', flat=True)
        posts = []
        posts = Post.objects.using('default').filter(post_id__in=postIds).order_by('-created_on').values_list('post_id')
        
        posts = [PostListType(post_id=x[0]) for x in posts]
        flag, page_data = pagination(posts, page, limit)

        if flag:
            return posts
        else:
            raise BadRequestException(page_data)
