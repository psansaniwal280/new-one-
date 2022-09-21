#...
import graphene
import json
import geopy.distance
from graphene_django import DjangoObjectType
from .models import Post, PostSaved, PostComment, ExperienceCategory, UserToken, AttachmentType, ChatDeleteThread,  ChatMessageReactionType, ChatMessageReaction, VenueExperienceCategory, ShareType, UserBlocked, ReportPost, ReportPostReason, ReportUser, ReportUserReason, PostLike, PostShared, MediaPost, MediaUser, MediaVenue, MediaItinerary, Venue, User, VenueStayPrice, VenueTransportationPrice, VenueExperiencePrice, VenueType, Location, PostLike, VenueInternal, PostSaved, PostShared, VenueShared, PostComment, PostCommentLike, PostMention, PostCommentTag, PostCommentMention, Tag, PostTag, UserTag, UserTrip, VenueExternal, UserFollowing, Badge, UserBadge, BadgeType, UserSharedItinerary, UserSharedItineraryPost, UserSharedItineraryTag, UserSharedItineraryMention, UserProfile, UserFollower, UserFollowing, TripBooked, UserProfileTag, StayType, VenueStayType, VenueAmenity, VenueStayPrice, Amenity, ExploreCategory, UserBioMention, UserBioTag, ChatThread, ChatMessage, UserMessageStore, UserMessageUnsent, CardPaymentDetail, PaymentOption, BillingAddress, PaymentOptionType, Transaction,  Vendor, VendorVenue, VenueExperienceBookingOption
from django.db.models import Count, Sum
from datetime import datetime, date, time, timezone, timedelta
import datetime
import math
from .utilities.toBigInt import BigInt
from .utilities.filterVenueObjs import filterStayVenueObjs, filterExperienceVenueObjs, filterTransportationVenueObjs
from .utilities.filterDateVenueObjs import getDateFilteredVenueObjects, calculateVenueStayPrice, dates_between
from itertools import chain
from . import models
from .utilities.extractWord import extract_tags_mentions
from graphene_file_upload.scalars import Upload
import boto3
import re
# import requests, json
from boto3 import session
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import hashlib, binascii, os
from django.db.models import Q
from math import radians, cos, sin, asin, sqrt
from django.http import HttpResponseBadRequest, HttpResponse
from graphql import GraphQLError
from graphql_extensions import exceptions
from .utilities.errors import NotFoundException, BadRequestException, NoContentException, ConflictException, AuthorizationException
from django.db import IntegrityError
import asyncio
from django.db.models import Q
from django.db.models import Max, Avg
import graphql_jwt
from graphql_auth import mutations
from graphql_jwt.utils import jwt_encode, jwt_payload
from .utilities.authentication import authenticateLogin
from .utilities.standardizemethods import encrypt_password, standardize_phonenumber
from .utilities.sendMail import sendMailToUser, sendPasswordResetCodeMailToUser, sendPostReportMailToUser, sendUserReportMailToUser
import jwt
from .utilities.redis import get_routes_from_api, get_routes_from_cache, set_routes_to_cache, redis_connect, delete_routes_from_cache, get_hashmap_from_cache, set_hashmap_to_cache, delete_hashmap_from_cache
from .utilities.cache_lru import LRUCache
from django.contrib.sessions.backends.db import SessionStore
import pyotp
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii
import cryptography
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import pytz
from operator import getitem

#...
class UserIdFieldType(graphene.ObjectType):
    user_id = graphene.Int()
class PageInfoObject(graphene.ObjectType):
    nextPage = graphene.Int()
    limit = graphene.Int()

class aggregate(graphene.ObjectType):
    count = graphene.Int()

class aggregateObjectType(graphene.ObjectType):
    aggregate = graphene.Field(aggregate)

class BadgeType(graphene.ObjectType):
    # class Meta:
    #     model = Badge
    user_badge_id = graphene.Int()
    badge_id = graphene.Int()
    image = graphene.String()
    name = graphene.String()
    value = graphene.Int()
    badge_type = graphene.String()
    date_earned = graphene.DateTime()
    is_pinned = graphene.Boolean()

class UserListType(graphene.ObjectType):
    user_id= graphene.Int()    

class BadgesListType(graphene.ObjectType):
    user_badge_id = graphene.Int()

class BadgesPageListType(graphene.ObjectType):
    badges = graphene.List(BadgesListType)
    page_info = graphene.Field(PageInfoObject)

class ProfileTagObjectType(DjangoObjectType):
    class Meta:
        model = UserProfileTag
    user_tag_id = graphene.Int()
    name = graphene.String()
    def resolve_user_tag_id(self, info):
        return self.user_profile_tag_id

# class ProfileTagObjectType(DjangoObjectType):
#     class Meta:
#         model = UserProfileTag
#     user_profile_tag_id = graphene.Int()
#     name = graphene.String()

class VenueObjectType(DjangoObjectType):
    class Meta:
        model = Venue
    venue_id = graphene.String()
    is_external = graphene.Boolean()
    venue_price = graphene.String()
    venue_name = graphene.String()
    venue_location = graphene.String()
    venue_type = graphene.String()

    def resolve_venue_price(self, info):
        if self.is_external:
            return None
        else:
            result_venue = VenueInternal.objects.using('default').get(pk=self.venue_id)
            if result_venue.type_id == 1:
                price = VenueExperiencePrice.objects.using('default').get(pk=result_venue.price_id).price
            elif result_venue.type_id == 2:
                price = VenueStayPrice.objects.using('default').get(pk=result_venue.price_id).price
            elif result_venue.type_id == 3:
                try:
                    price = VenueTransportationPrice.objects.using('default').get(pk=result_venue.price_id).price
                except: 
                    price = 0
            return str(price) 
    def resolve_venue_location(self, info):
        if self.is_external:
            obj = VenueExternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.location.city)
        else:
            obj = VenueInternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.location.city)
    def resolve_venue_name(self, info):
        if self.is_external:
            obj = VenueExternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.name)
        else:
            obj = VenueInternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.name) 
    def resolve_venue_type(self, info):
        if self.is_external:
            obj = VenueExternal.objects.using('default').get(pk=self.venue_id)
            venue_type_obj = VenueType.objects.using('default').get(pk=obj.type_id)
            return venue_type_obj.name
        else:
            obj = VenueInternal.objects.using('default').get(pk=self.venue_id)
            venue_type_obj = VenueType.objects.using('default').get(pk=obj.type_id)
            return venue_type_obj.name

class VenueInternalType(DjangoObjectType):
    class Meta:
        model = VenueInternal
    name = graphene.String(), 
    price = graphene.Boolean(), 
    description = graphene.String(), 
    location = graphene.String(), 
    venue_id = graphene.String(), 
    type = graphene.String()

class VenueExternalType(DjangoObjectType):
    class Meta:
        model = VenueExternal
    api_id = graphene.String(),
    name = graphene.String(),  
    description = graphene.String(), 
    location = graphene.String(), 
    latitude = graphene.Boolean(), 
    longitude = graphene.Boolean(), 
    venue_id = graphene.String()

class mentionSection(graphene.ObjectType):
    username = graphene.String()        
    userid = graphene.Int()

class hashtagSection(graphene.ObjectType):
    hashtag = graphene.String()        
    tagid = graphene.Int()

class bioSection(graphene.ObjectType):
    content = graphene.String()
    hashtags = graphene.List(hashtagSection)
    mentions = graphene.List(mentionSection)

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
    phone_number = graphene.Int()
    gender = graphene.String()
    dob = graphene.Date()   

class ItineraryType(graphene.ObjectType):
    # class Meta:
    #     model = UserSharedItinerary
    itinerary_id = graphene.Int()
    user_id = graphene.Field(UserType)
    name = graphene.String()
    thumbnail = graphene.String()
    date_created = graphene.DateTime()
    date_modified = graphene.DateTime()

class ItineraryListType(graphene.ObjectType):
    itinerary_id = graphene.Int()
    date_created = graphene.DateTime()

class ItineraryPageListType(graphene.ObjectType):
    itineraries = graphene.List(ItineraryListType)
    page_info = graphene.Field(PageInfoObject)

class OutputHashTagType(DjangoObjectType):
    class Meta:
        model = Tag
    tag_id = graphene.Int()
    name = graphene.String()

class OutputPostHashTagType(DjangoObjectType):
    class Meta:
        model = PostTag
    post_tag_id = graphene.Int()
    post_id = graphene.Int()
    tag_id = graphene.Field(OutputHashTagType)
    def resolve_post_id(self, info):
        return Post.objects.all()
    def resolve_tag_id(self, info):
        return Tag.objects.all()

class OutputMentionType(DjangoObjectType):
    class Meta:
        model = PostMention
    post_mention_id = graphene.Int()
    post_id = graphene.Int()
    user_id = graphene.Field(UserType)
    def resolve_post_id(self, info):
        return Post.objects.all()
    def resolve_user_id(self, info):
        return User.objects.all()

class PostListType(graphene.ObjectType):
    post_id = graphene.Int()
    
class PostPageListType(graphene.ObjectType):
    posts = graphene.List(PostListType)
    page_info = graphene.Field(PageInfoObject)

class PostCommentListType(graphene.ObjectType):
    post_comment_id = graphene.Int()

class PostType(graphene.ObjectType):
    # class Meta:
    #     model = Post
    post_id = graphene.Int()
    media = graphene.String()
    thumbnail = graphene.String()
    venue_id = graphene.String()
    title = graphene.String()
    user_rating = graphene.Float()
    user_id = graphene.Int()
    is_verified_booking = graphene.Boolean()
    date_created = graphene.DateTime()
    postLikesAggregate = graphene.Field(aggregateObjectType)
    postCommentsAggregate = graphene.Field(aggregateObjectType)
    postSharesAggregate = graphene.Field(aggregateObjectType)
    postSavesAggregate = graphene.Field(aggregateObjectType)
    description = graphene.String()
    hashtags = graphene.List(hashtagSection)
    mentions = graphene.List(mentionSection)
    isLiked = graphene.Boolean()
    isSaved = graphene.Boolean()
    # isFollowing = graphene.Boolean()


    # def resolve_likes(self, info):
    #     return PostLike.objects.using('default').filter(post_id=self.['post_id']).count()
    def resolve_media(self, info):
        if self['media'][0] == 'h':
            return self['media']
        else:
            return MediaPost.objects.using('default').get(media_post_id=int(self['media'])).url
    def resolve_postLikesAggregate(self, info):
        return aggregateObjectType(aggregate(count=self['total_likes']))
    def resolve_postCommentsAggregate(self, info):
        return aggregateObjectType(aggregate(count=self['total_comments']))
    def resolve_postSavesAggregate(self, info):
        return aggregateObjectType(aggregate(count=self['total_saves']))
    def resolve_postSharesAggregate(self, info):
        return aggregateObjectType(aggregate(count=self['total_shares']))
    def resolve_hashtags(self, info):
        hashtags_word, hashtags = [], []
        hashtags_word, _ = extract_tags_mentions(self['description'])
        if hashtags_word == []:
            return []
        for one_hashtag in hashtags_word:
            try:
                tag_obj = Tag.objects.using('default').get(name=one_hashtag)
                try:
                    PostTag.objects.using('default').get(post_id=self['post_id'], tag_id=tag_obj.tag_id)
                except PostTag.DoesNotExist:
                    PostTag.objects.create(post_id=self['post_id'], tag_id=tag_obj.tag_id)
                hashtags.append(hashtagSection(tag_obj.name, tag_obj.tag_id))
            except Tag.DoesNotExist:
                tag_obj = Tag.objects.create(name=one_hashtag) 
                try:
                    PostTag.objects.using('default').get(post_id=self['post_id'], tag_id=tag_obj.tag_id)
                except PostTag.DoesNotExist:
                    PostTag.objects.create(post_id=self['post_id'], tag_id=tag_obj.tag_id)
                hashtags.append(hashtagSection(tag_obj.name, tag_obj.tag_id))  
        return hashtags
    def resolve_mentions(self, info):
        mentions_word, mentions = [], []
        _ , mentions_word = extract_tags_mentions(self['description'])
        if mentions_word == []:
            return []
        for one_mention in mentions_word:
            try:
                user_obj = User.objects.using('default').get(username=one_mention)
                mentions.append(mentionSection(user_obj.username, user_obj.user_id))
            except User.DoesNotExist:
                mentions.append(mentionSection(one_mention, None))
        return mentions
    # def resolve_isLiked(self, info):
    #     result = False
    #     try:
    #         post_liked = PostLike.objects.using('default').get(Q(post_id=self['post_id']) & Q(user_id=self['user_id']))
    #         result = True
    #     except PostLike.DoesNotExist:
    #         result = False
    #     return result  
    # def resolve_isSaved(self, info):
    #     result = False
    #     try:
    #         post_saved = PostSaved.objects.using('default').get(Q(post_id=self['post_id']) & Q(user_id=self['user_id']))
    #         result = True
    #     except PostSaved.DoesNotExist:
    #         result = False
    #     return result   
    # def resolve_isFollowing(self, info):
        # if self['isFollowing']:
        #     return True
        # else:
        #     return False


class UserMainProfile(graphene.ObjectType):
    # class Meta:
    #     model = UserProfile
    user_id = graphene.Int()
    username = graphene.String()
    name = graphene.String()
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

    def resolve_username(self, info):
        user = User.objects.using('default').get(user_id=self.user_id)
        return user.username
    def resolve_level(self, info):
        user = User.objects.using('default').get(user_id=self.user_id)
        return user.level 
    def resolve_avatar(self, info):
        user = User.objects.using('default').get(user_id=self.user_id)
        return user.avatar 
    def resolve_city(self, info):
        try:
            if self.location is not None:
                location_obj = Location.objects.using('default').get(location_id=self.location.location_id)
                return location_obj.city
            else:
                return None
        except Location.DoesNotExist:
            return None
        
    def resolve_country(self, info):
        try:
            if self.location is not None:
                location_obj = Location.objects.using('default').get(location_id=self.location.location_id)
                return location_obj.country
            else:
                return None
        except Location.DoesNotExist:
            return None
    def resolve_bio(self, info):
        bio_content = UserProfile.objects.using('default').get(user_id=self.user_id).bio
        hashtag_words, hashtags = [], []
        mention_words, mentions = [], []
        hashtag_words, mention_words = extract_tags_mentions(bio_content)
        if hashtag_words == []:
            hashtags = []
        for one_hashtag in hashtag_words:
            try:
                tag_obj = Tag.objects.using('default').get(name=one_hashtag)
                hashtags.append(hashtagSection(tag_obj.name, tag_obj.tag_id))
            except Tag.DoesNotExist:
                tag_obj = Tag.objects.create(name=one_hashtag)   
                hashtags.append(hashtagSection(tag_obj.name, tag_obj.tag_id))  
        
        if mention_words == []:
            mentions = []
        for one_mention in mention_words:
            try:
                user_obj = User.objects.using('default').get(username=one_mention)
                mentions.append(mentionSection(user_obj.username, user_obj.user_id))
            except User.DoesNotExist:
                mentions.append(mentionSection(one_mention, None))
        
        return bioSection(bio_content, hashtags, mentions)
        
    # def resolve_follower(self, info):
    #     return UserFollowing.objects.using('default').filter(following_user_id=self.user_id).count()
    # def resolve_following(self, info):
    #     return UserFollowing.objects.using('default').filter(user_id=self.user_id).count()
    # def resolve_trips_booked(self, info):
    #     return UserTrip.objects.using('default').filter(user_id=self.user_id).count()
    def resolve_tags(self, info):
        try:
            tags_ids = UserProfileTagList.objects.using('default').get(user_id=self.user_id)
            return list(UserProfileTag.objects.using('default').filter(user_profile_tag_id__in=tags_ids.user_profile_tag_list))
        except UserProfileTagList.DoesNotExist:
            return []
    
    # def isFollowing(self, info):


class PostLikeType(DjangoObjectType):
    class Meta:
        model = PostLike
    post_like_id = graphene.Field(BigInt)
    post_id = graphene.Field(BigInt)
    user_id = graphene.Field(BigInt)

class PostSavedType(DjangoObjectType):
    class Meta:
        model = PostSaved
    post_saved_id = graphene.Field(BigInt)
    post_id = graphene.Field(BigInt)
    user_id = graphene.Field(BigInt)

class OutputUserType(graphene.ObjectType):
    user_id = graphene.Int()
    username = graphene.String()
    avatar = graphene.String()
    level = graphene.Int()

class PostCommentReplyType(graphene.ObjectType):
    post_comment_id = graphene.Int()
    # user = graphene.Field(UserType)
    # post_id = graphene.Field(PostType)
    # comment = graphene.String()
    # number_of_likes = graphene.Int()
    # date_created = graphene.DateTime()
    # hashtags = graphene.List(hashtagSection)
    # mentions = graphene.List(mentionSection)

class PostCommentType(graphene.ObjectType):
    # class Meta:
    #     model  = PostComment
    post_comment_id = graphene.Field(BigInt)
    user = graphene.Field(OutputUserType)
    comment = graphene.String()
    commentLikesAggregate = graphene.Field(aggregateObjectType)
    date_created = graphene.DateTime()
    commentRepliesAggregate = graphene.Field(aggregateObjectType)
    comment_replies = graphene.List(PostCommentReplyType)
    hashtags = graphene.List(hashtagSection)
    mentions = graphene.List(mentionSection)
    isLiked = graphene.Boolean()
    isReply = graphene.Boolean()
    # def resolve_no_of_replies(self, info):
    #     return 0
"""
Graphene Location Object Type
"""
class locationObject(graphene.InputObjectType):
    city = graphene.String()
    state = graphene.String()
    country = graphene.String()
    latitude = graphene.Float()
    longitude = graphene.Float()

class LocationObject(graphene.ObjectType):
    city = graphene.String()
    state = graphene.String()
    country = graphene.String()
    latitude = graphene.Float()
    longitude = graphene.Float()

class LocationObjectType(graphene.ObjectType):
    city = graphene.String()
    state = graphene.String()
    country = graphene.String()
    latitude = graphene.Float()
    longitude = graphene.Float()

class PlaceObjectType(graphene.ObjectType):
    venue_id = graphene.String()
    venue_title = graphene.String()
    venue_type = graphene.String()
    is_external = graphene.Boolean()
    location = graphene.Field(LocationObjectType)
    rating = graphene.Float()
    noOfRatings = graphene.Int()

    def resolve_rating(self,info):
        rating = Post.objects.using('default').filter(venue_id=self.venue_id).aggregate(Avg('user_rating'))['user_rating__avg']
        return rating if rating else 0 
    def resolve_noOfRatings(self, info):
        return Post.objects.using('default').filter(venue_id=self.venue_id).count()

'''
Search Suggestions Grpahene Object Types
'''
class SearchPostListType(graphene.ObjectType):
    post_id = graphene.Int()

class SearchAllSuggestionsHashTagType(graphene.ObjectType):
    hashtag_id = graphene.String()
    hashtag = graphene.String()

class SearchAllSuggestionsVenueType(graphene.ObjectType):
    venue_id = graphene.String()
    venue_name = graphene.String()

class SearchAllSuggestionsUsersType(graphene.ObjectType):
    user_id = graphene.String()
    username = graphene.String()    

class AllSearchSuggestionsType(graphene.ObjectType):
    hashtags = graphene.List(SearchAllSuggestionsHashTagType)
    venues = graphene.List(SearchAllSuggestionsVenueType)
    users = graphene.List(SearchAllSuggestionsUsersType)

'''
Search By Filter Graphene Object Types (Output)
'''

class SearchFilterVenueObjectType(graphene.ObjectType):
    venue_id = graphene.String()
    venue_type_id = graphene.String()
    venue_type_name = graphene.String()

class SearchFilterUserType(graphene.ObjectType):
    user_id = graphene.String()
    username = graphene.String()
    avatar = graphene.String()
    level = graphene.String()
    rating = graphene.String()

class SearchFilterLocationType(graphene.ObjectType):
    city = graphene.String()
    country = graphene.String()
    latitude = graphene.String()
    longitude = graphene.String()

class SearchStaysFilterValueType(graphene.ObjectType):
    is_post = graphene.Boolean()
    price = graphene.String()
    location = graphene.Field(SearchFilterLocationType)
    venue = graphene.Field(SearchFilterVenueObjectType)
    thumbnail = graphene.String()
    name = graphene.String()
    user = graphene.Field(SearchFilterUserType)

class SearchTagsValueType(graphene.ObjectType):
    tagId = graphene.Int() 
    hashtag = graphene.String()
    posts = graphene.List(PostListType)

class SearchTagsValueListType(graphene.ObjectType):
    page_info=graphene.Field(PageInfoObject)
    tags = graphene.List(SearchTagsValueType)
class SearchTagsValuePostListType(graphene.ObjectType):
    tag_id = graphene.Int()
    hashtag = graphene.String()
    posts=graphene.List(PostListType)
    page_info = graphene.Field(PageInfoObject)
class SearchPlacesValueType(graphene.ObjectType):
    venue = graphene.Field(PlaceObjectType)
    posts = graphene.List(PostListType)
class SearchPlacesValuePostListType(graphene.ObjectType):
    venue = graphene.Field(PlaceObjectType)
    posts = graphene.List(PostListType)
    page_info = graphene.Field(PageInfoObject)
class SearchPlacesValueListType(graphene.ObjectType):
    venues = graphene.List(SearchPlacesValueType)
    page_info = graphene.Field(PageInfoObject)
'''
Search Grpahene Object Types
'''
class SearchListTemplateType(graphene.ObjectType):
    id = graphene.String()
    type = graphene.Int()

class SearchAllHashTagType(graphene.ObjectType):
    hashtag_id = graphene.String()
    hashtag = graphene.String()

class SearchAllLocationType(graphene.ObjectType):
    city = graphene.String()
    country = graphene.String()
    latitude = graphene.String()
    longitude = graphene.String()

class SearchAllCarRentalType(graphene.ObjectType):
    is_post = graphene.Boolean()
    price = graphene.String()
    location = graphene.Field(SearchFilterLocationType)
    venue = graphene.Field(SearchFilterVenueObjectType)
    thumbnail = graphene.String()
    name = graphene.String()
    user = graphene.Field(SearchFilterUserType)

class SearchAllExperienceType(graphene.ObjectType):
    is_post =graphene.Boolean()
    template = graphene.Field(SearchListTemplateType)
    

class SearchAllExperienceListType(graphene.ObjectType):
    experiences = graphene.List(SearchAllExperienceType)
    page_info= graphene.Field(PageInfoObject)
class AllSearchExperienceListType(graphene.ObjectType):
    is_post =graphene.Boolean()
    template = graphene.Field(SearchListTemplateType)
# class SearchAllExperienceType(graphene.ObjectType):
#     is_post = graphene.Boolean()
#     price = graphene.String()
#     location = graphene.Field(SearchFilterLocationType)
#     venue = graphene.Field(SearchFilterVenueObjectType)
#     thumbnail = graphene.String()
#     name = graphene.String()
#     user = graphene.Field(SearchFilterUserType)

class SearchAllStayType(graphene.ObjectType):
    is_post = graphene.Boolean()
    price = graphene.String()
    location = graphene.Field(SearchFilterLocationType)
    venue = graphene.Field(SearchFilterVenueObjectType)
    thumbnail = graphene.String()
    name = graphene.String()
    user = graphene.Field(SearchFilterUserType)

class SearchAllUsersType(graphene.ObjectType):
    user_id = graphene.String()
    username = graphene.String()
    avatar = graphene.String()
    level = graphene.Int()
    tag = graphene.String()    

class AllSearchType(graphene.ObjectType):
    users = graphene.List(UserListType)
    results = graphene.List(AllSearchExperienceListType)
    # stays = graphene.List(SearchAllStayType)
    # experiences = graphene.List(SearchAllExperienceListType)
    # car_rentals = graphene.List(SearchAllCarRentalType)
    # hashtags = graphene.List(SearchAllHashTagType)

#----------------------------------------------------------------------------------------------------------------------------
class SearchRecommendedListType(graphene.ObjectType):
    pass

class SearchUserListType(graphene.ObjectType):
    user_id = graphene.Int()

class SearchUserPageListType(graphene.ObjectType):
    users = graphene.List(SearchUserListType)
    page_info = graphene.Field(PageInfoObject)

'''
Search Filter Objects
'''
class priceObject(graphene.InputObjectType):
    min = graphene.Int()
    max = graphene.Int()

class staysFilterObject(graphene.InputObjectType):
    noOfGuests = graphene.Int()
    sortBy = graphene.String()
    typeOfStay = graphene.List(graphene.String)
    pricing = priceObject()
    amenities = graphene.List(graphene.String)
    uniqueStays = graphene.List(graphene.String)
    userRatings = graphene.String()

class experiencesFilterObject(graphene.InputObjectType):
    noOfGuests = graphene.Int()
    sortBy = graphene.String()
    categories = graphene.List(graphene.String)
    pricing = priceObject()
    timeOfDay = graphene.List(graphene.String)
    duration = graphene.List(graphene.String)
    userRatings = graphene.String()

class transportationsFilterObject(graphene.InputObjectType):
    sortBy = graphene.String()
    vehicleType = graphene.List(graphene.String)
    pricing = priceObject()
    capacity = graphene.Int()



'''
Explore Graphene Object Type
'''

class ExploreTheLoopObjectType(graphene.ObjectType):
    name = graphene.String()
    thumbnail = graphene.String()

class ExploreAllUserObjectType(graphene.ObjectType):
    user_id = graphene.String()
    username = graphene.String()
    avatar = graphene.String()
    rating = graphene.String()

class ExploreAllPostObjectType(graphene.ObjectType):
    post_id  = graphene.String()
    name = graphene.String()
    #price = graphene.String()
    user = graphene.Field(ExploreAllUserObjectType)

class ExploreAllFieldType(graphene.ObjectType):
    near_you = graphene.List(ExploreAllPostObjectType)
    explore_the_loop = graphene.List(ExploreTheLoopObjectType)
    trending_videos = graphene.List(ExploreAllPostObjectType)
    recommended_users = graphene.List(ExploreAllUserObjectType)
    recommended_videos = graphene.List(ExploreAllPostObjectType)

"""
Error Message and Code Type
"""
class ExceptionFieldObjectType(graphene.ObjectType):
    message = graphene.String()
    code = graphene.Int()
    
class ExceptionErrorObjectType(graphene.ObjectType):
    error = graphene.Field(ExceptionFieldObjectType)

"""
    User Type
"""
class userObject(graphene.ObjectType):
    is_following = graphene.Boolean()
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
            tags_list.append(profileTagObject(tag.user_profile_tag_id, tag.name))
        except UserProfileTag.DoesNotExist:
            raise NotFoundException("userProfileTagId provided not found", 404)
    return tags_list

"""
    String Type
"""
class stringType(graphene.ObjectType):
    message = graphene.String()

"""
    String Type
"""
class responseResetPasswordType(graphene.ObjectType):
    message = graphene.String()
    token = graphene.String()

class ReportPostReasonType(graphene.ObjectType):
    class Meta:
        model = ReportPostReason
    report_post_reason_id = graphene.Int()
    reason = graphene.String()

class ReportUserReasonType(graphene.ObjectType):
    class Meta:
        model = ReportUserReason
    report_user_reason_id = graphene.Int()
    reason = graphene.String()

class ChatUserType(graphene.ObjectType):
    username = graphene.String()
    userId = graphene.Int()
    avatar = graphene.String()

class AttachmentTypeObject(graphene.ObjectType):
    attachment_type_id = graphene.Int()
    name = graphene.String()

class ChatMessageAttachmentType(graphene.ObjectType):
    type = graphene.Field(AttachmentTypeObject)
    id = graphene.String()

class ChatMessageReactionType(graphene.ObjectType):
    type_id = graphene.String()
    user_id = graphene.String()

class ChatSharesTemplateMessageType(graphene.ObjectType):
    type = graphene.String()
    media = graphene.String()
    id = graphene.String()
    title = graphene.String()

class ChatSharesMessageType(graphene.ObjectType):
    link = graphene.String()
    template = graphene.Field(ChatSharesTemplateMessageType)
    

class ChatStroyMessageType(graphene.ObjectType):
    link = graphene.String()
    id = graphene.Int()
    is_reply = graphene.Boolean()

class ChatMessageType(graphene.ObjectType):
    class Meta:
        model = ChatMessage
    isSender = graphene.Boolean()
    messageId = graphene.Int()
    modified_datetime = graphene.DateTime()
    # sender = graphene.Field(ChatUserType)
    sender_user_id = graphene.Int()
    recipient_user_id = graphene.List(UserIdFieldType)
    message = graphene.String()
    attachment = graphene.Field(ChatMessageAttachmentType)
    reaction = graphene.List(ChatMessageReactionType)
    shares = graphene.Field(ChatSharesMessageType)
    story = graphene.Field(ChatStroyMessageType)
    read = graphene.Boolean()

class ChatMessagesType(graphene.ObjectType):
    messageId = graphene.Int()
    date_created = graphene.DateTime()
    # message = graphene.String()

class ChatMessagesPageListType(graphene.ObjectType):
    page_info = graphene.Field(PageInfoObject)
    messages = graphene.List(ChatMessagesType)

class ChatThreadType(graphene.ObjectType):
    thread_id = graphene.Int()
    name = graphene.String()
    # messages = graphene.List(ChatMessagesType)
    participants = graphene.List(UserIdFieldType)
    unreadCount = graphene.Field(aggregateObjectType)
    mostRecentMessage = graphene.String()
    hasUnreadMessage = graphene.Boolean()
    admin = graphene.List(UserIdFieldType)

class ChatThreadListType(graphene.ObjectType):
    threadId = graphene.Int()
    participants = graphene.List(ChatUserType)
    date_modified = graphene.DateTime()
    recent_message = graphene.Field(ChatMessagesType)
    has_unread = graphene.Boolean()

class ChatThreadsPageListType(graphene.ObjectType):
    page_info = graphene.Field(PageInfoObject)
    threads = graphene.List(ChatThreadListType)

# class ChatMessageListType(graphene.ObjectType):
#     messages = graphene.List(ChatMessagesType)

class BillingAddressType(graphene.ObjectType):
    class Meta:
        model = BillingAddress
    billing_name = graphene.String()
    address = graphene.String()
    city = graphene.String()
    state = graphene.String()
    zip = graphene.Int()

class UserPaymentCardType(graphene.ObjectType):
    card_payment_detail_id = graphene.Int()
    last_four_digits = graphene.Int()
    expiry_month = graphene.Int()
    expiry_year = graphene.Int()
    # security_code = graphene.Int()+
    card_name = graphene.String()
    billing_address = graphene.Field(BillingAddressType)

class PaymentOptionType(graphene.ObjectType):
    payment_option_id = graphene.Int()
    name = graphene.String()
    last_four_digits = graphene.Int()
    expiry_date = graphene.String()

class PaymentOptionField(graphene.ObjectType):
    cards = graphene.List(PaymentOptionType)

class ImageObjectType(graphene.ObjectType):
    id = graphene.Int()
    url = graphene.String()

class VendorObjectType(graphene.ObjectType):
    # class Meta:
    #     model = Vendor
    vendor_id = graphene.Int()
    name = graphene.String()
    avatar = graphene.String()
    bio_url = graphene.String()
    short_description = graphene.String()
    rating = graphene.Float()
    no_of_ratings = graphene.Int()

# class VendorListObjectType(graphene.ObjectType):
#     venue_vendor_id = graphene.Int()

class VenueUserObjectType(graphene.ObjectType):
    user_id = graphene.Int()
    # username = graphene.String()
    # avatar = graphene.String()
    # level = graphene.Int()
    # phone_number = graphene.Field(BigInt)
    # rating = graphene.Float()

class FeaturedVideoObjectType(graphene.ObjectType):
    isVideo = graphene.Boolean()
    media = graphene.List(ImageObjectType)

class VenueRatingObjectType(graphene.ObjectType):
    venue_rating = graphene.Float()
    venue_rating_aggregate = graphene.Field(aggregateObjectType)

class ViewVenueObjectType(graphene.ObjectType):
    venue_id = graphene.String()
    venue_type = graphene.String()
    featured_media = graphene.Field(FeaturedVideoObjectType)
    title = graphene.String()
    location = graphene.Field(LocationObjectType)
    price = graphene.Float()
    price_with_tax = graphene.Float()
    # rating = graphene.Float()
    # no_of_ratings = graphene.Int()
    is_refundable = graphene.Boolean()
    shared_by = graphene.Field(VenueUserObjectType)
    short_description = graphene.String()
    gallery = graphene.List(ImageObjectType)
    vendor_venue_id = graphene.Int()

class DurationUnitType(graphene.ObjectType):
    value = graphene.Int()
    unit = graphene.String()

class VenueBookingOptionObjectType(graphene.ObjectType):
    time = graphene.Time()
    duration = graphene.Field(DurationUnitType)
    title = graphene.String()
    price = graphene.Float()
    guests_limit = graphene.Int()
    short_description = graphene.String()

class DescriptionObjectType(graphene.ObjectType):
    content = graphene.String()
    hashtags = graphene.List(hashtagSection)
    mentions = graphene.List(mentionSection)

class VenueBookingOptionsIdsType(graphene.ObjectType):
    Ids = graphene.List(graphene.Int)

# class TagObjectType(DjangoObjectType):
#     class Meta:
#         model = Tag
#     tag_id = graphene.Int()
#     name = graphene.String()

#     # def resolve_hashtag(self, info):
#     #     return self.name

class ItineraryObjectType(graphene.ObjectType):
    itinerary_id = graphene.Int()
    userId = graphene.Int()
    title = graphene.String()
    description = graphene.Field(DescriptionObjectType)
    tags = graphene.List(hashtagSection)
    posts = graphene.List(PostListType)
    thumbnail = graphene.String()

    def resolve_description(self, info):
        description_content = UserSharedItinerary.objects.using('default').get(user_shared_itinerary_id=self['itinerary_id']).description
        hashtag_words, hashtags = [], []
        mention_words, mentions = [], []
        hashtag_words, mention_words = extract_tags_mentions(description_content)
        if hashtag_words == []:
            hashtags = []
        for one_hashtag in hashtag_words:
            try:
                tag_obj = Tag.objects.using('default').get(name=one_hashtag)
                hashtags.append(hashtagSection(tag_obj.name, tag_obj.tag_id))
            except Tag.DoesNotExist:
                tag_obj = Tag.objects.create(name=one_hashtag)   
                hashtags.append(hashtagSection(tag_obj.name, tag_obj.tag_id))  
        
        if mention_words == []:
            mentions = []
        for one_mention in mention_words:
            try:
                user_obj = User.objects.using('default').get(username=one_mention)
                mentions.append(mentionSection(user_obj.username, user_obj.user_id))
            except User.DoesNotExist:
                mentions.append(mentionSection(one_mention, None))
        
        return DescriptionObjectType(description_content, hashtags, mentions)

# class VenueAvailabilityObjectType(graphene.ObjectType):
#     date = graphene.DateTime()
#     booking_options = graphene.List(VenueBookingOptionObjectType)

class VenueAvailableDatesObjectType(graphene.ObjectType):
    # ids = graphene.List(graphene.Int)
    dates = graphene.List(graphene.DateTime)

class SearchHistoryType(graphene.ObjectType):
    searchTerm = graphene.String()
    searchDate = graphene.DateTime()

# class aggregate(graphene.ObjectType):
#     count = graphene.Int()

# class aggregateObjectType(graphene.ObjectType):
#     aggregate = graphene.Field(aggregate)

class SearchRecommendedType(graphene.ObjectType):
    message = graphene.String()

class BlockedUsersListType(graphene.ObjectType):
    user_id = graphene.Int()

class APIPlacesListType(graphene.ObjectType):
    name = graphene.String()

class UserReasonDetailObjectType(graphene.ObjectType):
    reason = graphene.String()
    description = graphene.String()
    report_user_reason_id = graphene.Int()

class PostReasonDetailObjectType(graphene.ObjectType):
    reason = graphene.String()
    description = graphene.String()
    report_post_reason_id = graphene.Int()
'''
This is where you write all the queries for your API.
'''

class Query(graphene.ObjectType):
    
    #Feed Posts Queries
    followingFeed = graphene.List(PostListType, userId = graphene.Int())
    discoveryFeed =  graphene.List(PostListType, userId = graphene.Int())
    #Explore Queries
    exploreAll = graphene.Field(ExploreAllFieldType, userId = graphene.Int(), location=locationObject())
    #User Profile Tags
    allUserTags = graphene.List(ProfileTagObjectType)
    # getUserTags = graphene.List(profileTagObject, userId = graphene.Int())
    

    #User Profile Queries
    userPosts = graphene.Field(PostPageListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    userBadges = graphene.Field(BadgesPageListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    userBadge = graphene.Field(BadgeType, userBadgeId = graphene.Int())
    userItineraries = graphene.Field(ItineraryPageListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    user = graphene.Field(UserMainProfile, recipientUserId=graphene.Int(), authUserId=graphene.Int())

    usersFollowingAggregate = graphene.Field(aggregateObjectType, userId = graphene.Int())

    userFollowersAggregate = graphene.Field(aggregateObjectType, userId = graphene.Int())

    tripsBookedAggregate = graphene.Field(aggregateObjectType, userId = graphene.Int())

    userPersonalInfo = graphene.Field(UserPersonalInfoObjectType, userId= graphene.Int())

    #User Followed & Following Queries
    usersFollowing = graphene.Field(userPageObjectType, userId =  graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    userFollowers = graphene.Field(userPageObjectType, userId = graphene.Int(), page=graphene.Int(), limit=graphene.Int())
            
    usersFollowingResults = graphene.Field(userPageObjectType, userId=graphene.Int(), searchContent = graphene.String(), page=graphene.Int(), limit=graphene.Int())
    userFollowersResults = graphene.Field(userPageObjectType, userId=graphene.Int(), searchContent = graphene.String(), page=graphene.Int(), limit=graphene.Int())

    #Logout
    logout = graphene.Field(stringType, userId=graphene.Int())

    #Send Reset Password Code
    resetPasswordCode = graphene.Field(responseResetPasswordType, email=graphene.String())
    # resendResetPasswordCode = graphene.Field(responseResetPasswordType, email=graphene.String())

    verifyresetpasswordcode = graphene.Field(stringType, code=graphene.String(), token=graphene.String())

    #Get Cache 
    getTokenFromCache = graphene.Field(stringType, userId=graphene.Int())

    #Resend User Activation Link
    resendActivation = graphene.Field(stringType, email=graphene.String())

    #Posts Queries
    allPosts = graphene.List(PostType)
    post = graphene.Field(PostType, postId=graphene.Int(), userId = graphene.Int())
    savedPosts = graphene.Field(PostPageListType, userId = graphene.Int(), page = graphene.Int(), limit=graphene.Int())
    
    #Comments Queries
    postComments = graphene.List(PostCommentListType, postId=graphene.Int())
    comment = graphene.Field(PostCommentType, postCommentId= graphene.Int(), authUserId=graphene.Int())
    
    #Search Queries
    """getRecentSearch = graphene.List(RecentSearchType, user_id=graphene.Int())"""
    """searchAllSuggestions = graphene.List(AllSearchSuggestionsType, user_id=graphene.Int(), search_content=graphene.String())"""
    searchAll =graphene.Field(AllSearchType, userId=graphene.Int(), searchContent=graphene.String(), checkInDate=graphene.String(), checkOutDate=graphene.String(), location = locationObject())
    userResults = graphene.Field(SearchUserPageListType, userId=graphene.Int(), searchContent=graphene.String(), page=graphene.Int(), limit=graphene.Int())
    stayResults = graphene.List(SearchStaysFilterValueType, userId=graphene.Int(), location=graphene.String(), searchContent=graphene.String(), filterContent=staysFilterObject(), checkInDate=graphene.String(), checkOutDate=graphene.String())
    transportationResults = graphene.List(SearchAllCarRentalType, userId=graphene.Int(), pickupLocation=locationObject(), dropoffLocation=locationObject(), searchContent=graphene.String(), filterContent=transportationsFilterObject(), checkInDate=graphene.String(), checkInTime=graphene.String(), checkOutDate=graphene.String(), checkOutTime=graphene.String())
    experienceResults = graphene.Field(SearchAllExperienceListType, userId=graphene.Int(), location=graphene.String(), searchContent=graphene.String(), filterContent=experiencesFilterObject(), checkInDate=graphene.String(), checkOutDate=graphene.String(), page=graphene.Int(), limit=graphene.Int())
    searchTags = graphene.Field(SearchTagsValueListType, userId = graphene.Int(), searchContent = graphene.String(), page=graphene.Int(), limit=graphene.Int())
    searchVenues = graphene.Field(SearchPlacesValueListType, userId = graphene.Int(), searchContent = graphene.String(), page=graphene.Int(), limit=graphene.Int())
    searchHistory = graphene.List(SearchHistoryType, userId = graphene.Int())
    searchRecommendations = graphene.Field(AllSearchSuggestionsType, userId = graphene.Int(), searchContent=graphene.String())

    
    #Delete Search History Term
    deleteSearchHistoryTerm = graphene.Field(stringType, userId = graphene.Int(), searchTerm = graphene.String())
    #Delete Search History 
    deleteSearchHistory = graphene.Field(stringType, userId = graphene.Int())

    #Report Post Reasons
    reportPostReasons = graphene.List(ReportPostReasonType)
    reportUserReasons = graphene.List(ReportUserReasonType)

    #Recieve Message
    messages = graphene.List(ChatMessageType, userId = graphene.Int(), recipientUserId= graphene.Int(), threadId = graphene.Int())
    
    #Threads
    threadList = graphene.Field(ChatThreadsPageListType, userId = graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    #Threads -- Chat Request
    requestThreadList = graphene.Field(ChatThreadsPageListType, userId = graphene.Int(), page=graphene.Int(), limit = graphene.Int())

    #Message Thread
    threadInfo = graphene.Field(ChatThreadType, userId = graphene.Int(), threadId = graphene.Int())

    #Message List 
    messageList = graphene.Field(ChatMessagesPageListType, userId = graphene.Int(), threadId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    #Message
    message = graphene.Field(ChatMessageType, userId = graphene.Int(), messageId = graphene.Int())

    #Get Payment Options
    paymentInfo = graphene.Field(UserPaymentCardType, paymentOptionId = graphene.Int(), userId = graphene.Int())

    paymentOptions = graphene.Field(PaymentOptionField, userId = graphene.Int())

    #Get Venue Object by Venue Id
    venue = graphene.Field(ViewVenueObjectType, venueId = graphene.String(), userId = graphene.Int(), postId = graphene.Int())

    #Get Venue Rating by Venue Id
    venueRating = graphene.Field(VenueRatingObjectType, venueId=graphene.String())

    #Get Vendor Object By Venue Vendor Id
    vendor = graphene.Field(VendorObjectType, vendorVenueId = graphene.Int())
    
    #Get Available Dates of a Venue
    venueAvailableDates = graphene.Field(VenueAvailableDatesObjectType, venueId = graphene.String(), userId = graphene.Int())

    #Get Booking Options for that particular date
    venueBookingOptions = graphene.Field(VenueBookingOptionsIdsType, userId = graphene.Int(), venueId = graphene.String(), date=graphene.String()) #'''dateIds = graphene.List(graphene.Int)'''

    #Get Booking Option with Venue Booking Option Id
    venueBookingOption = graphene.Field(VenueBookingOptionObjectType, userId = graphene.Int(), venueBookingOptionId = graphene.Int())

    #Get Itinerary by Itinerary Ids
    itinerary = graphene.Field(ItineraryObjectType, userId = graphene.Int(), itineraryId=graphene.Int())

    #Get Post by Hashtag Id
    tagPosts = graphene.Field(SearchTagsValuePostListType, userId=graphene.Int(), tagId = graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    #Get Post by Places(Venue Id)
    venuePosts = graphene.Field(SearchPlacesValuePostListType, userId = graphene.Int(), venueId = graphene.String(), isExternal = graphene.Boolean(), page=graphene.Int(), limit=graphene.Int())

    #Get Blocked User List by User Id
    blockedUsers = graphene.List(BlockedUsersListType, userId = graphene.Int())

    #Query Places -- Google API.
    queryPlaces = graphene.List(APIPlacesListType, userId = graphene.Int(), searchContent= graphene.String())

    #Report Users Reason Detail
    reportUserReason = graphene.Field(UserReasonDetailObjectType, userId = graphene.Int(), reportUserReasonId = graphene.Int())

    #Report Post reason Detail
    reportPostReason = graphene.Field(PostReasonDetailObjectType, userId = graphene.Int(), reportPostReasonId = graphene.Int())


 #Get All Posts    
    def resolve_allPosts(parent, info):
        return Post.objects.all()

 #Get Discovery Feed for each user
    def resolve_discoveryFeed(parent, info, **kwargs):
        id = kwargs.get('userId')
        # if not info.context.session[id]:
        #     raise AuthorizationException("Please login to access", 401)
        # id = info.context.session[id]['userId']
        # # id = kwargs.get('userId')
        if id is not None:
            result = []
            try:
                if User.objects.using('default').get(user_id=id) is not None:
                    for i in Post.objects.all().order_by('-date_created'):
                        if i.post_id >= 32 and i.post_id <=48:
                            result.append(PostListType(i.post_id))
                    # if not result == []:
                    print(result.sort(key=lambda x:x.post_id))
                    return result
                    # else:
                    #     raise NotFoundException("no associated posts for the user", 404)
            except User.DoesNotExist:
                raise NotFoundException("userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId is invalid", 400)

 #Get Following Feed for each user       
    def resolve_followingFeed(parent, info, **kwargs):
        id = kwargs.get('userId')
        if id is not None:
            try:
                if User.objects.using('default').get(user_id=id) is not None:
                    
                    following_ids = UserFollowing.objects.using('default').filter(user_id=id).values_list('following_user_id', flat=True)
                    result = []
                    if following_ids:
                        for i in Post.objects.using('default').filter(user_id__in=following_ids).order_by('-date_created'):
                            if i.post_id >= 49 and i.post_id <=58:
                                result.append(PostListType(i.post_id))
                    result.sort(key=lambda x:x.post_id)
                    return result
                    
            except User.DoesNotExist:
                raise NotFoundException("userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

 #Get Post Ids List by User Id  
    def resolve_userPosts(parent, info, **kwargs):
        id = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        # if info.context.session[str(id)] == {}:
        #     raise AuthorizationException("Please login to access", 401)
        
        if id is not None :
            result = []
            try:
                if User.objects.using('default').get(user_id=id) and UserProfile.objects.using('default').get(user_id=id):
                    for i in Post.objects.using('default').filter(user_id=id).order_by('-date_created'):
                        result.append(PostListType(i.post_id))
                    result.sort(key=lambda x:x.post_id, reverse=True)
                    if len(result)>0:
                        if page and limit:
                            totalPages = math.ceil(len(result)/limit)
                            if page <= totalPages:
                                start = limit*(page-1)
                                result = result[start:start+limit]

                                return PostPageListType(posts=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                            else:
                                raise BadRequestException("invalid request; page provided exceeded total")
                        elif page == limit == None:
                            return PostPageListType(posts=result, page_info=PageInfoObject(nextPage= None, limit=None))
                        elif page is None:
                            raise BadRequestException("invalid request; limit cannot be provided without page")
                        elif limit is None:
                            raise BadRequestException("invalid request; page cannot be provided without limit")
                        
                    else:
                        return PostPageListType(posts=[], page_info=PageInfoObject(nextPage= None, limit=None))
                
                    
                    # else:
                    #     raise NotFoundException("post does not exist", 204) 
            except (User.DoesNotExist, Post.DoesNotExist):
                raise NotFoundException("userId provided not found", 404)
            except UserProfile.DoesNotExist:
                raise NotFoundException("profile for provided userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)       
        return None

 #Get Badges by User Id    
    def resolve_userBadges(parent, info , **kwagrs):
        
        id = kwagrs.get('userId')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if id is not None :
            try:
                result_badge_ids = []
                if User.objects.using('default').get(user_id=id) and UserProfile.objects.using('default').get(user_id=id):
                    result_badge_ids = UserBadge.objects.using('default').filter(user_id=id)
                    result = []
                    k =0
                    if result_badge_ids:
                        for j in result_badge_ids:
                            for i in Badge.objects.using('default').filter(badge_id = j.badge_id):
                                if j.is_pinned:
                                    result.insert(0, j)#BadgesListType(j.user_badge_id)) #, i.badge_id, i.image, i.name, i.value, i.badge_type_id, j.date_earned))
                                else:
                                    result.append(j)
                    if len(result)>0:
                        if page and limit:
                            totalPages = math.ceil(len(result)/limit)
                            if page <= totalPages:
                                start = limit*(page-1)
                                result = result[start:start+limit]

                                return BadgesPageListType(badges=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                            else:
                                raise BadRequestException("invalid request; page provided exceeded total")
                        elif page == limit == None:
                            return BadgesPageListType(badges=result, page_info=PageInfoObject(nextPage= None, limit=None))
                        elif page is None:
                            raise BadRequestException("invalid request; limit cannot be provided without page")
                        elif limit is None:
                            raise BadRequestException("invalid request; page cannot be provided without limit")
                        
                    else:
                        return BadgesPageListType(badges=[], page_info=PageInfoObject(nextPage= None, limit=None))
                    
                    return result
                    # else:
                    #     raise NotFoundException("no badges associated with this user", 204)
            except (User.DoesNotExist, Badge.DoesNotExist):
                raise NotFoundException("userId provided not found", 404)
            except UserProfile.DoesNotExist:
                raise NotFoundException("profile for provided userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        return None

 #Get Badge by User Badge Id
    def resolve_userBadge(parent, info, **kwargs):
        userBadgeId = kwargs.get('userBadgeId')
        if userBadgeId is not None :
            userBadge = UserBadge.objects.using('default').get(user_badge_id=userBadgeId)
            try:
                i = Badge.objects.using('default').get(badge_id = userBadge.badge_id)
                return BadgeType(userBadgeId, i.badge_id, i.image, i.name, i.value, i.badge_type_id, userBadge.date_earned, userBadge.is_pinned)
            except (UserBadge.DoesNotExist, Badge.DoesNotExist):
                raise NotFoundException("userBadgeId provided not found", 404)
            except UserProfile.DoesNotExist:
                raise NotFoundException("profile for provided userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)


        # return result

 #Get Itineraries by User Id
    def resolve_userItineraries(parent, info, **kwagrs):
        id = kwagrs.get('userId') 
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')  
        result= []
        if id is not None:
            try:
                if User.objects.using('default').get(user_id = id) and UserProfile.objects.using('default').get(user_id=id):
                    for i in UserSharedItinerary.objects.using('default').filter(user_id=id):
                        result.append(ItineraryListType(i.user_shared_itinerary_id, i.date_created))
                    if result :
                        result.sort(key=lambda x:x.date_created, reverse=True)
                        # return result
                        if len(result)>0:
                            if page and limit:
                                totalPages = math.ceil(len(result)/limit)
                                if page <= totalPages:
                                    start = limit*(page-1)
                                    result = result[start:start+limit]

                                    return ItineraryPageListType(itineraries=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                                else:
                                    raise BadRequestException("invalid request; page provided exceeded total")
                            elif page == limit == None:
                                return ItineraryPageListType(itineraries=result, page_info=PageInfoObject(nextPage= None, limit=None))
                            elif page is None:
                                raise BadRequestException("invalid request; limit cannot be provided without page")
                            elif limit is None:
                                raise BadRequestException("invalid request; page cannot be provided without limit")
                        
                        else:
                            return ItineraryPageListType(itineraries=[], page_info=PageInfoObject(nextPage= None, limit=None))
                    else:
                        return ItineraryPageListType(itineraries=[], page_info=PageInfoObject(nextPage= None, limit=None))
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
            except UserProfile.DoesNotExist:
                raise NotFoundException("profile for provided userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)   
        return None

 #Get User By userId 
    def resolve_user(parent, info, **kwargs):
        authUserId = kwargs.get('authUserId')
        recipientUserId = kwargs.get('recipientUserId')
        if authUserId is not None:
            result = []
            try:
                if User.objects.using('default').get(user_id=authUserId):
                    try:
                        result1 = UserProfile.objects.using('default').get(user_id=authUserId)
                    except UserProfile.DoesNotExist:
                        raise NotFoundException("authUserId provided has not created a profile", 404)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid", 400)
        if recipientUserId is not None:
            result = []
            try:
                user2 = User.objects.using('default').get(user_id=recipientUserId)
                
                try:
                    result2 = UserProfile.objects.using('default').get(user_id=recipientUserId)
                    print(result2)
                    # try: 
                    #     isBlocked = UserBlocked.objects.using('default').get(user_id=authUserId, block_user_id=recipientUserId)
                    #     obj ={
                    #         "username": user2.username,
                    #         "avatar": user2.avatar,
                    #         "name": result2.name
                    #     }
                    #     return UserMainProfile(obj)
                    # except UserBlocked.DoesNotExist:
                    #     pass
                    try:
                        us = UserFollowing.objects.using('default').get(Q(user_id=authUserId) & Q(following_user_id=recipientUserId))
                        print(us)
                        print('-------user follwoing here')
                        result2.isFollowing = True
                    except UserFollowing.DoesNotExist:
                        result2.isFollowing = False
                    print(result2)
                    return result2
                except UserProfile.DoesNotExist:
                    raise NotFoundException("recipientUserId provided has not created a profile", 404)
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid", 400)
        return None

 #Get Following Aggregate
    def resolve_usersFollowingAggregate(parent, info, **kwargs):
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
                UserProfile.objects.using('default').get(user_id=userId)
                return aggregateObjectType(aggregate(count=UserFollowing.objects.using('default').filter(user_id=userId).count()))
            except UserProfile.DoesNotExist:
                raise NotFoundException("userId provided has not created a profile", 404)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400) 

 #Get Follower Aggregate
    def resolve_userFollowersAggregate(parent, info, **kwargs):
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
                UserProfile.objects.using('default').get(user_id=userId)
                return aggregateObjectType(aggregate(count=UserFollowing.objects.using('default').filter(following_user_id=userId).count()))
            except UserProfile.DoesNotExist:
                raise NotFoundException("userId provided has not created a profile", 404)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)  

 #Get Trips Booked Aggregate
    def resolve_tripsBookedAggregate(parent, info, **kwargs):
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
                UserProfile.objects.using('default').get(user_id=userId)
                return aggregateObjectType(aggregate(count=UserTrip.objects.using('default').filter(user_id=userId).count()))
            except UserProfile.DoesNotExist:
                raise NotFoundException("userId provided has not created a profile", 404)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)    

 #Get Post By Id   
    def resolve_post(parent, info, **kwargs):
        userId = kwargs.get('userId')
        id = kwargs.get('postId')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
                UserProfile.objects.using('default').get(user_id=userId)
            except UserProfile.DoesNotExist:
                raise NotFoundException("userId provided has not created a profile", 404)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if id is not None:
            try:
                if Post.objects.using('default').get(post_id=id):
                    result = Post.objects.using('default').filter(post_id=id).values()
                    post = result[0]
                    # # post['isFollowing'] = False
                    # try:
                    #     print(userId)
                    #     print(post['user_id'])
                    #     us = UserFollowing.objects.using('default').get(Q(user_id=userId) & Q(following_user_id=post['user_id']))
                    #     print(us)
                    #     print('-------following here')
                    #     post['isFollowing'] = True
                    # except UserFollowing.DoesNotExist:
                    #     post['isFollowing'] = False
                    isLiked = False
                    post['isLiked'] = None
                    try:
                        post_liked = PostLike.objects.using('default').get(Q(post_id=id) & Q(user_id=userId))
                        isLiked = True
                    except PostLike.DoesNotExist:
                        isLiked = False
                    post['isLiked']=isLiked
                    isSaved = False
                    post['isSaved']=None
                    try:
                        post_saved = PostSaved.objects.using('default').get(Q(post_id=id) & Q(user_id=userId))
                        isSaved = True
                    except PostSaved.DoesNotExist:
                        isSaved = False
                    post['isSaved']=isSaved
                    return post
            except Post.DoesNotExist:
                raise NotFoundException('postId provided not found', 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)
        return None

 #Get Comments By Post Id
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
                        comments.append(PostCommentListType(each.post_comment_id))#, user_output_obj, each.comment, each.number_of_likes,  each.date_created, len(reply_comment_output_obj), reply_comment_output_obj, hashtags, mentions))
                # comments.sort(key=lambda x:x.date_created, reverse=True)
                return comments
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

 #Get Comments By Post Comment Id
    def resolve_comment(parent, info, **kwagrs):
        id = kwagrs.get('postCommentId')
        authUserId = kwagrs.get('authUserId')
	    
        if id is not None:
            if authUserId:
                try:
                    User.objects.using('default').get(user_id=authUserId)
                    UserProfile.objects.using('default').get(user_id=authUserId)
                except UserProfile.DoesNotExist:
                    raise NotFoundException("authUserId provided has not created a profile", 404)
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
                    postLike = PostCommentLike.objects.using('default').get(post_comment_id=id,user_id=authUserId)
                    print(postLike)
                    postIsLiked = True
                except PostCommentLike.DoesNotExist:
                    print("exception")
                    postIsLiked = False
                # for each in PostComment.objects.using('default').filter(post_id=id):
                reply_comment_output_obj = []
                user_obj = User.objects.using('default').get(user_id=each.user_id)
                user_output_obj = OutputUserType(user_obj.user_id, user_obj.username, user_obj.avatar, user_obj.level)
                reply_comment_objs =[]
                reply_comment_objs += PostComment.objects.using('default').filter(comment_reply_id=id).values_list('post_comment_id', flat=True)
                print(reply_comment_objs)
                if reply_comment_objs !=[]:
                    for each_reply in reply_comment_objs:
                        # each_reply_obj = PostComment.objects.using('default').get(post_comment_id=each_reply)
                        reply_comment_output_obj.append(PostCommentReplyType(each_reply))
                    print(reply_comment_output_obj)
                elif reply_comment_objs == []:
                    reply_comment_output_obj = []
                # if each.comment_reply_id == None:
                    #Get Hashtags and Mentions
                    hashtags_word, hashtags = [], []
                    mentions_word, mentions = [], []
                    hashtags_word, mentions_word = extract_tags_mentions(each.comment)
                    for one_hashtag in hashtags_word:
                        try:
                            tag_obj = Tag.objects.using('default').get(name=one_hashtag)
                            hashtags.append(hashtagSection(tag_obj.name, tag_obj.tag_id))
                        except Tag.DoesNotExist:
                            pass
                    for one_mention in mentions_word:
                        try:
                            user_obj = User.objects.using('default').get(username=one_mention)
                            mentions.append(mentionSection(user_obj.username, user_obj.user_id))
                        except User.DoesNotExist:
                            mentions.append(mentionSection(one_mention, None))
                comments = PostCommentType(each.post_comment_id, user_output_obj, each.comment, aggregateObjectType(aggregate=aggregate(count=each.number_of_likes)),  each.date_created, aggregateObjectType(aggregate=aggregate(count=len(reply_comment_output_obj))), reply_comment_output_obj if len(reply_comment_output_obj)>=1 else None, hashtags, mentions, postIsLiked, False if len(reply_comment_output_obj)>=1 else True)
                
                # comments.sort(key=lambda x:x.date_created, reverse=True)
                return comments
            except PostComment.DoesNotExist:
                raise NotFoundException("postCommentId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postCommentId provided is invalid", 400)
        
 #Search Users
    """
        This API takes in input from user their user id and serach keyword to display the users who have created user profiles in the application.
    """
    def resolve_userResults(parent, info, **kwagrs):
        uid = kwagrs.get('userId')
        search_content = kwagrs.get('searchContent') 
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if uid is not None:
            try:
                user = UserProfile.objects.using('default').get(user_id=uid)
            except UserProfile.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if search_content is not None :
            if (search_content and search_content.strip()):
                client = redis_connect()
                search_history_cache = get_hashmap_from_cache(client, str(uid)+"_search_history")
                search_history_cache.put(search_content, datetime.datetime.now())
                print(search_history_cache.getAll())
                state = set_hashmap_to_cache(client, str(uid)+ "_search_history", search_history_cache)
                print(state)
            else:
                raise BadRequestException("invalid request; searchContent provided is empty", 400)
        else:
            raise BadRequestException("invalid request; searchContent provided is invalid", 400)
        
        username_objs = []
        if uid is not None and search_content is not None:
            username_objs += User.objects.using('default').filter(username__icontains=search_content).values_list('user_id', flat=True)
            # obj_list = UserProfile.objects.using('default').filter(Q(user_id__in = username_objs) | Q(name__icontains=search_content))
            print(username_objs)
        result =[]
        for each in username_objs:
            result.append({"user_id": each})
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return SearchUserPageListType(users=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return SearchUserPageListType(users=result, page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return SearchUserPageListType(users=[], page_info=PageInfoObject(nextPage= None, limit=None))

 #Search All Suggestions  
    # def resolve_searchAllSuggestions(parent, info, **kwagrs):
    #     uid = kwagrs.get('user_id')
    #     search_content = kwagrs.get('search_content')
    #     if uid is not None:
    #         try:
    #             user= User.objects.using('default').filter(user_id=uid)
    #             userProfile = UserProfile.objects.using('default').filter(user_id=uid)
    #             profiletags = UserProfileTagList.objects.using('default').filter(user_id=uid)
    #         except User.DoesNotExist:
    #             raise NotFoundException("userId provided is not found")
    #         except UserProfile.DoesNotExist:
    #             raise NotFoundException("userId provided has not created a profile")
    #         except UserProfileTagList.DoesNotExist:
    #             raise NotFoundException
    #     else:
    #         raise BadRequestException("invalid request; userId provided is invalid")
    #     if search_content is not None:
    #         json_search_content = {}
    #         json_content = {}


    #         #To collect all the Venue objects
    #         venues_obj_list = []
    #         json_content = {}
    #         for i in VenueExternal.objects.using('default').filter(name__icontains=search_content):
    #             json_content[i.venue_id] = i
    #         for i in VenueInternal.objects.using('default').filter(name__icontains=search_content):
    #             json_content[i.venue_id] = i

    #         for k, v json_content.items():
    #             if v.location_id == userProfile.location_id:
    #                 section = SearchAllSuggestionsVenueType(k, v.name)
    #                 venues_obj_list.append(section)
    #             if v.

    #         for k, v in json_content.items():
    #             section = SearchAllSuggestionsVenueType(k, v.name)
    #             venues_obj_list.append(section)
    #         json_search_content["venues"]=venues_obj_list

    #         #To collect all the Tag objects
    #         tags_obj_list =[]
    #         json_content = {}
    #         for i in Tag.objects.using('default').filter(name__icontains=search_content):
    #             json_content[i.tag_id] = i.name
    #         for k, v in json_content.items():
    #             section = SearchAllSuggestionsHashTagType(k, v)
    #             tags_obj_list.append(section)
    #         json_search_content["hashtags"]=tags_obj_list

    #         #To collect all the User objects
    #         users_obj_list =[]
    #         json_content = {}
    #         for i in User.objects.using('default').filter(username__icontains=search_content):
    #             json_content[i.user_id] = i.username
    #         for k, v in json_content.items():
    #             section = SearchAllSuggestionsUsersType(k, v)
    #             users_obj_list.append(section)
    #         json_search_content["users"]=users_obj_list
            
    #         #Converting to graphql format
    #         section = AllSearchSuggestionsType(json_search_content["hashtags"], json_search_content["venues"], json_search_content["users"])
            
            
    #         return section
    #     return None

 #Search Recommendations  
    def resolve_searchRecommendations(self, info, **kwagrs):
        def calculate_distance_between_points(location_a, location_b):
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
                user= User.objects.using('default').get(user_id=uid)
                userProfile = UserProfile.objects.using('default').get(user_id=uid)
                profileTags = UserProfileTagList.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
            except UserProfile.DoesNotExist:
                raise NotFoundException("userId provided has not created a profile")
            except UserProfileTagList.DoesNotExist:
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


            #To collect all the Venue objects
            venues_obj_list = {}
            json_content = {}
            profileTagNames = []
            for i in VenueExternal.objects.using('default').filter(name__icontains=search_content):
                json_content[i.venue_id] = i
            for i in VenueInternal.objects.using('default').filter(name__icontains=search_content):
                json_content[i.venue_id] = i

            if profileTags!= [] and profileTags:
                profileTagNames += UserProfileTag.objects.using('default').filter(user_profile_tag_id__in = profileTags.user_profile_tag_list).values_list('name', flat=True)
            else:
                profileTagNames = []
            # for k, v in json_content.items():
            #     section = SearchAllSuggestionsVenueType(k, v.name)
            #     venues_obj_list.append(section)
            
            #location with location weight --- minimum weight is the best
            for k, v in json_content.items():
                # print(calculate_distance_between_points(v.location, userProfile.location))
                json_content[k]={'object':v, 'location_weight':calculate_distance_between_points(v.location, userProfile.location)}
                # json_content['location_weight']= calculate_distance_between_points(json_content[i][1].location, )

            
            #weigh by number of profile tags present in object --- maximum value is best
            for k,v in json_content.items():
                # print(profileTagNames)
                # print(v['object'].name.split())
                set_profile_tags = set(v['object'].name.split()) & set(profileTagNames)
                print(set_profile_tags)
                if len(set_profile_tags)>0:
                    json_content[k]['profile_tags_weight'] = len(set_profile_tags)
                else:
                    json_content[k]['profile_tags_weight'] = 0
            print(json_content)
            
            #weigh by mutual interest with friends --- how much 
            followingUsers = []
            followingUsers += UserFollowing.objects.using('default').filter(user_id=uid).values_list('following_user_id')
            followingUsers = [each[0] for each in followingUsers]
            # print(followingUsers)
            #get following user's post
            followingUsersPosts = []
            followingUsersProfileTagIds = []
            followingUsersProfileTags = []
            followingUsersPosts += Post.objects.using('default').filter(user_id__in=followingUsers).values_list('post_id', 'venue_id')
            followingUsersProfileTagIds += UserProfileTagList.objects.using('default').filter(user_id__in=followingUsers).values_list('user_profile_tag_list')
            followingUsersProfileTagIds = [each[0] for each in followingUsersProfileTagIds]
            followingUsersProfileTagIds = [j for i in followingUsersProfileTagIds for j in i]
            # print(followingUsersProfileTagIds)
            followingUsersProfileTags += UserProfileTag.objects.using('default').filter(user_profile_tag_id__in = followingUsersProfileTagIds).values_list('name',  flat=True)

            #To collect all the following users venue objects
            following_venues_obj_list = {}
            following_json_content = {}
            followingUsersProfileTagNames = []
            venueids = []
            json_search_content["venues"] = []
            venueids= [each[1] for each in followingUsersPosts]
            for i in VenueExternal.objects.using('default').filter(Q(name__icontains=search_content)&Q(venue_id__in=venueids)):
                following_json_content[i.venue_id] = i
            for i in VenueInternal.objects.using('default').filter(Q(name__icontains=search_content)&Q(venue_id__in=venueids)):
                following_json_content[i.venue_id] = i

            #location with location weight --- minimum weight is the best
            for k, v in following_json_content.items():
                # print(calculate_distance_between_points(v.location, userProfile.location))
                following_json_content[k]={'object':v, 'location_weight':calculate_distance_between_points(v.location, userProfile.location)}
                # json_content['location_weight']= calculate_distance_between_points(json_content[i][1].location, )
            
            #weigh by number of profile tags present in object --- maximum value is best
            for k,v in following_json_content.items():
                # print(followingUsersProfileTags)
                # print(v['object'].name.split())
                following_set_profile_tags = set(v['object'].name.split()) & set(followingUsersProfileTags)
                # print(following_set_profile_tags)
                if len(following_set_profile_tags)>0:
                    following_json_content[k]['profile_tags_weight'] = len(following_set_profile_tags)
                else:
                    following_json_content[k]['profile_tags_weight'] = 0
            

            venues_obj_list = {**following_json_content, **json_content}

            ##Sorting the venue objects on location
            venues_obj_list = sorted(venues_obj_list.items(), key = lambda x: (getitem(x[1], 'location_weight'), (-getitem(x[1], 'profile_tags_weight'))))
            print(venues_obj_list)
            # for k,v in venue_obj_list.items():
            for k, v in venues_obj_list:
                json_search_content["venues"].append(SearchAllSuggestionsVenueType(v['object'].venue_id, v['object'].name))

            # json_search_content["venues"]=venues_obj_list
            

            #To collect all the Tag objects
            tags_obj_list =[]
            json_content = {}
            for i in Tag.objects.using('default').filter(name__icontains=search_content):
                json_content[i.tag_id] = i.name
            for k, v in json_content.items():
                section = SearchAllSuggestionsHashTagType(k, v)
                tags_obj_list.append(section)
            json_search_content["hashtags"]=tags_obj_list

            #To collect all the User objects
            users_obj_list =[]
            json_content = {}
            userFollowing =[]
            for i in User.objects.using('default').filter(username__icontains=search_content):
                # json_content[i.user_id] = {"username":i.username, "following_weight":0}
                try:
                    print(i.user_id)
                    print(uid)
                    userFollowing += UserFollowing.objects.using('default').filter(user_id=uid, following_user_id=i.user_id).values_list('following_user_id', flat=True)
                    print(userFollowing)
                    if userFollowing !=[]:
                        json_content[i.user_id] = {"username":i.username, "following_weight":1}
                    else:
                        raise Exception
                except :
                    json_content[i.user_id] = {"username":i.username, "following_weight":0}
            #Sort the json_content
            print(json_content)
            print(type(json_content))
            json_content = dict(sorted(json_content.items(), key = lambda x: (-getitem(x[1], 'following_weight'))))
            print(json_content)
            print(type(json_content))
            for k, v in json_content.items():
                section = SearchAllSuggestionsUsersType(k, v["username"])
                users_obj_list.append(section)
            json_search_content["users"]=users_obj_list
            
            #Converting to graphql format
            section = AllSearchSuggestionsType(json_search_content["hashtags"], json_search_content["venues"], json_search_content["users"])
            
            
            return section
        else:
            raise BadRequestException("searchContetnt provided is invalid")
        return None

 #Search All 
    def resolve_searchAll(parent, info, **kwagrs):
        
        def getCurrentCity(lat, lon):
            location = {
                "city":"Maple Grove",
                "state":"MN",
                "country":"US"
                }
            return location
        
        # def calculateVenueStayPrice(obj, date_venue_objs):

            #     for x in date_venue_objs:
            #         if x['venue_id'] == obj.venue_id:
            #             price = str(x['price'])  
                
            #     return price
        
        def createGrapheneTypeObject(obj):

            if obj['user'] is not None:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'], SearchFilterLocationType(obj['location']['city'], obj['location']['country'], obj['location']['lat'], obj['location']['long']), SearchFilterVenueObjectType(obj['venue']['venue_id'], obj['venue']['venue_type_id'], obj['venue']['venue_type_name']),  obj['thumbnail'], obj['name'], SearchFilterUserType(obj['user']['user_id'], obj['user']['username'], obj['user']['avatar'], obj['user']['level'], obj['user']['rating']))
            else:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'], SearchFilterLocationType(obj['location']['city'], obj['location']['country'], obj['location']['lat'], obj['location']['long']), SearchFilterVenueObjectType(obj['venue']['venue_id'], obj['venue']['venue_type_id'], obj['venue']['venue_type_name']), obj['thumbnail'], obj['name'], None)
            return one
        
        uid = kwagrs.get('userId')
        search_content = kwagrs.get('searchContent') 
        if uid is not None:
            pass
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if search_content is not None :
            # pass
            if (search_content and search_content.strip()):
                client = redis_connect()
                search_history_cache = get_hashmap_from_cache(client, str(uid)+"_search_history")
                if search_history_cache:
                    search_history_cache.put(search_content, datetime.datetime.now())
                    print(search_history_cache.getAll())
                    state = set_hashmap_to_cache(client, str(uid)+ "_search_history", search_history_cache)
                    print(state)
                else:
                    key =  str(uid)+ "_search_history"
                    search_history_cache = LRUCache(35)
                    # search_history_cache.put()
                    search_cache = set_hashmap_to_cache(client, key, search_history_cache)
                    search_history_cache.put(search_content, datetime.datetime.now())
                    print(search_history_cache.getAll())
                    state = set_hashmap_to_cache(client, key, search_history_cache)
                    print(state)
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
        location=kwagrs.get('location')
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
        default_location = location#getCurrentCity(lat,lon)
        if default_location is None:
            raise NotFoundException("location is incorrect", 404)
        today = date.today()
        tomorrow = today+timedelta(days=1)
        check_in_date, check_out_date = date( int(check_in_date.split('-')[0]),  int(check_in_date.split('-')[1]),  int(check_in_date.split('-')[2])), date( int(check_out_date.split('-')[0]),  int(check_out_date.split('-')[1]),  int(check_out_date.split('-')[2]))
        default_dates = [check_in_date, check_out_date]
        
        if uid is not None and search_content is not None:
            """
                User Results
            """
            username_objs = []
            username_objs += User.objects.using('default').filter(username__icontains=search_content).values_list('user_id', flat=True)
            # obj_list = UserProfile.objects.using('default').filter(Q(user_id__in = username_objs) | Q(name__icontains=search_content))
            json_content["users"] = username_objs

        
           #Stays Results
           
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

           #Experiences
            """
                    Things To Do Results
            """
            print("Experiences")
            locations  =[]
            locations += Location.objects.using('default').filter(city=default_location["city"], country=default_location["country"]).values_list('location_id', flat=True)
            print(locations)
            search_venue_objs = []
            location_obj = []
            json_result = []
            venue_objs = []
            date_venue_objs = []
            filter_date_objs = []
            location_venue_objs = []
            post_objs = []

            #Collecting Venue_Id with respect to search keywords
            for i in VenueInternal.objects.using('default').filter(Q(name__icontains=search_content, type_id=1 ) |Q(description__icontains=search_content, type_id=1)).values_list('venue_id'):
                search_venue_objs.append(i[0])
            for i in VenueExternal.objects.using('default').filter(Q(name__icontains=search_content, type_id=1 ) |Q(description__icontains=search_content, type_id=1)).values_list('venue_id'):
                search_venue_objs.append(i[0])

            #Collectting venue_id with respect to the location given    
            for i in VenueInternal.objects.using('default').filter(location_id__in=locations,type_id=1).values_list('venue_id') :
                location_venue_objs.append(i[0])
            for i in VenueExternal.objects.using('default').filter(location_id__in=locations, type_id=1).values_list('venue_id'):
                location_venue_objs.append(i[0])

            #Collecting venue_id with respect to the date given
            venue_type="Experiences" 
            filter_date_objs, date_venue_objs = getDateFilteredVenueObjects(default_dates, venue_type)

            #Finding the common venue_id which is match the search keywords,
            #location given and date availablitiy.
            print(search_venue_objs)
            
            print(location_venue_objs)
            venue_objs = list(set(search_venue_objs).intersection(set(location_venue_objs)))
            print(date_venue_objs)
            print(venue_objs)
            venue_objs = list(set(venue_objs).intersection(set(date_venue_objs)))
            print("Venues")
            print(venue_objs)
            # #Creating Json Objects for each result
            json_result = []
            for obj in venue_objs:

                try:
                    obj = VenueExternal.objects.using('default').get(venue_id=obj)
                except VenueExternal.DoesNotExist:
                    obj = VenueInternal.objects.using('default').get(venue_id=obj)
                print(obj)
                
                try:
                    # post_venue_id = PostVenue.objects.using('default').get(venue_id=obj.venue_id)
                    # print(post_venue_id)
                    print("posts")
                    post_objs = Post.objects.using('default').filter(venue_id=obj.venue_id)
                    print(post_objs)
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
                            "is_post":True,
                            "template":{
                                "id":str(obj_post.post_id),
                                "type":1
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
                            "is_post":False,
                            "template":{
                                "id":obj.venue_id,
                                "type":2
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
                            "is_post":False,
                            "template":{
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

           #Transportation
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
           #To collect all the Tag objects
            # tags_obj_list =[]
            # for i in Tag.objects.using('default').filter(name__icontains=search_content):
            #     json_content[i.tag_id] = i.name
            # for k, v in json_content.items():
            #     section = SearchAllSuggestionsHashTagType(k, v)
            #     tags_obj_list.append(section)
            # json_content["hashtags"]=tags_obj_list

           #Converting into graphene objects
            
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
            print(json_content["users"])
            for each in json_content["users"]:
                result_users.append({"user_id": each})

            # if len(json_content["hashtags"]) > 3:
            #     json_content["hashtags"] = json_content["hashtags"][0:3]   

            return AllSearchType(result_users, result_thingstodo)


        return None

 #Search Stays with Filter
    def resolve_stayResults(parent, info, **kwagrs):
        

        def createGrapheneTypeObject(obj):
            print(obj)
            if obj['user'] is not None:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'], SearchFilterLocationType(obj['location']['city'], obj['location']['country'], obj['location']['lat'], obj['location']['long']), SearchFilterVenueObjectType(obj['venue']['venue_id'], obj['venue']['venue_type_id'], obj['venue']['venue_type_name']),  obj['thumbnail'], obj['name'], SearchFilterUserType(obj['user']['user_id'], obj['user']['username'], obj['user']['avatar'], obj['user']['level'], obj['user']['rating']))
            else:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'], SearchFilterLocationType(obj['location']['city'], obj['location']['country'], obj['location']['lat'], obj['location']['long']), SearchFilterVenueObjectType(obj['venue']['venue_id'], obj['venue']['venue_type_id'], obj['venue']['venue_type_name']), obj['thumbnail'], obj['name'], None)
            return one
        
     #User Id
        uid = kwagrs.get('userId')
        if uid is not None: 
            pass
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
     #Search Content
        search_content = kwagrs.get('searchContent')
        if search_content is not None :
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
     #Location
        search_location = kwagrs.get('location')
        if search_location is not None  :
            pass
        else:
            raise BadRequestException("invalid request; location provided is invalid", 400)
        
        if (search_location and search_location.strip()):
            pass 
        else:
            raise BadRequestException("invalid request; location provided is empty", 400)
     #Check in Date
        search_checkin_date = kwagrs.get('checkInDate')
        if search_checkin_date is not None and (search_checkin_date and search_checkin_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkInDate provided is invalid", 400)
     #Check Out Date
        search_checkout_date = kwagrs.get('checkOutDate') 
        if search_checkout_date is not None and (search_checkout_date and search_checkout_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkOutDate provided is invalid", 400)
     #Filter Content
        filter_content = kwagrs.get('filterContent')
        if filter_content is not None:
            input_json_filter_content = {
                "noOfGuests":filter_content['noOfGuests'],
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
        
     #Logic
        json_search_content = {}
        json_content = {}
        objs_list = []
        
        
        
        filtered_venue_id_by_amenity = []
        filtered_venue_id_by_staytype = []
        filtered_venue_id_by_price = []
        
        #Filter by Location
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
        state = search_location.split(',')[1].replace(' ','')
        locations = Location.objects.using('default').filter(city=city, state=state).values('location_id')
        i = 0
        
        #Collecting Venue_Id with respect to search keywords
        for i in VenueInternal.objects.using('default').filter(name__icontains=kwagrs.get('searchContent'), type_id=2).values_list('venue_id'):
            search_venue_objs.append(i[0])
        for i in VenueExternal.objects.using('default').filter(name__icontains=kwagrs.get('searchContent'), type_id=2).values_list('venue_id'):
            search_venue_objs.append(i[0])

        #Collectting venue_id with respect to the location given    
        for i in VenueInternal.objects.using('default').filter(location_id__in=locations,type_id=2).values_list('venue_id') :
            location_venue_objs.append(i[0])
        for i in VenueExternal.objects.using('default').filter(location_id__in=locations, type_id=2).values_list('venue_id'):
            location_venue_objs.append(i[0])

        #Collecting venue_id with respect to the date given 
        dates_in_the_range = dates_between(search_checkin_date, search_checkout_date)
        filter_date_objs, date_venue_objs = getDateFilteredVenueObjects(dates_in_the_range, "Stays")

        #Finding the common venue_id which is match the search keywords,
        #location given and date availablitiy.
        venue_objs = list(set(search_venue_objs).intersection(set(location_venue_objs)))
        venue_objs = list(set(venue_objs).intersection(set(date_venue_objs)))

        print(venue_objs)
        for obj in venue_objs:

            try:
                obj = VenueExternal.objects.using('default').get(venue_id=obj)
            except VenueExternal.DoesNotExist:
                obj = VenueInternal.objects.using('default').get(venue_id=obj)
            print(obj)
            
            try:
                post_objs = Post.objects.using('default').filter(venue_id=obj.venue_id)
                print(post_objs)
                if post_objs.exists():
                    for obj_post in post_objs:
                        print(obj_post)
                        location = Location.objects.using('default').get(location_id=obj.location_id)
                        user = User.objects.using('default').get(user_id=obj_post.user_id)
                        price = calculateVenueStayPrice(obj, filter_date_objs)
                        json_obj = {
                            "is_post":True,
                            "price":str(price) if price is not None else None,
                            "location":{
                                "city":city,
                                "country":location.country,
                                "lat":str(location.latitude),
                                "long":str(location.longitude)
                                },
                            "name":obj.name,
                            "venue":{
                                "venue_id":obj.venue_id,
                                "venue_type_id":obj.type_id,
                                "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                                },
                            "thumbnail":obj.thumbnail,
                            "user":{
                                "user_id":user.user_id,
                                "username":user.username,
                                "avatar":user.avatar,
                                "level":user.level,
                                "rating":str(obj_post.user_rating)
                                }
                        }
                        json_result.append(json_obj)
                else:
                    location = Location.objects.using('default').get(location_id=obj.location_id)
                    price = calculateVenueStayPrice(obj, filter_date_objs)
                    json_obj = {
                            "is_post":False,
                            "price":str(price) if price is not None else None,
                            "location":{
                                "city":city,
                                "country":location.country,
                                "lat":str(location.latitude),
                                "long":str(location.longitude)
                            },
                            "name":obj.name,
                            "venue":{
                                "venue_id":obj.venue_id,
                                "venue_type_id":obj.type_id,
                                "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                                },
                            "thumbnail":obj.thumbnail,
                            "user":None
                        }
                    json_result.append(json_obj)
                        
            except (Post.DoesNotExist):
                location = Location.objects.using('default').get(location_id=obj.location_id)
                price = calculateVenueStayPrice(obj, filter_date_objs)
                json_obj = {
                        "is_post":False,
                        "price":str(price) if price is not None else None,
                        "location":{
                            "city":city,
                            "country":location.country,
                            "lat":str(location.latitude),
                            "long":str(location.longitude)
                            },
                        "name":obj.name,
                        "venue":{
                                "venue_id":obj.venue_id,
                                "venue_type_id":obj.type_id,
                                "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                            },
                        "thumbnail":obj.thumbnail,
                        "user":None
                    }
                json_result.append(json_obj)
        
        
        one_json = filterStayVenueObjs(json_result, input_json_filter_content) 
        print(one_json) 
        one_json = [createGrapheneTypeObject(x) for x in one_json]
        
        return one_json

        return None

 #Search Experiences with Filter
    def resolve_experienceResults(parent, info, **kwagrs):
        
        def createGrapheneTypeObject(obj):

            if obj['user'] is not None:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'], SearchFilterLocationType(obj['location']['city'], obj['location']['country'], obj['location']['lat'], obj['location']['long']), SearchFilterVenueObjectType(obj['venue']['venue_id'], obj['venue']['venue_type_id'], obj['venue']['venue_type_name']),  obj['thumbnail'], obj['name'], SearchFilterUserType(obj['user']['user_id'], obj['user']['username'], obj['user']['avatar'], obj['user']['level'], obj['user']['rating']))
            else:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'], SearchFilterLocationType(obj['location']['city'], obj['location']['country'], obj['location']['lat'], obj['location']['long']), SearchFilterVenueObjectType(obj['venue']['venue_id'], obj['venue']['venue_type_id'], obj['venue']['venue_type_name']), obj['thumbnail'], obj['name'], None)
            return one
       #User Id
        uid = kwagrs.get('userId')
        if uid is not None: 
            pass
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
       #Search Content
        search_content = kwagrs.get('searchContent')
        if search_content is not None :
           # client = redis_connect()
            # search_history_cache = get_hashmap_from_cache(client, str(uid)+"_search_history")
            # search_history_cache.put(search_content, datetime.datetime.now())
            # print(search_history_cache.getAll())
            # state = set_hashmap_to_cache(client, str(uid)+ "_search_history", search_history_cache)
            # print(state)
            pass
        else:
            raise BadRequestException("invalid request; searchContent provided is invalid", 400)
        if (search_content and search_content.strip()):
            pass
        else:
            raise BadRequestException("invalid request; searchContent provided is empty", 400)
       #Search Location
        search_location = kwagrs.get('location')
        if search_location is not None and (search_location and search_location.strip()):
            pass
        else:
            raise BadRequestException("invalid request; searchLocation provided is invalid", 400)
       #Search Check In Date
        search_checkin_date = kwagrs.get('checkInDate')
        if search_checkin_date is not None and (search_checkin_date and search_checkin_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkInDate provided is invalid", 400)
       #Search Check Out Date
        search_checkout_date = kwagrs.get('checkOutDate') 
        if search_checkout_date is not None and (search_checkout_date and search_checkout_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkOutDate provided is invalid", 400)
       #Filter Content 
        filter_content = kwagrs.get('filterContent')
        if filter_content is not None:
            input_json_filter_content = {
                "categories": filter_content['categories'],
                "time_of_day": filter_content['timeOfDay'],
                # "duration": filter_content['duration'],
                "max_price": filter_content['pricing'].max if filter_content['pricing'].max != 10000 else 10000,
                "min_price": filter_content['pricing'].min if filter_content['pricing'].min != 0 else 0,
                "rating": filter_content['userRatings'],
                "noOfGuests": filter_content['noOfGuests'],
                "sort_by": filter_content['sortBy']

            }


        # no_of_guests = kwagrs.get('noOfGuests')
        # if no_of_guests is not None :
        #     pass
        # else:
        #     raise BadRequestException("invalid request; noOfGuests provided is invalid", 400)
        
        #page
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')

        try:
            user = User.objects.using('default').get(user_id=uid)
        except User.DoesNotExist:
            raise NotFoundException("userId provided not found", 404)

       #Logic
        if (uid is not None) and (search_content is not None) and input_json_filter_content:

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
            state = search_location.split(',')[1].replace(' ','')
            locations = Location.objects.using('default').filter(city=city, state=state).values('location_id')
            i = 0

            #Collecting Venue_Id with respect to search keywords
            for i in VenueInternal.objects.using('default').filter(Q(name__icontains=search_content, type_id=1 ) |Q(description__icontains=search_content, type_id=1)).values_list('venue_id'):
                search_venue_objs.append(i[0])
            for i in VenueExternal.objects.using('default').filter(Q(name__icontains=search_content, type_id=1 ) |Q(description__icontains=search_content, type_id=1)).values_list('venue_id'):
                search_venue_objs.append(i[0])

            #Collectting venue_id with respect to the location given    
            for i in VenueInternal.objects.using('default').filter(location_id__in=locations, type_id=1).values_list('venue_id') :
                location_venue_objs.append(i[0])
            for i in VenueExternal.objects.using('default').filter(location_id__in=locations, type_id=1).values_list('venue_id'):
                location_venue_objs.append(i[0])

            #Collecting venue_id with respect to the date given
            venue_type="Experiences" 
            dates_in_the_range = dates_between(search_checkin_date, search_checkout_date)
            filter_date_objs, date_venue_objs = getDateFilteredVenueObjects(dates_in_the_range, venue_type)
            print(date_venue_objs)
            #Finding the common venue_id which is match the search keywords,
            #location given and date availablitiy.
            print(search_venue_objs)
            print(location_venue_objs)
            venue_objs = list(set(search_venue_objs).intersection(set(location_venue_objs)))

            venue_objs = list(set(venue_objs).intersection(set(date_venue_objs)))

           
            # #Creating Json Objects for each result
            json_result = []
            for obj in venue_objs:

                try:
                    obj = VenueExternal.objects.using('default').get(venue_id=obj)
                except VenueExternal.DoesNotExist:
                    obj = VenueInternal.objects.using('default').get(venue_id=obj)
                print(obj)
                
                try:
                    # post_venue_id = PostVenue.objects.using('default').get(venue_id=obj.venue_id)
                    # print(post_venue_id)
                    post_objs = Post.objects.using('default').filter(venue_id=obj.venue_id)
                    print(post_objs)
                    # if post_objs.exists():
                    for obj_post in post_objs:
                        location = Location.objects.using('default').get(location_id=obj.location_id)
                        user = User.objects.using('default').get(user_id=obj_post.user_id)
                        price = calculateVenueStayPrice(obj, filter_date_objs)
                        json_obj = {
                            "is_post":True,
                            "template":{
                                "id":obj_post.post_id,
                                "type":1
                            },
                            "price":str(price) if price is not None else None,
                            "location":{
                                "city":location.city,
                                "country":location.country,
                                "lat":str(location.latitude),
                                "long":str(location.longitude)
                                },
                            "name":obj.name,
                            "venue":{
                                "venue_id":obj.venue_id,
                                "venue_type_id":obj.type_id,
                                "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                                },
                            "thumbnail":obj.thumbnail,
                            "user":{
                                "user_id":user.user_id,
                                "username":user.username,
                                "avatar":user.avatar,
                                "level":user.level,
                                "rating":str(obj_post.user_rating)
                                }
                            }
                        json_result.append(json_obj)
                    # else:
                    location = Location.objects.using('default').get(location_id=obj.location_id)
                    price = calculateVenueStayPrice(obj, filter_date_objs)
                    json_obj = {
                            "is_post":False,
                            "template":{
                                "id":obj.venue_id,
                                "type":2
                            },
                            "price":str(price) if price is not None else None,
                            "location":{
                                "city":location.city,
                                "country":location.country,
                                "lat":str(location.latitude),
                                "long":str(location.longitude)
                            },
                            "name":obj.name,
                            "venue":{
                                "venue_id":obj.venue_id,
                                "venue_type_id":obj.type_id,
                                "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                                },
                            "thumbnail":obj.thumbnail,
                            "user":None
                        }
                    json_result.append(json_obj)
                            
                except (Post.DoesNotExist):
                    location = Location.objects.using('default').get(location_id=obj.location_id)
                    price = calculateVenueStayPrice(obj, filter_date_objs)
                    json_obj = {
                            "is_post":False,
                            "template":{
                                "id":obj.venue_id,
                                "type":2
                            },
                            "price":str(price) if price is not None else None,
                            "location":{
                                "city":location.city,
                                "country":location.country,
                                "lat":str(location.latitude),
                                "long":str(location.longitude)
                                },
                            "name":obj.name,
                            "venue":{
                                    "venue_id":obj.venue_id,
                                    "venue_type_id":obj.type_id,
                                    "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                                },
                            "thumbnail":obj.thumbnail,
                            "user":None
                        }
                    json_result.append(json_obj)
            # json_content["thingstodo"] = json_result

            one_json = filterExperienceVenueObjs(json_result, input_json_filter_content)  
            # one_json = [createGrapheneTypeObject(x) for x in one_json]
            result =[]
            print(one_json)
            for each_obj in one_json:
                print(each_obj["template"])
                result.append({"is_post": each_obj["is_post"], "template":each_obj["template"]})
                
            # result.append(SearchAllExperienceListType(is_post=each_obj['is_post'], template=SearchListTemplateType(id=each_obj["template"]["id"], type=each_obj["template"]["type"])))
            result_page = []
            if len(result)>0:
                if page and limit:
                    totalPages = math.ceil(len(result)/limit)
                    if page <= totalPages:
                        start = limit*(page-1)
                        result_page = result[start:start+limit]

                        return SearchAllExperienceListType(experiences=[SearchAllExperienceType(is_post=result['is_post'], template=SearchListTemplateType(id=result["template"]["id"], type=result["template"]["type"])) for result in result_page], page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                    else:
                        raise BadRequestException("invalid request; page provided exceeded total")
                elif page == limit == None:
                    return SearchAllExperienceListType(experiences=[SearchAllExperienceType(is_post=result['is_post'], template=SearchListTemplateType(id=result["template"]["id"], type=result["template"]["type"])) for result in result_page], page_info=PageInfoObject(nextPage= None, limit=None))
                elif page is None:
                    raise BadRequestException("invalid request; limit cannot be provided without page")
                elif limit is None:
                    raise BadRequestException("invalid request; page cannot be provided without limit")
                
            else:
                return SearchAllExperienceListType(experiences=[], page_info=PageInfoObject(nextPage= None, limit=None))
            return result

 #Search Transportation with Filter 
    def resolve_transportationResults(parent, info, **kwagrs):
        def createGrapheneTypeObject(obj):

            if obj['user'] is not None:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'], SearchFilterLocationType(obj['location']['city'], obj['location']['country'], obj['location']['lat'], obj['location']['long']), SearchFilterVenueObjectType(obj['venue']['venue_id'], obj['venue']['venue_type_id'], obj['venue']['venue_type_name']),  obj['thumbnail'], obj['name'], SearchFilterUserType(obj['user']['user_id'], obj['user']['username'], obj['user']['avatar'], obj['user']['level'], obj['user']['rating']))
            else:
                one = SearchStaysFilterValueType(obj['is_post'], obj['price'], SearchFilterLocationType(obj['location']['city'], obj['location']['country'], obj['location']['lat'], obj['location']['long']), SearchFilterVenueObjectType(obj['venue']['venue_id'], obj['venue']['venue_type_id'], obj['venue']['venue_type_name']), obj['thumbnail'], obj['name'], None)
            return one
       #User ID
        uid = kwagrs.get('userId')
        if uid is not None: 
            pass
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
       #Search Content
        search_content = kwagrs.get('searchContent')
        if search_content is not None :
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
       #Pick up Location
        pickup_location = kwagrs.get('pickupLocation')
        if pickup_location is not None  :
            pass
        else:
            raise BadRequestException("invalid request; pickupLocation provided is invalid", 400)
    
       #Drop off Location
        dropoff_location = kwagrs.get('dropoffLocation')
        if dropoff_location is not None  :
            pass
        else:
            raise BadRequestException("invalid request; dropoffLocation provided is invalid", 400)
        
       #Check In Date
        search_checkin_date = kwagrs.get('checkInDate')
        if search_checkin_date is not None and (search_checkin_date and search_checkin_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkInDate provided is invalid", 400)
       #Check Out Date
        search_checkout_date = kwagrs.get('checkOutDate') 
        if search_checkout_date is not None and (search_checkout_date and search_checkout_date.strip()):
            pass
        else:
            raise BadRequestException("invalid request; checkOutDate provided is invalid", 400)
       #Check In Time
        search_checkin_time = kwagrs.get('checkInTime')
        if search_checkin_time is not None and (search_checkin_time and search_checkin_time.strip()):
            search_checkin_time = datetime.time(int(search_checkin_time.split(':')[0]), int(search_checkin_time.split(':')[1]), int(search_checkin_time.split(':')[2]))    
        else:
            raise BadRequestException("invalid request; checkInTime provided is invalid", 400)
       #Check Out Time
        search_checkout_time = kwagrs.get('checkOutTime') 
        if search_checkout_time is not None and (search_checkout_time and search_checkout_time.strip()):
            search_checkout_time = datetime.time(int(search_checkout_time.split(':')[0]), int(search_checkout_time.split(':')[1]), int(search_checkout_time.split(':')[2]))    
        else:
            raise BadRequestException("invalid request; checkOutTime provided is invalid", 400)
       #Filter Content
        filter_content = kwagrs.get('filterContent')
        if filter_content is not None:
            input_json_filter_content = {
                
                "vehicle_type": filter_content['vehicleType'],
                "max_price": filter_content['pricing'].max if filter_content['pricing'].max != 10000 else 10000,
                "min_price": filter_content['pricing'].min if filter_content['pricing'].min != 0 else 0,
                "sort_by": filter_content['sortBy'],
                "capacity":filter_content['capacity']

            }

        
        try:
            user = User.objects.using('default').get(user_id=uid)
        except User.DoesNotExist:
            raise NotFoundException("userId provided not found", 404)
        print(input_json_filter_content["max_price"])

       #Logic      
        json_result = []

        locations = Location.objects.using('default').filter(city__in=[pickup_location.city, dropoff_location.city]).values('location_id')
        search_venue_objs = []
        location_venue_objs = []

        #Collecting Venue_Id with respect to search keywords
        for i in VenueInternal.objects.using('default').filter(name__icontains=search_content, type_id=3).values_list('venue_id'):
            search_venue_objs.append(i[0])
        for i in VenueExternal.objects.using('default').filter(name__icontains=search_content, type_id=3).values_list('venue_id'):
            search_venue_objs.append(i[0])

        #Collectting venue_id with respect to the location given    
        for i in VenueInternal.objects.using('default').filter(location_id__in=locations,type_id=3).values_list('venue_id') :
            location_venue_objs.append(i[0])
        for i in VenueExternal.objects.using('default').filter(location_id__in=locations, type_id=3).values_list('venue_id'):
            location_venue_objs.append(i[0])

        #Collecting venue_id with respect to the date given
        filter_date_objs, date_venue_objs = getDateFilteredVenueObjects([search_checkin_date, search_checkout_date, search_checkout_time, search_checkout_time], "Transportations")

        #Finding the common venue_id which is match the search keywords,
        #location given and date availablitiy.
        print(search_venue_objs)
        print(location_venue_objs)
        venue_objs = list(set(search_venue_objs).intersection(set(location_venue_objs)))
        print(date_venue_objs)
        venue_objs = list(set(venue_objs).intersection(set(date_venue_objs)))
        print("Car Rentl")
        print(venue_objs)

        for obj in venue_objs:
            try:
                obj = VenueExternal.objects.using('default').get(venue_id=obj)
            except VenueExternal.DoesNotExist:
                obj = VenueInternal.objects.using('default').get(venue_id=obj)

            location = Location.objects.using('default').get(location_id=obj.location_id)
            price = calculateVenueStayPrice(obj, filter_date_objs)
            json_obj = {
                "is_post":False,
                "price":str(price) if price is not None else None,
                "location":{
                    "city":location.city,
                    "country":location.country,
                    "lat":str(location.latitude),
                    "long":str(location.longitude)
                    },
                "name":obj.name,
                "venue":{
                    "venue_id":obj.venue_id,
                    "venue_type_id":obj.type_id,
                    "venue_type_name":VenueType.objects.using('default').get(venue_type_id=obj.type_id).name
                    },
                "thumbnail":obj.thumbnail,
                "user":None
                }
            json_result.append(json_obj)
        
        
    #Filtering Logic
        one_json = filterTransportationVenueObjs(json_result, input_json_filter_content)  
        one_json = [createGrapheneTypeObject(x) for x in one_json]
        return one_json

 #Search Tags
    def resolve_searchTags(self, info, **kwargs):
    #User Id
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
    #Search Content
        search_content = kwargs.get('searchContent')
        if search_content is not None :
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
        
        post_tag_objs = PostTag.objects.using('default').filter(tag_id__name__icontains=search_content).values_list('post_tag_id','post_id','tag_id')
        # print(post_tag_objs)
        post_obj_dict = {}
        for each in post_tag_objs:
            if each[1] >= 35:
                tag_name = Tag.objects.using('default').get(tag_id=each[2])
                try:
                    if tag_name in post_obj_dict.keys():
                        if len(post_obj_dict[tag_name]) <9: 
                            post_obj_dict[tag_name].append(Post.objects.using('default').get(post_id = each[1]))
                            # post_obj_list.append( Post.objects.using('default').get(post_id = each[1]))
                        else:
                            pass
                    else:
                        post_obj_dict[tag_name]=[Post.objects.using('default').get(post_id = each[1])]
                except Post.DoesNotExist:
                    pass
            else:
                pass
        # print(post_obj_dict)
        for each in post_obj_dict.items():
            # print(eac)
            # print(len(each[1]))
            result.append(SearchTagsValueType(each[0].tag_id, each[0].name, each[1]))
        
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return SearchTagsValueListType(tags=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return SearchTagsValueListType(tags=result, page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return SearchTagsValueListType(tags=[], page_info=PageInfoObject(nextPage= None, limit=None))

 #Search Tag Posts
    def resolve_tagPosts(self, info, **kwargs):
        #User Id
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
        #Tag Id
        tagId = kwargs.get('tagId')
        if tagId is not None: 
            try:
                Tag.objects.using('default').get(tag_id=tagId)
            except Tag.DoesNotExist:
                raise NotFoundException("tagId provided is not found")
        else:
            raise BadRequestException("invalid request; tagId provided is invalid", 400)   

        tag_name = Tag.objects.using('default').get(tag_id=tagId)
        post_tag_objs = PostTag.objects.using('default').filter(tag_id__tag_id=tagId).values_list('post_tag_id','post_id','tag_id')
        posts = []
        for each in post_tag_objs:
            try:
                posts.append(PostListType(Post.objects.using('default').get(post_id = each[1]).post_id))
                    # post_obj_list.append( Post.objects.using('default').get(post_id = each[1]))
            except Post.DoesNotExist:
                pass 
        result = posts
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return SearchTagsValuePostListType(tag_id=tag_name.tag_id, hashtag=tag_name.name, posts=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return SearchTagsValuePostListType(tag_id=tag_name.tag_id, hashtag=tag_name.name, posts=result,  page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return SearchTagsValuePostListType(tag_id=tag_name.tag_id, hashtag=tag_name.name, posts=[],  page_info=PageInfoObject(nextPage= None, limit=None))
        return SearchTagsValueType(tag_name.tag_id, tag_name.name, posts)

 #Search Venues 
    def resolve_searchVenues(self, info, **kwargs):
       #User Id
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
       #Search Content
        search_content = kwargs.get('searchContent')
        if search_content is not None :
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
        venue_internal_objs = VenueInternal.objects.using('default').filter(name__icontains=search_content).values_list('venue_id', 'location_id', 'type', 'name', 'thumbnail', 'max_guests', 'price_id')
        venue_external_objs = VenueExternal.objects.using('default').filter(name__icontains= search_content).values_list('venue_id', 'location_id', 'type', 'name', 'thumbnail', 'max_guests', 'price_id')
        
        print(venue_internal_objs)
        print(venue_external_objs)
        posts = []
        for each in venue_internal_objs:
            type = VenueType.objects.using('default').get(venue_type_id=each[2]).name
            location = Location.objects.using('default').get(location_id =each[1])
            print(location)
            place_obj = PlaceObjectType(each[0], each[3], type, False, LocationObjectType(location.city, location.state, location.country, location.latitude, location.longitude))
            posts = Post.objects.using('default').filter(venue_id=each[0])
            result.append(SearchPlacesValueType(place_obj,posts[:9]))
        
        print(result)
        posts = []
        for each in venue_external_objs:
            type = VenueType.objects.using('default').get(venue_type_id=each[2]).name
            location = Location.objects.using('default').get(location_id =each[1])
            print(location)
            place_obj = PlaceObjectType(each[0], each[3], type, True, LocationObjectType(location.city, location.state, location.country, location.latitude, location.longitude))
            posts = Post.objects.using('default').filter(venue_id=each[0]) 
            result.append(SearchPlacesValueType(place_obj,posts[:9]))
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return SearchPlacesValueListType(venues=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return SearchPlacesValueListType(venues=result, page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return SearchPlacesValueListType(venues=[], page_info=PageInfoObject(nextPage= None, limit=None))
        return result

 #Search Venue Posts
    def resolve_venuePosts(self, info, **kwargs):
        #User Id
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
        #Venue Id
        venueId = kwargs.get('venueId')
        if venueId is not None: 
            try:
                Venue.objects.using('default').get(venue_id=venueId)
            except Venue.DoesNotExist:
                raise NotFoundException("venueId provided is not found")
        else:
            raise BadRequestException("invalid request; venueId provided is invalid", 400)
        #is_external 
        isExternal = kwargs.get('isExternal')
        if isExternal is not None:
            if not isExternal:
                try:
                    venue_obj = VenueInternal.objects.using('default').get(venue_id=venueId)
                except VenueInternal.DoesNotExist:
                    raise BadRequestException("invalid request; venueId provided doesnt correspond with isExternal field")
            else:
                try:
                    venue_obj = VenueExternal.objects.using('default').get(venue_id = venueId)
                except VenueExternal.DoesNotExist:
                    raise BadRequestException("invalid request; venueId provided doesnt correspond with isExternal field")
        else:
            raise BadRequestException("invalid request; isExternal provided provided is invalid", 400)
        
        type = VenueType.objects.using('default').get(venue_type_id=venue_obj.type_id).name
        location = Location.objects.using('default').get(location_id =venue_obj.location_id)
        print(location)
        place_obj = PlaceObjectType(venue_obj.venue_id, venue_obj.name, type, isExternal, LocationObjectType(location.city, location.state, location.country, location.latitude, location.longitude))
        posts = [] 

        for i in Post.objects.using('default').filter(venue_id=venueId).order_by('-date_created'):
            posts.append(PostListType(i.post_id))
        result = posts
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return SearchPlacesValuePostListType(venue=place_obj, posts=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return SearchPlacesValuePostListType(venue=place_obj, posts=result,  page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return SearchPlacesValuePostListType(venue=place_obj, posts=[],  page_info=PageInfoObject(nextPage= None, limit=None))
        # return SearchPlacesValueType(place_obj,posts)

 #Explore ALL   
    def resolve_exploreAll(parent, info, **kwagrs):

        def dist(lat1, long1, lat2, long2):
            """
            Calculate the great circle distance between two points 
            on the earth (specified in decimal degrees)
            """
            # convert decimal degrees to radians 
            print([lat1, long1, lat2, long2])
            lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])
            # haversine formula 
            dlon = long2 - long1 
            dlat = lat2 - lat1 
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a)) 
            # Radius of earth in kilometers is 6371
            km = 6371* c

            # conversion factor
            conv_fac = 0.621371

            # calculate miles
            miles = km * conv_fac
            # print(miles)
            return miles
        
        def findNearestLocationObjects(location):
            city = location.city
            country = location.country
            lat = location.latitude
            lon = location.longitude
            #validate city, country, lat, lon
            if city is not None:
                pass
            else:
                raise BadRequestException("invalid request; city is incorrect", 400)
            if country is not None:
                pass
            else:
                raise BadRequestException("invalid request; country is incorrect", 400)
            if lat is not None:
                pass
            else:
                raise BadRequestException("invalid request; latitude is incorrect", 400)
            if lon is not None:
                pass
            else:
                raise BadRequestException("invalid request; longitude is incorrect", 400)

            dist_obj = []
            all_location_objs = Location.objects.all()
            for one_obj  in all_location_objs:
                #get respective venue objects for the location
                # try:
                if VenueInternal.objects.using('default').filter(location_id=one_obj.location_id).values_list('venue_id'):
                    venue_id_objs = VenueInternal.objects.using('default').filter(location_id=one_obj.location_id).values_list('venue_id')

                if VenueExternal.objects.using('default').filter(location_id=one_obj.location_id).values_list('venue_id'):
                    venue_id_objs = VenueExternal.objects.using('default').filter(location_id=one_obj.location_id).values_list('venue_id')
                
                for venue_id in venue_id_objs:
                    one_post_venue_objs = Post.objects.using('default').filter(venue_id=venue_id)
                    for post_id_obj in one_post_venue_objs:
                        # print(post_id_obj)
                        if (one_obj.latitude is not None) and  (one_obj.longitude is not None):
                            dist_obj.append((dist(lat, lon, one_obj.latitude, one_obj.longitude), (post_id_obj.post_id, venue_id[0])))
            #Sort the distance by nearest first
            dist_obj.sort(key=lambda y: y[0])
            return dist_obj


        uid = kwagrs.get('userId')
        location = kwagrs.get('location')

    #Get the user details with the user id
        if uid is not None:
            try:
                user_obj = User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

        json_result = []
        nearYouObjs = []
        exploreTheLoopObjs = []
        trendingVideosObjs = []
        stuffYouLike = []
        usersYouLike = []

        if location:
            dist_post_objs = findNearestLocationObjects(location)
            for i in range(len(dist_post_objs)):
                (dist, (pid, vid)) = dist_post_objs[i]
                obj = Post.objects.using('default').get(post_id=pid)
                uobj = User.objects.using('default').get(user_id=obj.user_id)
                # priceobj = VenueExperiencePrice.objects.using('default').get()
                json_obj = ExploreAllPostObjectType(obj.post_id, obj.title, ExploreAllUserObjectType(obj.user_id, uobj.username, uobj.avatar, obj.user_rating)) 
                # {
                #     'id':obj.post_id,
                #     'name':obj.title,
                #     #'price':obj.price,
                #     'user': ExploreAllUserObjectType(obj.user_id, uobj.username, uobj.avatar, obj.user_rating)
                #     # {
                #     #     'id':obj.user_id,
                #     #     'username':uobj.username,
                #     #     'avatar':uobj.avatar,
                #     #     'rating':obj.user_rating
                #     # }
                #}
                json_result.append(json_obj)
            nearYouObjs = json_result


        #For Explore the loop
        json_result =  []
        for obj in ExploreCategory.objects.all():
            json_result.append(ExploreTheLoopObjectType(obj.name, obj.thumbnail))
        exploreTheLoopObjs = json_result

        #For trending videos, the post can be curated from the most liked and shared videos.
        
        json_result = []
        post_objs = Post.objects.all().order_by('-total_likes', '-total_shares', '-total_comments','-total_saves')
        for pobj in post_objs:
            
            uobj = User.objects.using('default').get(user_id=pobj.user_id)

            json_obj = ExploreAllPostObjectType(pobj.post_id, pobj.title, ExploreAllUserObjectType(pobj.user_id, uobj.username, uobj.avatar, pobj.user_rating))
            json_result.append(json_obj)
        trendingVideosObjs = json_result

        '''-----------------------------------------------------------------------TO DO---------------------------------------------------------------------------'''
        #Looper you like
        #Stuff you like
        

        
        return ExploreAllFieldType(nearYouObjs, exploreTheLoopObjs, trendingVideosObjs, stuffYouLike, usersYouLike)

 #Get Following Users
    def resolve_usersFollowing(parent, info, **kwagrs):
        uid = kwagrs.get("userId")
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if uid is not None:
            try:
                User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        following_user_ids =[]
        following_user_ids += UserFollowing.objects.using('default').filter(user_id=uid).values_list('following_user_id')
        for a in range(len(following_user_ids)):
            following_user_ids[a] = following_user_ids[a][0]
        following_user_objs = []
        for each in following_user_ids:
            # following_user_objs.append(User.objects.using('default').get(user_id=each))   
            # try:
            #     UserFollowing.objects.using('default').get(Q(following_user_id=uid) & Q(user_id=each))
            userprofile = UserProfile.objects.using('default').get(user_id=each)
            user = User.objects.using('default').get(user_id=each)
            following_user_objs.append(userObject(True, userprofile.user_id ))#, user.username, userprofile.name, user.avatar, user.level))
            # except UserFollowing.DoesNotExist:
            #     userprofile = UserProfile.objects.using('default').get(user_id=each)
            #     user = User.objects.using('default').get(user_id=each)
            #     following_user_objs.append(userObject(False, userprofile.user_id, user.username, userprofile.name, user.avatar, user.level))
            # following_user_objs.append(UserProfile.objects.using('default').get(user_id=each))
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
        # return  

 #Get Follower Users
    def resolve_userFollowers(parent, info, **kwagrs):
        uid = kwagrs.get("userId")
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if uid is not None:
            try:
                User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        follower_user_ids =[]
        follower_user_ids += UserFollower.objects.using('default').filter(user_id=uid).values_list('follower_user_id')
        
        for a in range(len(follower_user_ids)):
            follower_user_ids[a] = follower_user_ids[a][0]
        follower_user_objs = []
        for each in follower_user_ids:
            try:
                UserFollowing.objects.using('default').get(user_id=uid, following_user_id=each)
                userprofile = UserProfile.objects.using('default').get(user_id=each)
                user = User.objects.using('default').get(user_id=each)
                follower_user_objs.append(userObject(True, userprofile.user_id ))#, user.username, userprofile.name, user.avatar, user.level))
            except UserFollowing.DoesNotExist:
                userprofile = UserProfile.objects.using('default').get(user_id=each)
                user = User.objects.using('default').get(user_id=each)
                follower_user_objs.append(userObject(False, userprofile.user_id ))#, user.username, userprofile.name, user.avatar, user.level))
        # return follower_user_objs 
        result = follower_user_objs
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

 #Search Following User
    def resolve_usersFollowingResults(parent, info, **kwagrs):
        uid = kwagrs.get("userId")
        search_content = kwagrs.get("searchContent")
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if uid is not None:
            try:
                User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
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
        obj_list = UserProfile.objects.using('default').filter(Q(user_id__in = username_objs) | (Q(name__icontains=search_content)& Q(user_id__in=following_user_ids))).values_list('user_id')
        following_user_objs = []
        for each in obj_list:
            # following_user_objs.append(User.objects.using('default').get(user_id=each))   
            # try:
            #     UserFollowing.objects.using('default').get(Q(following_user_id=uid) & Q(user_id=each))
            userprofile = UserProfile.objects.using('default').get(user_id=each[0])
            user = User.objects.using('default').get(user_id=each[0])
            following_user_objs.append(userObject(True, userprofile.user_id))
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
        if uid is not None:
            try:
                User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
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
        follower_user_ids += UserFollower.objects.using('default').filter(user_id=uid).values_list('follower_user_id')
        for a in range(len(follower_user_ids)):
            follower_user_ids[a] = follower_user_ids[a][0]
        username_objs = []
        obj_list = []
        username_objs += User.objects.using('default').filter(Q(username__icontains=search_content) & Q(user_id__in=follower_user_ids)).values_list('user_id')
        for a in range(len(username_objs)):
            username_objs[a] = username_objs[a][0]
        obj_list = UserProfile.objects.using('default').filter(Q(user_id__in = username_objs) | (Q(name__icontains=search_content)& Q(user_id__in=follower_user_ids)))
        result = []
        for one in obj_list:
            try:
                UserFollowing.objects.using('default').get(user_id=uid, following_user_id=one.user_id)
                userprofile = UserProfile.objects.using('default').get(user_id=one.user_id)
                user = User.objects.using('default').get(user_id=one.user_id)
                result.append(userObject(True, userprofile.user_id))
            except UserFollowing.DoesNotExist:
                userprofile = UserProfile.objects.using('default').get(user_id=one.user_id)
                user = User.objects.using('default').get(user_id=one.user_id)
                result.append(userObject(False, userprofile.user_id))

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
        if uid  is not None:
            try:
                u_obj = User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        try:
            UserProfile.objects.using('default').get(user_id=uid)
        except UserProfile.DoesNotExist:
            raise NotFoundException("user profile for provided userId not found", 404)    
        return getProfileTagsList(uid)

 #Get All User Tags
    def resolve_allUserTags(parent, info):
        return UserProfileTag.objects.all().order_by('name')

 #Get Saved Posts
    def resolve_savedPosts(parent, info, **kwagrs):
        id = kwagrs.get('userId')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if id is not None :
            result = []
            post_ids = []
            try:
                if User.objects.using('default').get(user_id=id) and UserProfile.objects.using('default').get(user_id=id):
                    post_ids += PostSaved.objects.using('default').filter(user_id=id).values_list('post_id')
                    post_ids = [i[0] for i in post_ids]
                    for i in Post.objects.using('default').filter(post_id__in=post_ids).order_by('-date_created'):
                        result.append(PostListType(i.post_id))
                        # result.append(i)
                    result.sort(key=lambda x:x.post_id, reverse=True)
                    # return result
                    if len(result)>0:
                        if page and limit:
                            totalPages = math.ceil(len(result)/limit)
                            if page <= totalPages:
                                start = limit*(page-1)
                                result = result[start:start+limit]

                                return PostPageListType(posts=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                            else:
                                raise BadRequestException("invalid request; page provided exceeded total")
                        elif page == limit == None:
                            return PostPageListType(posts=result,  page_info=PageInfoObject(nextPage= None, limit=None))
                        elif page is None:
                            raise BadRequestException("invalid request; limit cannot be provided without page")
                        elif limit is None:
                            raise BadRequestException("invalid request; page cannot be provided without limit")
                        
                    else:
                        return PostPageListType(posts=[],  page_info=PageInfoObject(nextPage= None, limit=None))
                    # else:
                    #     raise NotFoundException("post does not exist", 204) 
            except (User.DoesNotExist):
                raise NotFoundException("userId provided not found", 404)
            except UserProfile.DoesNotExist:
                raise NotFoundException("profile for provided userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)       
        return None

 #Resend Email to acitvate account
    def resolve_resendActivation(parent, info, **kwargs):
        email = kwargs.get('email')
        if email is not None:
            try:
                # username = jwt.decode(email, "1232141",algorithms=['HS256'])['user']
                user = User.objects.using('default').get(email=email)
                name = user.first_name + user.last_name
                username = user.username
                
                
                if username and not user.is_activated:
                    sendMailToUser(name, username, email)
                    return stringType(str("successfully resent the activation link"))
                elif username and user.is_activated:
                    raise ConflictException("conflict in request; account already activated", 409)
            except User.DoesNotExist:
                raise NotFoundException("email provided is not found")
            except jwt.DecodeError:
                raise BadRequestException("invalid request; email provided is invalid", 400)
        else:
            raise BadRequestException("invalid request; email provided is invalid", 400)

 #Get Cache
    def resolve_getTokenFromCache(slef, info, **kwargs):
        userId= kwargs.get('userId')
        client  = redis_connect()
        if get_routes_from_cache(client, userId) is not None:
            return stringType(str(get_routes_from_cache(client, userId).decode("utf-8")))
        else:
            raise AuthorizationException("userId provided has logged out", 401)

 #Logout
    def resolve_logout(self, info, **kwargs):
        userId = kwargs.get('userId')
        client = redis_connect()
        user = User.objects.using('default').get(user_id=userId)
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjIwMjEwMTA2LCJ1c2VybmFtZSI6IlVzZXI4QGxvb3AiLCJyZWNvbW1lbmRlZFBvc3RzIjpbXX0.4srgfk2N2zgoPzq26RRq0dCZHZtN2C2W97D_5J7o6Ok"
        # print(info.context.session[user.user_id])
        # print(user.user_id)
        if info.context.session[str(user.user_id)]:
            print(info.context.session[str(user.user_id)])
            # set_routes_to_cache()
            info.context.session[str(user.user_id)] = {}
            # delete_routes_from_cache(client, str(userId)+"_search_history")
            # delete_routes_from_cache(client, userId)
            return stringType("logout successful")
        else:
            raise AuthorizationException("userId provided has already logged out", 401)

 #SendResetPasswordCode
    def resolve_resetPasswordCode(self, info, **kwargs):
        useremail = kwargs.get('email')
        response = {}
        # sessionObj = {
        #     # 'email': "",
        #     # 'username': "",
        #     # 'userId': "",
        #     'secret': "",
        #     'verified': False
        # }
        if useremail is not None:
            if useremail and useremail.strip():
                try:
                    user = User.objects.using('default').get(Q(email__icontains=useremail)|Q(username__icontains=useremail))
                except User.DoesNotExist:
                    raise NotFoundException("username/email provided not found", 404)
                response = sendPasswordResetCodeMailToUser(user.email, user.username, user.user_id)
                # sessionObj = {
                #     # 'email': user.email,
                #     # 'username': user.username,
                #     # 'userId': user.user_id,
                #     'secret': response['secretcode'],
                #     'verified': False
                # }
                # sessionId = 'reset'+str(user.user_id)
                info.context.session[response['secretcode']]=False
                if response['code'] == 202:
                    return responseResetPasswordType(response['message'], response['secretcode'])
                else:
                    raise NoContentException("email not sent to the provided email")
            else:
                raise BadRequestException("invalid request; username/email provided is empty", 400)
        else:
            raise BadRequestException("invalid request; username/email provided is invalid", 400)

 #ResendResetPasswordCode
    # def resolve_resendResetPasswordCode(self, info, **kwargs):
        # useremail = kwargs.get('email')
        # if useremail is not None:
        #     pass
        # else:
        #     raise BadRequestException("email provided is invalid", 400)
        # response = {}
        # # if info.context.session['reset'+str(user_id)] is not None:
        # #     user = info.context.session['reset'+str(user_id)] 
        # if email is not None:
        #     if email and email.strip():
        #         user = User.objects.using('default').get(Q(email__icontains=useremail)|Q(username__icontains=useremail))
        #         response = sendPasswordResetCodeMailToUser(user.email, user.username, user.user_id)
        #         # sessionObj = {
        #         #     'email': user.email,
        #         #     'username': user.username,
        #         #     'userId': user.user_id,
        #         #     'secret': response['secretcode']
        #         # }
        #         # sessionId = 'reset'+str(user.user_id)
        #         # info.context.session[response['secretcode']]=sessionObj
        #         if response['code'] == 202:
        #             return responseResetPasswordType(response['message'], response['secretcode'])
        #         else:
        #             raise NoContentException("email not sent to the provided email")
        #     else:
        #         raise BadRequestException("email provided is empty", 400)
        # else:
        #     raise BadRequestException("email provided is invalid", 400)

 #Verify reset Password Code
    def resolve_verifyresetpasswordcode(self, info, **kwargs):
        code = kwargs.get('code')
        token = kwargs.get('token')
        if token is not None:
            pass
        else:
            raise BadRequestException("invalid request; token provided is invalid", 400)
        # base32secret = pyotp.random_base32()
        sessionObj = info.context.session[token]
        print(sessionObj)
        # base32secret = session['secret']
        
        totp = pyotp.TOTP(token, interval=300)
        # totp = pyotp.TOTP("base32secret3232", interval=60)
        if code is not None:
            print(code)
            print(type(code))
            response = totp.verify(str(code))

            print(response)
            if response:
                info.context.session[token] = True
                return stringType(str("successful verified the code"))
            else:
                raise AuthorizationException("code provided is not authorized", 401)
        else:
            raise BadRequestException("invalid request; code provided is invalid", 400)

 #Report Post Reasons
    def resolve_reportPostReasons(self, info):
        return ReportPostReason.objects.all()

 #Report User Reasons
    def resolve_reportUserReasons(self, info):
            return ReportUserReason.objects.all()

 #Receive Chat Message
    def resolve_messages(self, info, **kwargs):
        sender_user_id = kwargs.get('authUserId')
        receiver_user_id = kwargs.get('recipientUserId')
        dialog_id = kwargs.get('threadId')

        try: 
            User.objects.using('default').get(user_id=sender_user_id)
        except User.DoesNotExist:
            raise NotFoundException("sender userId provided not found", 404)
        try: 
            User.objects.using('default').get(user_id=receiver_user_id)
        except User.DoesNotExist:
            raise NotFoundException("receiver userId provided not found", 404)
        try:
            dialog = ChatThread.objects.using('default').get(id = dialog_id)
            try:
                dialog = ChatThread.objects.using('default').get((Q(user1_id= sender_user_id) & Q(user2_id= receiver_user_id)) | (Q(user2_id= sender_user_id) & Q(user1_id= receiver_user_id)))
            except ChatThread.DoesNotExist:
                raise NotFoundException("thread between the users not found", 404)
        except ChatThread.DoesNotExist:
            raise NoContentException("threadId provided not found", 404)
        
        chat_messages = []
        chat_messages += ChatMessage.objects.using('default').filter(dialog_id = dialog_id)
        result = []
        print(len(chat_messages))
        for each in chat_messages:
            s_user = User.objects.using('default').get(user_id=each.sender_id)
            r_user = User.objects.using('default').get(user_id=each.recipient_id)
            

            sender_user = {
                "username": s_user.username,
                "id": s_user.user_id ,
                "avatar": s_user.avatar
            }
            recipient_user = {
                "username": r_user.username,
                "id": r_user.user_id ,
                "avatar": r_user.avatar
            }
            if each.attachment_type is not None:
                if each.attachment_type.name == 'post':
                    attachment_id = PostShared.objects.using('default').get(chat_message_id=each.id).post_id
                elif each.attachment_type.name == 'venue':
                    attachment_id = VenueShared.objects.using('default').get(chat_message_id=each.id).venue_id
                attachment = {
                    "type": {
                        "name":each.attachment_type.name,
                        "attachment_type_id":each.attachment_type_id
                        },
                    "id": attachment_id
                }
            else:
                attachment = {}
            if each.reaction:
                reaction = {
                    "reaction": None,
                    "user": None
                }
            else:
                reaction = {}
            shares = {
                "is_post": False,
                "media": None,
                "id": None,
                "title": None
            }
            story = {
                "id": None,
                "link": None,
                "is_reply": None
            }
            each_result =  {
                "messageId": each.id,
                "modified_datetime": each.modified,
                "sender": sender_user,
                "recipient": recipient_user,
                "message":each.text,
                "attachment": attachment,
                "reaction": reaction,
                "shares": shares,
                "story": story
            }
            result.append(each_result)
        
        #Sort with latest date on top
        result.sort(key = lambda x:x['modified_datetime'], reverse=True)

        return result
        
 #Thread List
    def resolve_threadList(self, info, **kwargs):
        user_id = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id=user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        dialogs = []
        dialogs += ChatThread.objects.using('default').filter(participant_id__contains=[user_id]).values_list('thread_id', 'modified', 'is_approved')#, 'created', 'user1_id', 'user2_id')
        dialogs.sort(key=lambda x:x[1], reverse = True)
        result = []
        for each in dialogs:
            # messages = []
            # recent_message = []
            # has_unread = False
            # if user_id == each[3]:
            #     flag = 0
            # else:
            #     flag = 1
            # participant = User.objects.using('default').get(user_id=each[3]) if flag == 1 else User.objects.using('default').get(user_id=each[4])
            
            # recent_message += ChatMessage.objects.using('default').filter(dialog_id=each[0]).values_list('id', 'modified', 'text', 'read', 'sender_id')

            # recent_message.sort(key = lambda x:x[1], reverse=True)

            # for each_message in recent_message:
            #     messages.append({"id": each_message[0], "date_created": each_message[1], "message": each_message[2]})
            #     if not each_message[3] and not each_message[4]==user_id :
            #         has_unread = True
            if each[2]:
                try:
                    ChatDeleteThread.objects.using('default').get(thread_id=each[0], user_id = user_id)
                except ChatDeleteThread.DoesNotExist:
                    result.append({
                        "threadId": each[0],
                        # "date_modified": each[1],
                        # "participants": [{
                        #     "username":participant.username,
                        #     "id": participant.user_id,
                        #     "avatar": participant.avatar
                        #     }],
                        # "recent_message":messages[0],
                        # "has_unread":has_unread
                    })
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return ChatThreadsPageListType(threads=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return ChatThreadsPageListType(threads=result, page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return ChatThreadsPageListType(threads=[], page_info=PageInfoObject(nextPage= None, limit=None))
        
        return result
 
 #Get Thread by Thread Id
    def resolve_threadInfo(self, info, **kwargs):
        dialog_id = kwargs.get('threadId')
        user_id = kwargs.get('userId')
        if user_id is not None:
            try:
                user= User.objects.using('default').get(user_id=user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if dialog_id is not None:
            try:
                dialog = ChatThread.objects.using('default').get(thread_id = dialog_id)
                if user.user_id in dialog.participant_id:
                    pass
                else:
                    raise AuthorizationException("userId provided is not authorized to view this thread")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found", 404)
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")

        result = {}
        list_messages = []
        messages = []
        participants = []
        unreadCount = 0
        list_messages+= ChatMessage.objects.using('default').filter(thread_id=dialog_id).values_list('thread_id', 'modified', 'read', 'text')
        list_messages.sort(key = lambda x:x[1], reverse=True)
        for each in list_messages:
            if each[2]:
                pass
            else:
                unreadCount +=1
            messages.append({"id": each[0], "date_created": each[1], "message":each[3]})
        print(messages)
        recentMessage = messages[0]['message'] if messages!=[] else ""
        participants = dialog.participant_id
        # user1 = User.objects.using('default').get(user_id=dialog.user1_id)
        # user2 = User.objects.using('default').get(user_id=dialog.user2_id)
        # participants.append( {
        #     "username":user1.username,
        #     "id": user1.user_id,
        #     "avatar": user1.avatar
        # })
        # participants.append({
        #     "username":user2.username,
        #     "id": user2.user_id,
        #     "avatar": user2.avatar
        # })
        name =''
        if dialog.name:
            user = User.objects.using('default').get(user_id=user_id)
            if not len(dialog.participant_id)>2:
                for one in participants:
                    # one = User.objects.using('default').get(user_id=one)
                    if one==user_id:
                        continue
                    one = User.objects.using('default').get(user_id=one)
                    
                    name += one.username
                    if len(participants)>2:
                        name += ',' 
            else:
                name = dialog.name
        else:
            for one in participants:
                # one = User.objects.using('default').get(user_id=one)
                if one==user_id:
                    continue
                one = User.objects.using('default').get(user_id=one)
                
                name += one.username
                if len(participants)>2:
                    name += ','
        admin =[]
        if dialog.admin is not None:
            if user_id in dialog.admin:
                admin = dialog.admin

        result = {
            "thread_id": dialog.thread_id,
            # "messages": messages,
            "participants": [{"user_id": each} for each in participants],
            "name": name,
            "hasUnreadMessage": False if unreadCount ==0 else True,
            "unreadCount":aggregateObjectType(aggregate= aggregate(count = unreadCount)),
            "mostRecentMessage": recentMessage,
            "admin":[{"user_id":eachAdmin} for eachAdmin in admin]
        }
        return result

 #Get Message List
    def resolve_messageList(self, info, **kwargs):
        user_id = kwargs.get('userId')
        dialog_id = kwargs.get('threadId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')

        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id=user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if dialog_id is not None:
            try:
                dialog = ChatThread.objects.using('default').get(thread_id = dialog_id)
                if user_id in dialog.participant_id:
                    pass
                else:
                    raise AuthorizationException("userId provided is not authorized to view this list")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found", 404)
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")
        
        list_messages = []
        messages = []
        participants = []

        list_messages+= ChatMessage.objects.using('default').filter(thread_id=dialog.thread_id).values_list('message_id', 'modified', 'sender_id', 'recipient_id')
        list_messages.sort(key = lambda x:x[1], reverse=True)
        
        for each in list_messages:
            messages.append({"messageId": each[0], "date_created": each[1]})
            if user_id in each[3] and len(each[3])==1:
                message = ChatMessage.objects.using('default').get(message_id=each[0])
                message.read = True
                message.save()
        result = messages
        if len(result)>0:
            if page and limit:
                totalPages = math.ceil(len(result)/limit)
                if page <= totalPages:
                    start = limit*(page-1)
                    result = result[start:start+limit]

                    return ChatMessagesPageListType(messages=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                else:
                    raise BadRequestException("invalid request; page provided exceeded total")
            elif page == limit == None:
                return ChatMessagesPageListType(messages=result, page_info=PageInfoObject(nextPage= None, limit=None))
            elif page is None:
                raise BadRequestException("invalid request; limit cannot be provided without page")
            elif limit is None:
                raise BadRequestException("invalid request; page cannot be provided without limit")
            
        else:
            return ChatMessagesPageListType(messages=[], page_info=PageInfoObject(nextPage= None, limit=None))
        
        # return messages

 #Get Message by Message Id
    def resolve_message(self, info, **kwargs):
        sender_user_id = kwargs.get('userId')
        # receiver_user_id = kwargs.get('recipientUserId')
        messageId = kwargs.get('messageId')
        # dialog_id = kwargs.get('threadId')

        if sender_user_id is not None:
            try: 
                User.objects.using('default').get(user_id=sender_user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            BadRequestException("invalid request; userId provided is invalid")
        # if receiver_user_id is not None:
        #     try: 
        #         User.objects.using('default').get(user_id=receiver_user_id)
        #     except User.DoesNotExist:
        #         raise NotFoundException("receiver recipientUserId provided not found", 404)
        # else:
        #     BadRequestException("invalid request; recipientUserId provided is invalid")
        
        # if dialog_id is not None:
        #     try:
        #         dialog = ChatThread.objects.using('default').get(thread_id = dialog_id)
        #         try:
        #             participants = []
        #             participants.append(sender_user_id)
        #             participants+= receiver_user_id
        #             dialog = ChatThread.objects.using('default').get(participant_id_contains = [sender_user_id, receiver_user_id])
        #         except ChatThread.DoesNotExist:
        #             raise NotFoundException("thread between the users not found", 404)
        #     except ChatThread.DoesNotExist:
        #         raise NoContentException("threadId provided not found", 404)
        # else:
        #     BadRequestException("invalid request; threadId provided is invalid")

        if messageId is not None:
            try:
                message = ChatMessage.objects.using('default').get(message_id = messageId)  
            except ChatMessage.DoesNotExist:
                raise NotFoundException("messageId provided not found") 
        else:
            raise BadRequestException("invalid request; meeageId provided is invalid")     
        
        # chat_messages = []
        # chat_messages += ChatMessage.objects.using('default').filter(dialog_id = dialog_id)
        result = []
        # print(len(chat_messages))
        # for each in chat_messages:
        each =message
        # s_user = User.objects.using('default').get(user_id=each.sender_id)
        # r_user = User.objects.using('default').get(user_id=each.recipient_id)
        try: 
            dialog = ChatThread.objects.using('default').get(thread_id=each.thread_id)
            if sender_user_id not in dialog.participant_id:
                raise AuthorizationException("authUserId provided is not authorized to view this messageId")
            receiver_user_id = [ e.user_id for e in User.objects.using('default').filter(user_id__in=dialog.participant_id) if e.user_id != each.sender_id]
        except ChatThread.DoesNotExist:
            raise NotFoundException("thread between the users not found", 404)
        # sender_user = {
        #     "username": s_user.username,
        #     "id": s_user.user_id ,
        #     "avatar": s_user.avatar
        # }
        # recipient_user = {
        #     "username": r_user.username,
        #     "id": r_user.user_id ,
        #     "avatar": r_user.avatar
        # }
        # for eachUser in participants:
        #     obj = {
        #         ""
        #     }

        if each.attachment_type is not None:
            # if each.attachment_type.name == 'post':
            #     attachment_id = PostShared.objects.using('default').get(chat_message_id=each.message_id).post_id
            # elif each.attachment_type.name == 'venue':
            #     attachment_id = VenueShared.objects.using('default').get(chat_message_id=each.message_id).venue_id
            # attachment = {
            #     "type": {
            #         "name":each.attachment_type.name,
            #         "attachment_type_id":each.attachment_type_id
            #         },
            #     "id": attachment_id
            # }
            attachment = {
                 "type": {
                    "name":each.attachment_type,
                    "attachment_type_id":each.attachment_type_id
                    },
                "id": attachment_id
            }
        else:
            attachment = { 
                "type": {
                    "name":each.attachment_type,
                    "attachment_type_id":each.attachment_type_id
                    },
                "id": each.attachment_type_id
                }
        try:
            reactions=[]
            reaction=[]
            reactions = ChatMessageReaction.objects.using('default').filter(message_id=each.message_id)
            for eachReaction in reactions:
                reaction.append( {
                    "type_id": eachReaction.reaction_type_id,
                    "user_id": eachReaction.user_id
                })
        except ChatMessageReaction.DoesNotExist:
            reaction = []
        
            
        if each.share_type is not None:
            if each.share_type.share_type_id == 1:

                print()
                post = PostShared.objects.using('default').get(chat_message_id=each.message_id)
                postObj = Post.objects.using('default').get(post_id=int(post.post_id))
                shares = {
                    "type": "Post",
                    "id": post.post_id,
                    "media": postObj.thumbnail,
                    "title":postObj.title
                }
            elif each.share_type.share_type_id == 2 :
                venue = VenueShared.objects.using('default').get(chat_message_id = each.message_id)
                if venue.venue.is_external:
                    venueObj = VenueExternal.objects.using('default').get(venue_id=venue.venue_id)
                    mediaString = venueObj.thumbnail
                else:
                    venueObj= VenueInternal.objects.using('default').get(venue_id=venue.venue_id)
                    mediaString = venueObj.thumbnail
                shares = {
                    "type": "Venue",
                    "id": venue.venue_id,
                    "media": mediaString,
                    "title": venueObj.name
                }
        
        else:            
            shares = {
                "type": None,
                "id": None,
                "media": None,
                "title": None
            }
        story = {
            "id": None,
            "link": None,
            "is_reply": None
        }
        each_result =  {
            # "isSender": True if message.sender_id == sender_user_id else False,
            "messageId": each.message_id,
            "modified_datetime": each.modified,
            "sender_user_id": each.sender_id,
            "recipient_user_id":[{"user_id": each} for each in receiver_user_id],
            "message":each.text,
            "attachment": attachment,
            "reaction": reaction,
            "shares": {"link":None, "template":shares},
            "story": None,
            "read":each.read
        }
        result.append(each_result)
        
        #Sort with latest date on top
        # result.sort(key = lambda x:x['modified_datetime'], reverse=True)

        return each_result

 #Get Payment Info
    def resolve_paymentInfo(self, info, **kwargs):
        uid = kwargs.get("paymentOptionId")
        userId = kwargs.get("userId")
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        
        result = {}
        payment = []
        
        try:
            # payment += SavedUserPayment.objects.using('payments').filter(Q(user_id=uid) & Q(payment_type_id=1)).values_list('saved_user_payment_id', flat=True)
            # print(payment)
            # card += UserPaymentCard.objects.using('payments').filter(user_payment_card_id__in=payment).values_list('user_payment_card_id', 'card_number', 'expiry_month', 'expiry_year', 'security_code', 'billing_address_id')
            # print(card)
            card = CardPaymentDetail.objects.using('payments').get(payment_option_id=uid)
        except CardPaymentDetail.DoesNotExist:

            raise NotFoundException("payment detail with paymentOptionId provided not found", 404)
        
       
        if card.card_number:
            password_provided = "password"  # This is input in the form of a string
            password = password_provided.encode()  # Convert to type bytes
            salt = b'salt_'  # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100100,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password)) 
            f = Fernet(key)
            # encrypted = b'gAAAAABh4gTuKyshpkptPVn0K9m3zoJ12bJ5cxzdKI3ZkLgcTKsB0jeJc0ZnfZmWQ792AfOHxtgrcKqIgAIdPwsrL3r_JahGqw=='
            decrypted_card_number = f.decrypt(bytes(card.card_number))
            # password_provided = "password"  # This is input in the form of a string
            # password = password_provided.encode()  # Convert to type bytes
            # salt = b'salt_'  # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password)) 
            f = Fernet(key)
            decrypted_security_code = f.decrypt(bytes(card.security_code))
        # if card.billing_address:
        #     billing_address = BillingAddress.objects.using('payments').get(billing_address_id=card.billing_address)

        result = {"card_payment_detail_id":card.card_payment_detail_id, "last_four_digits":str(int(float(decrypted_card_number.decode())))[-4:], "expiry_month": card.expiry_month, "expiry_year":card.expiry_year, 'card_name':card.card_name ,'billing_address':card.billing_address}

        return result

 #Get List of Payment Option by User Id
    def resolve_paymentOptions(self, info, **kwargs):
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        saved_user_payments = PaymentOption.objects.using('payments').filter(user_id=userId).values_list('payment_option_id', 'user_id', 'payment_option_type_id')
        result = {}
        card =[]
        for each in saved_user_payments:
            cardObj = CardPaymentDetail.objects.using('payments').get(card_payment_detail_id=each[0])
            nameObj = BillingAddress.objects.using('payments').get(billing_address_id=cardObj.billing_address_id)

            password_provided = "password"  # This is input in the form of a string
            password = password_provided.encode()  # Convert to type bytes
            salt = b'salt_'  # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100100,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password)) 
            f = Fernet(key)
            # encrypted = b'gAAAAABh4gTuKyshpkptPVn0K9m3zoJ12bJ5cxzdKI3ZkLgcTKsB0jeJc0ZnfZmWQ792AfOHxtgrcKqIgAIdPwsrL3r_JahGqw=='
            decrypted_card_number = f.decrypt(bytes(cardObj.card_number))
            expiryDate = str(cardObj.expiry_month)+"/"+str(cardObj.expiry_year)
            if each[2] == 1:
                card.append(PaymentOptionType(each[0], nameObj.name, str(int(float(decrypted_card_number.decode())))[-4:], expiryDate))
        result= {
            "cards": card
        }
        return result

 #Get Venue by venueId
    def resolve_venue(self, info, **kwargs):
        venueId = kwargs.get('venueId')
        postId = kwargs.get('postId')
        userId = kwargs.get('userId')
        if venueId is not None:
            try:
                venue = Venue.objects.using('default').get(venue_id=venueId)
            except Venue.DoesNotExist:
                raise NotFoundException("venueId provided not found") 
        else:
            raise BadRequestException("invalid request; venueId provided is invalid")
       
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found")
        else:
            raise BadRequestException("invalid request; postId provided is invalid")
        
        result = {}

        if venue.is_external:
            #Not done logic for external
            pass
        else:
            venue = VenueInternal.objects.using('default').get(venue_id=venue.venue_id)
            if venue.type_id ==1:
                venueType = 'Experience'
                now = datetime.datetime.now()

                
            
                venuePrice = VenueExperiencePrice.objects.using('default').filter(Q(venue_id=venue.venue_id) & Q(end_available_date__gt=now)).last()
                if venuePrice != None:
                    price = venuePrice.price
                    priceWithTax = float(price) + (float(price)*0.0838)

                else:
                    venuePrice = VenueExperiencePrice.objects.using('default').filter(venue_id=venue.venue_id).aggregate(Avg('price'))
                    price = venuePrice['price__avg']
                    priceWithTax = float(price) + (float(price)*0.0838)
            
            userRating = post.user_rating
            

            sharedBy = post.user
            # sharedBy['rating'] = userRating

            venueRating = Post.objects.using('default').filter(venue_id=post.venue_id).aggregate(Avg('user_rating'))['user_rating__avg']
            venueRatingCount = Post.objects.using('default').filter(venue_id=post.venue_id).count()

            fmObj = venue.featured_video if venue.featured_video else None
            isVideo = False
            featuredMedia = []
            if fmObj:
                isVideo = True
                featuredMedia = [{
                    "id": fmObj.media_venue_id,
                    "url": fmObj.url
                }]

                
            else:
                isVideo = False
                featuredMedia = []
                i= 1
                for j in range(2):
                    obj = {
                        "id": i,
                        "url": venue.images[j] if venue.images is not None else "Sample Image Link"
                    }
                    i+=1
                    featuredMedia.append(obj)   
                #Add Gallery images.
            featuredMediaObject={
                    "isVideo": isVideo,
                    "media": featuredMedia
                }

            title = venue.name

            location = Location.objects.using('default').get(location_id=venue.location_id)

            shortDescription = venue.description

            media = []
            i= 1
            if venue.images:
                for each in venue.images:
                    obj = {
                        "id": i,
                        "url": each
                    }
                    i+=1
                    media.append(obj)
            else:
                pass

            vendorVenue = VendorVenue.objects.using('default').get(venue_id=post.venue_id)
            # vendorVenueIds = []
            # vendorVenueIds = VendorVenue.objects.using('default').filter(vendor_id=vendorVenue.vendor_id).values_list('venue_id', flat=True)

            # vendorRating = Post.objects.using('default').filter(venue_id__in=vendorVenueIds).aggregate(Avg('user_rating'))['user_rating__avg']
            # vendorRatingCount = Post.objects.using('default').filter(venue_id__in=vendorVenueIds).count()

            venueObj = {
                "venue_id": venueId,
                "venue_type": venueType,
                "featured_media": featuredMediaObject,
                "title": title,
                "location": location, #Database Location Object
                "price": round(price,2),
                "price_with_tax": round(priceWithTax,2),
                # "rating": venueRating,
                # "no_of_ratings": venueRatingCount,
                "is_refundable": True,
                "shared_by": VenueUserObjectType(sharedBy.user_id), #, sharedBy.username, sharedBy.avatar, sharedBy.level, sharedBy.phone_number, userRating),  #Database User Object
                "short_description": shortDescription, 
                "gallery": media,  #Media Object with {'id', 'url'}
                "vendor_venue_id": vendorVenue.vendor_venue_id #vendorVenue.vendor.name, vendorVenue.vendor.avatar, vendorVenue.vendor.bio_url, vendorVenue.vendor.short_description, vendorRating, venueRatingCount)   #Database Vendor Object
            }
            
            return venueObj

 #Get Vendor Object by Venue Vendor Id
    def resolve_vendor(self, info, **kwargs):
        venueVendorId = kwargs.get('vendorVenueId')
        if venueVendorId is not None:
            try:
                vendorVenue = VendorVenue.objects.using('default').get(vendor_venue_id=venueVendorId)
                vendorVenueIds = []
                vendorVenueIds = VendorVenue.objects.using('default').filter(vendor_id=vendorVenue.vendor_id).values_list('venue_id', flat=True)

                vendorRating = Post.objects.using('default').filter(venue_id__in=vendorVenueIds).aggregate(Avg('user_rating'))['user_rating__avg']
                vendorRatingCount = Post.objects.using('default').filter(venue_id__in=vendorVenueIds).count()
                # result = VendorObjectType(vendorVenue.vendor_venue_id, vendorVenue.vendor.name, vendorVenue.vendor.avatar, vendorVenue.vendor.bio_url, vendorVenue.vendor.short_description, vendorRating, vendorRatingCount)
                
                return VendorObjectType(vendorVenue.vendor_venue_id, vendorVenue.vendor.name, vendorVenue.vendor.avatar, vendorVenue.vendor.bio_url, vendorVenue.vendor.short_description, vendorRating, vendorRatingCount)
            except VendorVenue.DoesNotExist:
                raise NotFoundException("vendorVenueId provided not found")
        else:
            raise BadRequestException("invalid request; vendorVenueId is invalid")
        
 #Get Number of Ratings and Aggregate Rating
    def resolve_venueRating(self, info, **kwargs):
        venueId = kwargs.get('venueId')
        if venueId is not None:
            try:
                venue = Venue.objects.using('default').get(venue_id=venueId)
                venueRating = Post.objects.using('default').filter(venue_id=venueId).aggregate(Avg('user_rating'))['user_rating__avg']
                venueRatingCount = Post.objects.using('default').filter(venue_id=venueId).count()
                return VenueRatingObjectType(venue_rating=venueRating, venue_rating_aggregate=aggregateObjectType(aggregate=aggregate(count=venueRatingCount)))
            except Venue.DoesNotExist:
                raise NotFoundException("venueId provided not found") 
        else:
            raise BadRequestException("invalid request; venueId provided is invalid")

 #Get Available Date for one venue
    def resolve_venueAvailableDates(self, info, **kwargs):
        venueId = kwargs.get('venueId')
        userId = kwargs.get('userId')
        if venueId is not None:
            try:
                venue = Venue.objects.using('default').get(venue_id=venueId)
            except:
                raise NotFoundException("venueId provided not found") 
        else:
            raise BadRequestException("invalid request; venueId provided is invalid")
       
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")

        if venue.is_external:
            #Not done logic for external
            pass
        else:
            venue = VenueInternal.objects.using('default').get(venue_id=venue.venue_id)
            if venue.type_id ==1:
                now = datetime.datetime.now()
                dateDict = {}
                dateList = []
                # now  = datetime.date(2022, 2, 25)
                # print(now)
                dateObj = VenueExperiencePrice.objects.using('default').filter(Q(venue_id=venueId) & Q(start_available_date__gt=now)).values_list('venue_experience_price_id', 'start_available_date')
                i = 0
                for each in dateObj:
                    if each[1] in dateDict.keys():

                        dateDict[each[1]].append(each[0])
                    else:
                        dateDict[each[1]]=[each[0]]
                    i+=1
                # print(dateDict)
                # for one in dateDict.items():
                #     # print(one)
                #     dateList.append(
                #         {
                #             'ids': one[1],
                #             'date': one[0] 
                #         }
                #     )
                return {'dates':dateDict.keys()}
        # print(dateObj)

 #Get Venue Booking Options Id List for a particular date
    def resolve_venueBookingOptions(self, info, **kwargs):
        userId = kwargs.get('userId')
        venueId = kwargs.get('venueId')
        # dateIds = kwargs.get('dateIds')
        date = kwargs.get('date')
        if venueId is not None:
            try:
                venue = Venue.objects.using('default').get(venue_id=venueId)
                if venue.is_external:
                    pass
                else:
                    venue = VenueInternal.objects.using('default').get(venue_id=venue.venue_id)
            except:
                raise NotFoundException("venueId provided not found") 
        else:
            raise BadRequestException("invalid request; venueId provided is invalid")
       
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        bookingOptions = []
        if date is not None:
            date = datetime.date(int(date.split('-')[0]), int(date.split('-')[1]), int(date.split('-')[2]))
            today = datetime.datetime.now()
            pacific_tzinfo = pytz.timezone("US/Pacific")
            pacific_time = today.astimezone(pacific_tzinfo)
            print(pacific_time.date())
            if date < pacific_time.date():
                raise BadRequestException('date provided is in the past')
            else:
                bookingOptions = VenueExperienceBookingOption.objects.using('default').filter(venue_experience_price__start_available_date=date).values_list('venue_experience_booking_option_id')
        else:
            raise BadRequestException('invalid request; date provided is invalid')
        print(bookingOptions)
        result = []
        result = [x[0] for x in bookingOptions]
        # #Duration
        # enter = bookingOptions[1].venue_experience_price.start_time
        # exit = bookingOptions[1].venue_experience_price.end_time
        # enter_delta = datetime.timedelta(hours=enter.hour, minutes=enter.minute, seconds=enter.second)
        # exit_delta = datetime.timedelta(hours=exit.hour, minutes=exit.minute, seconds=exit.second)
        # duration = (exit_delta - enter_delta).total_seconds()/3600

        # for each in bookingOptions:
        #     #Duration
        #     enter = each.venue_experience_price.start_time
        #     exit = each.venue_experience_price.end_time
        #     enter_delta = datetime.timedelta(hours=enter.hour, minutes=enter.minute, seconds=enter.second)
        #     exit_delta = datetime.timedelta(hours=exit.hour, minutes=exit.minute, seconds=exit.second)
        #     duration = int((exit_delta - enter_delta).total_seconds()/60)
        #     # seconds = duration % (24 * 3600)
        #     # hour = seconds // 3600
        #     # seconds %= 3600
        #     # minutes = seconds // 60
        #     # seconds %= 60
        #     durationObj = {
        #         "value": duration,
        #         "unit": "minutes"
        #     }

        #     #Venue Internal
            

        #     obj = {   
        #         "venue_experience_booking_option_id": each.venue_experience_booking_option_id,
        #         "title": each.title,
        #         "time": each.venue_experience_price.start_time,
        #         "duration": durationObj,
        #         "price": each.venue_experience_price.price,
        #         "guests_limit": venue.max_guests,
        #         "short_description": each.short_description,

        #     }
        #     result.append(obj)
        return VenueBookingOptionsIdsType(Ids=result)
        # if bookingOptions:
        #     for each in bookingOptions:

 #Get Booking Option 
    def resolve_venueBookingOption(self, info, **kwargs):
        userId = kwargs.get('userId')
        venueBookingOptionId = kwargs.get('venueBookingOptionId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if venueBookingOptionId is not None:
            try:
                result = {}
                each = VenueExperienceBookingOption.objects.using('default').get(venue_experience_booking_option_id=venueBookingOptionId)
                #Duration
                enter = each.venue_experience_price.start_time
                exit = each.venue_experience_price.end_time
                enter_delta = datetime.timedelta(hours=enter.hour, minutes=enter.minute, seconds=enter.second)
                exit_delta = datetime.timedelta(hours=exit.hour, minutes=exit.minute, seconds=exit.second)
                duration = int((exit_delta - enter_delta).total_seconds()/60)
                # seconds = duration % (24 * 3600)
                # hour = seconds // 3600
                # seconds %= 3600
                # minutes = seconds // 60
                # seconds %= 60
                durationObj = {
                    "value": duration,
                    "unit": "minutes"
                }

                #Venue Internal
                venue = Venue.objects.using('default').get(venue_id=each.venue_experience_price.venue_id)
                if not venue.is_external:
                    venue = VenueInternal.objects.using('default').get(venue_id=each.venue_experience_price.venue_id)
                else:
                    venue = VenueExternal.objects.using('default').get(venue_id=each.venue_experience_price.venue_id)

                result = {   
                    "venue_experience_booking_option_id": each.venue_experience_booking_option_id,
                    "title": each.title,
                    "time": each.venue_experience_price.start_time,
                    "duration": durationObj,
                    "price": each.venue_experience_price.price,
                    "guests_limit": venue.max_guests,
                    "short_description": each.short_description,

                }
                
                return result
            except VenueExperienceBookingOption.DoesNotExist:
                raise NotFoundException("venueExperienceBookingOptionId provided not found")
        else:
            raise BadRequestException("invalid request; venueExperienceBookingOptionId provided is invalid")

 #Get Itinerary of posts by Itinerary Id
    def resolve_itinerary(self, info, **kwargs):
        userId = kwargs.get('userId')
        itineraryId = kwargs.get('itineraryId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if itineraryId is not None:
            try:
                itinerary = UserSharedItinerary.objects.using('default').get(user_shared_itinerary_id = itineraryId)
            except:
                raise NotFoundException("itineraryId provided not found")
        else:
            raise BadRequestException("invalid request; itineraryId provided is invalid") 
        
        tagIds = UserSharedItineraryTag.objects.using('default').filter(user_shared_itinerary_id=itinerary.user_shared_itinerary_id).values_list('tag_id', flat=True)
        tags = []
        res_tags = []
        res_tags = Tag.objects.using('default').filter(tag_id__in=tagIds)
        for each in res_tags:
            tags.append(hashtagSection(each.name, each.tag_id))

        
        
        postIds = UserSharedItineraryPost.objects.using('default').filter(user_shared_itinerary_id=itinerary.user_shared_itinerary_id).values_list('post_id', flat=True)
        posts = []
        posts = Post.objects.using('default').filter(post_id__in=postIds).order_by('-date_created').values_list('post_id')
        
        posts = [PostListType(post_id=x[0]) for x in posts]
        # print(posts)
        result = {
            "itinerary_id": itinerary.user_shared_itinerary_id,
            "userId": itinerary.user_id,
            "title": itinerary.name,
            "description": itinerary.description,
            "tags": tags,
            "posts": posts,
            "thumbnail": itinerary.thumbnail
            }    
        return result  

 #Get Search History
    def resolve_searchHistory(self, info, **kwargs):
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
                try:
                    if info.context.session[str(userId)] == {}:
                        raise AuthorizationException("please login to access", 401)
                    else:
                        pass
                except GraphQLError:
                    raise AuthorizationException("please login to access", 401)

            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        client = redis_connect()
        search_history_cache = get_hashmap_from_cache(client, str(userId)+"_search_history")
        resultList= search_history_cache.getAll() if search_history_cache else None
        result = []
        if not resultList:
            return []
        else:
            for each in resultList:
                obj = {
                    "searchTerm": each[0],
                    "searchDate": each[1]
                }
                result.append(obj)
            result.sort(key=lambda x:x['searchDate'], reverse=True)
            return result

 #Delete Search History Term
    def resolve_deleteSearchHistoryTerm(self, info, **kwargs):
        userId = kwargs.get('userId')
        searchTerm = kwargs.get('searchTerm')

        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        
        if searchTerm is not None:
            if searchTerm and searchTerm.strip():
                client  = redis_connect()
                search_history_cache = get_hashmap_from_cache(client, str(userId)+"_search_history")
                state = False
                if search_history_cache:
                    print(search_history_cache.getAll())
                    state = delete_hashmap_from_cache(client, str(userId)+"_search_history", searchTerm)

                # if state:
                #     # set_hashmap_to_cache(client, str(userId)+"_search_history", state)
                #     return stringType(True)
                # else:
                    state = True
                return stringType("successfully deleted" if state else "not successful")
            else:
                raise BadRequestException("invalid request; searchTerm provided is empty")
        else:
            raise BadRequestException("invalid request; searchTerm provided is invalid")
        
 #Delete Search History Cache
    def resolve_deleteSearchHistory(self, info, **kwargs):
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
                key = str(userId)+"_search_history"
                client = redis_connect()
                state = delete_routes_from_cache(client, key)
                return stringType("successfully deleted" if state else "not successful")
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")

 #Get Blocked User List by User Id
    def resolve_blockedUsers(self, info, **kwargs):
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        
        result = []
        blockedList = []
        try:
            blockedList += UserBlocked.objects.using('default').filter(user_id=userId).values_list('block_user_id', flat=True)
            return [{'user_id': each} for each in blockedList]
        except UserBlocked.DoesNotExist:
            return []

 # Get Query Place -- Google Maps -- Places API
    def resolve_queryPlaces(self,info,**kwargs):
        userId = kwargs.get('userId')
        searchContent = kwargs.get('searchContent')
        if userId:
            try:
                user= User.objects.using('default').get(user_id=userId)
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
        r = requests.get(url + 'query='+searchContent+ '&key='+api_key)
        data = r.json()
        result = []
        print(data)
        for i in range(len(data['results'])):
            result.append(APIPlacesListType(name=data['results'][i]['name']))
        return result

 # Get User Personal Info
    def resolve_userPersonalInfo(self, info, **kwargs):
        userId = kwargs.get('userId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
                return UserPersonalInfoObjectType(email=user.email, phone_number=user.phone_number, gender=user.gender, dob=user.DOB)
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")

 # Get Thread List of Chat Request       
    def resolve_requestThreadList(self, info, **kwargs):
            user_id = kwargs.get('userId')
            page = kwargs.get('page')
            limit = kwargs.get('limit')
            if user_id is not None:
                try:
                    user = User.objects.using('default').get(user_id=user_id)
                except User.DoesNotExist:
                    raise NotFoundException("userId provided not found")
            else:
                raise BadRequestException("invalid request; userId provided is invalid")
            dialogs = []
            dialogs += ChatThread.objects.using('default').filter(participant_id__contains=[user_id]).values_list('thread_id', 'modified', 'is_approved')#, 'created', 'user1_id', 'user2_id')
            dialogs.sort(key=lambda x:x[1], reverse = True)
            result = []
            for each in dialogs:
                # messages = []
                # recent_message = []
                # has_unread = False
                # if user_id == each[3]:
                #     flag = 0
                # else:
                #     flag = 1
                # participant = User.objects.using('default').get(user_id=each[3]) if flag == 1 else User.objects.using('default').get(user_id=each[4])
                
                # recent_message += ChatMessage.objects.using('default').filter(dialog_id=each[0]).values_list('id', 'modified', 'text', 'read', 'sender_id')

                # recent_message.sort(key = lambda x:x[1], reverse=True)

                # for each_message in recent_message:
                #     messages.append({"id": each_message[0], "date_created": each_message[1], "message": each_message[2]})
                #     if not each_message[3] and not each_message[4]==user_id :
                #         has_unread = True
                if not each[2]:
                    result.append({
                        "threadId": each[0],
                        # "date_modified": each[1],
                        # "participants": [{
                        #     "username":participant.username,
                        #     "id": participant.user_id,
                        #     "avatar": participant.avatar
                        #     }],
                        # "recent_message":messages[0],
                        # "has_unread":has_unread
                    })
            if len(result)>0:
                if page and limit:
                    totalPages = math.ceil(len(result)/limit)
                    if page <= totalPages:
                        start = limit*(page-1)
                        result = result[start:start+limit]

                        return ChatThreadsPageListType(threads=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                    else:
                        raise BadRequestException("invalid request; page provided exceeded total")
                elif page == limit == None:
                    return ChatThreadsPageListType(threads=result, page_info=PageInfoObject(nextPage= None, limit=None))
                elif page is None:
                    raise BadRequestException("invalid request; limit cannot be provided without page")
                elif limit is None:
                    raise BadRequestException("invalid request; page cannot be provided without limit")
                
            else:
                return ChatThreadsPageListType(threads=[], page_info=PageInfoObject(nextPage= None, limit=None))
            
            return result

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
                return UserReasonDetailObjectType(report_user_reason_id=reasonId, reason = reason.reason, description=reason.description)
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
                return PostReasonDetailObjectType(report_post_reason_id=reasonId, reason = reason.reason, description=reason.description)
            except ReportPostReason.DoesNotExist:
                raise NotFoundException("reportPostReasonId provided not found")
        else:
            raise BadRequestException("invalid request; reportPostReasonId provided is invalid")


"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                                                                        POST MUTATION
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""  


#This function Uploads the media files into the AWS S3 buket
# depending on the folder, key and file.

def upload_to_aws(file, bucket_location, folder, key):
    
    success = True
    # s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    #Creating Session With Boto3.
    session = boto3.Session(
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    #Creating S3 Resource From the Session.
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    # print(type(file.name))
    
    try:
        print(file)
        # with open(file, "rb") as f:
        #     # fo = io.BytesIO(f)
        s3.upload_fileobj(file, bucket_location, folder+key)
            # s3.Bucket(bucket_location).upload_file(f, folder+key)
        print("Upload Successful")
        return True

    except Exception as err:

        print('An error occurred uploading file to S3: %s' % err)
        return False


class aggregateOutput(graphene.ObjectType):
    count = graphene.Int()

class aggregateOutputObjectType(graphene.ObjectType):
    aggregate = graphene.Field(aggregate)

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

    class Arguments:
        title = graphene.String()
        userRating = graphene.Float()
        isVerifiedBooking = graphene.Boolean()
        userId = graphene.Int()
        description = graphene.String()
        venueId = graphene.String()
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
        if uid is not None:
            try:
                user = User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        

        #upload the media into the S3 bucket
        last_post = Post.objects.all().aggregate(Max('post_id'))
        print(last_post['post_id__max']+1)
        post_id = last_post['post_id__max']+1
        aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
        folder_name = "post-videos/"
        file_name = "post_video_"+str(post_id)+".mp4"
        media_link = aws_link+folder_name+file_name
        print(media)
        success_upload = upload_to_aws(media, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
        print(success_upload)
        print(media_link)

        #upload the thumbnail into the S3 bucket
        thumbnail_folder_name = "thumbnail/"
        thumbnail_file_name = "post_thumbnail_"+str(post_id)+".jpg"
        thumbnail_media_link = aws_link+thumbnail_folder_name+thumbnail_file_name
        thumbnail_success_upload = upload_to_aws(thumbnail, settings.AWS_STORAGE_BUCKET_NAME, thumbnail_folder_name, thumbnail_file_name)
        print(thumbnail_success_upload)
        print(thumbnail_media_link)

        # #add to the post model with all the details of the post.
        if success_upload:
            media_post = models.MediaPost.objects.create(
                media_post_id=MediaPost.objects.count()+1,
                url=media_link
            )
            if media_post.media_post_id is not None:
                post = models.Post.objects.create(
                    post_id=post_id, 
                    media=media_post.media_post_id, 
                    title=title,  
                    user_rating=userRating, 
                    is_verified_booking=isVerifiedBooking, 
                    date_created= datetime.datetime.now(), 
                    date_modified= datetime.datetime.now(), 
                    user_id=userId, 
                    description=description,
                    total_likes = 0,
                    total_saves = 0,
                    total_shares = 0,
                    total_comments = 0,
                    venue_id=venueId,
                    thumbnail=thumbnail_media_link
                    )
            

        
        #extracting the hashtags word and mentioned usernames separatly
        hashtag_list, mentioned_list = extract_tags_mentions(description)
        #adding the hashtag words into the respective tables in DB.
        for word in hashtag_list:
            try:
                go = Tag.objects.using('default').get(name=word)
                try:
                    PostTag.objects.using('default').get(post_id=post_id, tag_id=go.tag_id)
                except PostTag.DoesNotExist:
                    PostTag.objects.create(post_id=post_id, tag_id=go.tag_id)
            except Tag.DoesNotExist:
                go = Tag.objects.create( name=word)
                try:
                    PostTag.objects.using('default').get(post_id=post_id, tag_id=go.tag_id)
                except PostTag.DoesNotExist:
                    PostTag.objects.create(post_id=post_id, tag_id=go.tag_id)

        # #adding the mentions username into the respective tables in DB.
        for username in mentioned_list:
            try:
                go  = User.objects.using('default').get(username=username)
                PostMention.objects.create( post_id=post_id, user_id=go.userId)
            except User.DoesNotExist:
                pass
        
        return CreatePostMutation(message=success_upload)

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
            post.description= description
            
            #extract hastags and mentions
            hashtag_words, mention_words = [], []
            hashtag_words, mention_words = extract_tags_mentions(description)
            for word in hashtag_words:
                try:
                    tag_obj = Tag.objects.using('default').get(name=word)
                except Tag.DoesNotExist:
                    tag_obj = Tag.objects.create(name=word)
                    tag_obj.save()
                try:
                    post_tag_obj = PostTag.objects.using('default').get(Q(tag_id=tag_obj.tag_id)&Q(post_id=postId))
                except PostTag.DoesNotExist:
                    post_tag_obj = PosTag.objects.create(
                        tag_id = tag_obj.tag_id,
                        post_id = postId 
                    )
                    post_tag_obj.save()
            for word in mention_words:
                try:
                    mention_obj = PostMention.objects.using('default').get(user_id=userId, post_id=postId)
                except PostMention.DoesNotExist:
                    mention_obj = PostMention.objects.create(user_id=userId, post_id=postId)
                    mention_obj.save()
            post.save()
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
                post.total_likes = post.total_likes+1
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)
        

        try:
            post_like = PostLike.objects.using('default').get(user_id=user.user_id, post_id=post.post_id)
            raise NoContentException("conflict in request; unable to like post that is already liked", 409)

        except PostLike.DoesNotExist:
            last_post_like_id = PostLike.objects.using('default').all().aggregate(Max('post_like_id'))
            lastPostLikeId = last_post_like_id['post_like_id__max']+1 if last_post_like_id['post_like_id__max'] else 1
            post_like = models.PostLike.objects.create(
                post_like_id = lastPostLikeId,
                post_id = post.post_id,
                user_id = user.user_id
            )
            number_of_likes = post.total_likes
            post.save()
            post_like.save()
            
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
                post.total_likes = post.total_likes-1
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)
        
        try:
            post_like = models.PostLike.objects.using('default').get(post_id=postId, user_id=userId)
            number_of_likes = post.total_likes
            post.save()
            post_like.delete()

            return UpdatePostLikeMutation(post_likes_aggregate = aggregateOutputObjectType(aggregate=aggregateOutput(count=number_of_likes)), message="successfully unliked post", post_id=postId, user_id=userId)
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
                post.total_saves = post.total_saves+1
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

        try:
            post_save = PostSaved.objects.using('default').get(post_id = post.post_id, user_id=user.user_id)
            raise NoContentException("conflict in reuqest; unable to save post that is already saved", 409)
        except PostSaved.DoesNotExist:
            last_post_save_id = PostSaved.objects.using('default').all().aggregate(Max('post_saved_id'))
            lastPostSaveId = last_post_save_id['post_saved_id__max']+1 if last_post_save_id['post_saved_id__max'] else 1
            post_save = models.PostSaved.objects.create(
                post_saved_id = lastPostSaveId,
                post_id = postId,
                user_id = userId
            )
            number_of_saves = post.total_saves
            post.save()
            post_save.save()
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
                post.total_saves = post.total_saves-1
            except Post.DoesNotExist:
                raise NotFoundException("postId provided not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

        try:
            post_save = models.PostSaved.objects.using('default').get(post_id=postId, user_id=userId)  
            number_of_saves=post.total_saves
            post.save()
            post_save.delete()
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

        
        #Insert into UserSharedItinerary
        last_post_comment_id = PostComment.objects.using('default').all().aggregate(Max('post_comment_id'))
        lastPostCommentId = last_post_comment_id['post_comment_id__max']+1 if last_post_comment_id['post_comment_id__max'] else 1

        comment = PostComment.objects.create(
            post_comment_id =  lastPostCommentId,
            user_id = userId,
            post_id = postId if reply_post_id == None else reply_post_id,
            comment = comment,
            number_of_likes = 0,
            date_created = datetime.datetime.now(),
            comment_reply_id = commentReplyId
        )
        comment.save()
        post.total_comments = PostComment.objects.using('default').filter(post_id=postId).count()
        post.save()
        #extracting the hashtags word and mentioned usernames separatly
        hashtag_list, mentioned_list = extract_tags_mentions(comment.comment)
        #adding the hashtag words into the respective tables in DB.
        return_hashtags, return_mentions = [], []
        for word in hashtag_list:
            try:
                go = Tag.objects.using('default').get(name=word)
                try:
                    post_comment_tag = PostCommentTag.objects.using('default').get(post_comment_id=comment.post_comment_id, tag_id=go.tag_id)
                except PostCommentTag.DoesNotExist:

                    PostCommentTag.objects.create( post_comment_id=comment.post_comment_id, tag_id=go.tag_id)
            except Tag.DoesNotExist:
                go = Tag.objects.create( name=word)
                try:
                    post_comment_tag = PostCommentTag.objects.using('default').get(post_comment_id=comment.post_comment_id, tag_id=go.tag_id)
                except PostCommentTag.DoesNotExist:
                    PostCommentTag.objects.create(post_comment_id=comment.post_comment_id, tag_id=go.tag_id)
            return_hashtags.append(hashtagSection(go.name, go.tag_id))


        #adding the mentions username into the respective tables in DB.
        for username in mentioned_list:
            try:
                go_user  = User.objects.using('default').get(username=username)
                try:
                    PostCommentMention.objects.using('default').get(post_comment_id=comment.post_comment_id, user_id=go_user.user_id)
                except PostCommentMention.DoesNotExist:
                    last_post_comment_mention_id = PostCommentMention.objects.using('default').all().aggregate(Max('post_comment_mention_id'))
                    print(last_post_comment_mention_id)
                    lastPostCommentMentionId = last_post_comment_mention_id['post_comment_mention_id__max']+1 if last_post_comment_mention_id['post_comment_mention_id__max'] else 1
                    PostCommentMention.objects.using('default').create(post_comment_mention_id=lastPostCommentMentionId, post_comment_id=comment.post_comment_id, user_id=go_user.user_id)
            except User.DoesNotExist:
                pass
            return_mentions.append(mentionSection(go_user.username, go_user.user_id))
        return_comment = comment.comment

   
        

        # commentObj={
        #     "content": return_comment,
        #     "hashtags": return_hashtags,
        #     "mentions": return_mentions
        # }
        post.save()
        
        return PostCommentMutation(message="successfully added comment on post", comment=return_comment, hashtags=return_hashtags, mentions=return_mentions,  postCommentId= comment.post_comment_id , userId=userId, postId=postId, repliedCommentId=commentReplyId if commentReplyId is not None else None, post_comments_aggregate =aggregateOutputObjectType(aggregate=aggregateOutput(count= PostComment.objects.using('default').filter(post_id=postId).count())), post_comment_replies_aggregate = aggregateOutputObjectType(aggregate=aggregateOutput(count= PostComment.objects.using('default').filter(comment_reply_id=commentReplyId).count())))
    
"""
    Update Post Comment
"""
# class InputUpdatePostCommentType(graphene.InputObjectType):
    #     post_comment_id = graphene.Field(BigInt)
    #     comment = graphene.String()

class UpdatePostCommentMutation(graphene.Mutation):
    message = graphene.String()
    comment =graphene.String()
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
            #extracting the hashtags word and mentioned usernames separatly
            hashtag_list, mentioned_list = extract_tags_mentions(comment)
            #adding the hashtag words into the respective tables in DB.
            for word in hashtag_list:
                try:
                    print(word) 
                    go = Tag.objects.using('default').get(name=word)
                    print("try")
                    try:
                        post_comment = PostCommentTag.objects.using('default').get(post_comment_id=comment_obj.post_comment_id, tag_id=go.tag_id)
                    except PostCommentTag.DoesNotExist:
                        PostCommentTag.objects.create( post_comment_id=comment_obj.post_comment_id, tag_id=go.tag_id)
                        pass
                except Tag.DoesNotExist:
                    print("else")
                    # Tag.objects.create( name=word)
                    go = Tag.objects.create( name=word)

                    try:
                        post_comment = PostCommentTag.objects.using('default').get(post_comment_id=comment_obj.post_comment_id, tag_id=go.tag_id)
                    except PostCommentTag.DoesNotExist:
                        PostCommentTag.objects.create( post_comment_id=comment_obj.post_comment_id, tag_id=go.tag_id)
                        pass



            #adding the mentions username into the respective tables in DB.
            for username in mentioned_list:
                try:
                    go  = User.objects.using('default').get(username=username)
                    try:
                        PostCommentMention.objects.using('default').get(post_comment_id=comment_obj.post_comment_id, user_id=go.user_id)
                    except PostCommentMention.DoesNotExist:
                        last_post_comment_mention_id = PostCommentMention.objects.using('default').all().aggregate(Max('post_comment_mention_id'))
                        lastPostCommentMentionId = last_post_comment_mention_id['post_comment_mention_id__max']+1 if last_post_comment_mention_id['post_comment_mention_id__max'] else 1
                        PostCommentMention.objects.create(post_comment_mention_id=lastPostCommentMentionId, post_comment_id=comment_obj.post_comment_id, user_id=go.user_id)
                        pass
                except User.DoesNotExist:
                    pass
            updated_comment = comment
            comment_obj.comment = comment
            comment_obj.save()
            return UpdatePostCommentMutation(message="Successfully updated comment on post", comment=updated_comment, postCommentId = postCommentId, post_comments_aggregate =aggregateOutputObjectType(aggregate=aggregateOutput(count= PostComment.objects.using('default').filter(post_id=postId).count())))
        except PostComment.DoesNotExist:
            raise NotFoundException("postCommentId provided not found", 404)
    
"""
    Delete Post Comment
"""
# class InputDeleteCommentLikeType(graphene.InputObjectType):
    #     post_comment_id = graphene.Field(BigInt)

class DeletePostCommentMutation(graphene.Mutation):
    message = graphene.String()
    postCommentId=graphene.Int()
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
            comment = models.PostComment.objects.using('default').get(post_comment_id=postCommentId)
            repliedCommentId = None
            postId = comment.post_id
            # replies_comments = PostComment.objects.using('using').filter(comment_reply_id=postCommentId)
            # for each in replies_comments:

            if comment.comment_reply_id:
                repliedCommentId = comment.comment_reply_id
            else:
                repliedCommentId = None
            comment.delete()
            post = models.Post.objects.using('default').get(post_id=postId)
            post.total_comments = PostComment.objects.using('default').filter(post_id=postId).count()
            post.save()
            return DeletePostCommentMutation(message="successfully deleted comment on post", postCommentId=postCommentId, post_comments_aggregate =aggregateOutputObjectType(aggregate=aggregateOutput(count= PostComment.objects.using('default').filter(post_id=postId).count())), repliedCommentId=repliedCommentId, post_comment_replies_aggregate =aggregateOutputObjectType(aggregate=aggregateOutput(count= PostComment.objects.using('default').filter(comment_reply_id=repliedCommentId).count())))
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
                comment = models.PostComment.objects.using('default').get(post_comment_id=postCommentId)
                comment.number_of_likes = comment.number_of_likes +1
                number_of_likes = comment.number_of_likes
                try:
                    comment_like = PostCommentLike.objects.using('default').get(user_id=userId, post_comment_id=postCommentId)
                    raise NoContentException("conflict in request; unable to like comment that is already liked", 409)
                except PostCommentLike.DoesNotExist:
                    last_post_comment_like_id = PostCommentLike.objects.using('default').all().aggregate(Max('post_comment_like_id'))
                    lastPostCommmentLikeId = last_post_comment_like_id['post_comment_like_id__max']+1 if last_post_comment_like_id['post_comment_like_id__max'] else 1
                    comment_like = models.PostCommentLike.objects.create(
                        post_comment_like_id = lastPostCommmentLikeId,
                        user_id = userId,
                        post_comment_id = postCommentId
                    )
                    comment_like.save()
                comment.save()
                return CommentLikeMutation(message="Successfully liked comment on post", post_comment_likes_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=number_of_likes)), user_id = userId, post_comment_id=postCommentId)
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
                comment = models.PostComment.objects.using('default').get(post_comment_id=postCommentId)
                comment.number_of_likes = comment.number_of_likes -1
                number_of_likes = comment.number_of_likes
                try:
                    comment_like = models.PostCommentLike.objects.using('default').get(user_id=userId, post_comment_id=postCommentId)
                    comment_like.delete()                  
                except PostCommentLike.DoesNotExist:
                    raise NoContentException("conflict in request; unable to unlike comment that is already unliked", 409)
                comment.save()
                return CommentLikeMutation(message="Successfully unliked comment on post", post_comment_likes_aggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=number_of_likes)), post_comment_id = postCommentId, user_id = userId)
            else:
                raise BadRequestException("invalid request; postCommentId provided is invalid", 400)
            
        except PostComment.DoesNotExist:
            raise NotFoundException("postCommentId provided not found", 404)


"""..................................................................................END POST.............................................................................................."""




"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                                                                        USER MUTATION
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""  

'''
Register User 
'''
class CreateUserMutation(graphene.Mutation):
    message = graphene.String()
    token = graphene.String()
    class Arguments:
        email = graphene.String()
        password =  graphene.String()
        username = graphene.String() 
        name = graphene.String()

    def mutate(root, info, **kwargs):
        email = kwargs.get('email')
        password = kwargs.get('password')
        username = kwargs.get('username')
        name = kwargs.get('name')

        # #upload the media into the S3 bucket
        # aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
        # folder_name = "user-profile-media/"
        # file_name = "user_profile_"+str(user_data.user_id)
        # media_link = aws_link+folder_name+file_name
        # success_upload = upload_to_aws(user_data.avatar, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
        # userid = int("20210001")+User.objects.count()
        # print(success_upload)
        # print(media_link)
        
        #add to the post model with all the details of the post.
        # if not success_upload:
        #     media_link = ""
        if email is not None:
            if email and email.strip():
                pass
            else:
                raise BadRequestException("invalid request; email provided is empty", 400)
        else:
            raise BadRequestException("invalid request; email provided is invalid", 400)
        if password is not None:
            if password and password.strip():
                pass
            else:
                raise BadRequestException("invalid request; password provided is empty", 400)
        else:
            raise BadRequestException("invalid request; password provided is invalid", 400)
        if username is not None:
            if username and username.strip():
                if any(ele.isupper() for ele in username):
                    raise BadRequestException("invalid request; username provided has upper case letters", 400)
                else:
                    pass
            else:
                raise BadRequestException("invalid request; username provided is empty", 400)
        else:
            raise BadRequestException("invalid request; username provided is invalid", 400)
        if name is not None:
            if name and name.strip():
                pass
            else:
                raise BadRequestException("invalid request; name provided is empty", 400)
        else:
            raise BadRequestException("invalid request; name provided is invalid", 400)

        try:
            usermails = User.objects.using('default').filter(email__icontains=email).values_list('email', flat=True)
            if email in usermails:
                raise BadRequestException("conflict in request; email provided is already in use", 409)
        except User.DoesNotExist:
            pass
        try:
            usernames = User.objects.using('default').filter(username__icontains=username).values_list('username', flat=True)
            if username in usernames:
                raise BadRequestException("conflict in request; username provided is already in use", 409)
        except User.DoesNotExist:
            pass
        last_user_id = PostLike.objects.using('default').all().aggregate(Max('user_id'))
        lastUserId = last_user_id['user_id__max']+1 if last_user_id['user_id__max'] else 1
        user = models.User.objects.create(
            user_id = lastUserId,
            email = email,
            password = encrypt_password(password),
            username = username,
            is_active = False,
            first_name = name.split(' ')[0],
            last_name = name.split(' ')[1],
            date_created = datetime.datetime.now(timezone.utc),
            # date_joined = datetime.datetime.now(timezone.utc),
            level = 1,
            is_activated = False
            )
        print("ds")
        user.save()
        # if avatar is not None:
        #     media = models.MediaUser.create(
        #         media_user_id=MediaUser.objects.count()+1,
        #         url="media_link"
        #     )
        #     media.save()
        #add to user profile table as well.
        if user.user_id is not None:
            profile_number = "2021_"+str(UserProfile.objects.count()+1)
            profile = models.UserProfile.objects.create(
                profile_id = int(profile_number),
                user_id = user.user_id, 
            )
        # Send mail for verification
        response = sendMailToUser(name, username, email)
        print(response)
        # userPayload = jwt_payload(user)
        # userToken = jwt_encode(userPayload)
        # token = UserToken.objects.create(
        #     user_id = user.userId,
        #     token = userToken
        # )

        # token.save()
        
        profile.save()
        return CreateUserMutation(message=str(response['message']), token=response['token'])

'''
Reset Password
'''
class ResetPasswordMutation(graphene.Mutation):
    message = graphene.String()

    class Arguments():
        userId = graphene.Int()
        password = graphene.String()
        token = graphene.String()

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        password = kwargs.get('password')
        token = kwargs.get('token')
        sessionObj = ''
        sessionObj = info.context.session[token]
       
        
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not provided", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if password is not None:
            if password and password.strip():
                pass
            else:
                raise BadRequestException("invalid request; password provided is empty", 400)
        else:
            raise BadRequestException("invalid request; password provided is invalid", 400)
        if sessionObj:
            pass
        else:
            raise AuthorizationException("conflict in request; password code is not verified")
        
        # user = User.objects.using('default').get(user_id=userId)
        user.password = encrypt_password(password)
        user.save()
        del info.context.session[token]
        return ResetPasswordMutation(message='successfully updated reset the password')

# '''
# Update User 
# '''
# class InputUpdateUserType(graphene.InputObjectType):
    # user_id = graphene.Argument(BigInt)
    # email = graphene.String()
    # password = graphene.String() 
    # phone_number = graphene.Argument(BigInt)
    # avatar = Upload()
    # featured_video = Upload()
    # city = graphene.String()
    # bio = graphene.String()
    # bio_link = graphene.String()

# class UpdateUserMutation(graphene.Mutation):
    # class Arguments:
    #     user_data = InputUpdateUserType()
    # user = graphene.Field(UserType)
    # userprofile = graphene.Field(UserProfileType)

#     def mutate(self, info, user_data):
        
        # user = User.objects.using('default').get(pk=user_data.user_id)
        # userprofile = UserProfile.objects.using('default').get(user_id=user_data.user_id)

        # aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
        # folder_name = "user-profile-media/"


        # if user_data.email is not None:
        #     user.email = user_data.email
        # if user_data.password is not None:
        #     user.password = encrypt_password(user_data.password)
        # if user_data.phone_number is not None:
        #     user.phone_number = user_data.phone_number
        # if user_data.avatar is not None:
        #     file_name = "user_profile_avatar"+str(user_data.user_id)+".png"
        #     media_link = aws_link+folder_name+file_name
        #     success_upload = upload_to_aws(user_data.avatar, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
        #     user.avatar = media_link
        # if user_data.featured_video is not None:
        #     file_name = "user_profile_featured_video"+str(user_data.user_id)+".mp4"
        #     media_link = aws_link+folder_name+file_name
        #     success_upload = upload_to_aws(user_data.featured_video, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
        #     userprofile.featured_video = media_link
        # if user_data.city is not None:
        #     userprofile.city = user_data.city
        # if user_data.bio is not None:
        #     userprofile.bio = user_data.bio
        # if user_data.bio_link is not None:
        #     userprofile.bio_link = user_data.bio_link
        # user.save()
        # userprofile.save()
        # return UpdateUserMutation(user=user, userprofile=userprofile)
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
        if authUserId is not None:
            try:
               user = User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid", 400)
        
        if recipientUserId is not None:
            try:
               user = User.objects.using('default').get(user_id=recipientUserId)
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid", 400)
        try:
            follower_table = UserFollower.objects.using('default').get(user_id=recipientUserId, follower_user_id=authUserId)
            raise ConflictException("conflict in request; authUserId already follows recipientUserId", 409)
        except UserFollower.DoesNotExist:
            last_user_follower_id = UserFollower.objects.using('default').all().aggregate(Max('user_follower_id'))
            lastUserFollowerId = last_user_follower_id['user_follower_id__max']+1 if last_user_follower_id['user_follower_id__max'] else 1
            follower_table = UserFollower.objects.create(
                user_follower_id = lastUserFollowerId,
                user_id = recipientUserId,
                follower_user_id = authUserId       
                )
            follower_table.save()
        try:
            following_table = UserFollowing.objects.using('default').get(user_id=authUserId, following_user_id=recipientUserId)
            raise ConflictException("conflict in request; authUserId already follows recipientUserId", 409)
        except UserFollowing.DoesNotExist: 
            last_user_following_id = UserFollowing.objects.using('default').all().aggregate(Max('user_following_id'))
            lastUserFollowingId = last_user_following_id['user_following_id__max']+1 if last_user_following_id['user_following_id__max'] else 1
            following_table = UserFollowing.objects.create(
                user_following_id=lastUserFollowingId,
                user_id = authUserId,
                following_user_id = recipientUserId
            )
            following_table.save()
        following_count= UserFollowing.objects.using('default').filter(user_id=authUserId).count()
        return FollowUserMutation(message="Successfully followed provided recipientUserId", followingAggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=following_count)), recipientUserId=recipientUserId, authUserId= authUserId)

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
        if authUserId is not None:
            try:
               user = User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid", 400)
        
        if recipientUserId is not None:
            try:
               user = User.objects.using('default').get(user_id=recipientUserId)
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid", 400)

        try:
            follower_table = UserFollower.objects.using('default').get(user_id=recipientUserId, follower_user_id=authUserId)
            follower_table.delete()
        except UserFollower.DoesNotExist:
            raise ConflictException("conflict in request; authUserId unable to remove recipientUserId that is not being followed", 409)
        try:
            following_table = UserFollowing.objects.using('default').get(user_id=authUserId, following_user_id=recipientUserId)
            following_table.delete()
        except UserFollowing.DoesNotExist:
            raise ConflictException("conflict in request; authUserId unable to remove recipientUserId that is not being followed", 409)
        following_count= UserFollowing.objects.using('default').filter(user_id=authUserId).count()

        return UnfollowUserMutation(message="Successfully unfollowed provided recipientUserId",  followingAggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=following_count)), recipientUserId = recipientUserId, authUserId=authUserId)
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
        if authUserId is not None:
            try:
               user = User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid", 400)
        
        if recipientUserId is not None:
            try:
               user = User.objects.using('default').get(user_id=recipientUserId)
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid", 400)

        try:
            follower_table = UserFollower.objects.using('default').get(user_id=authUserId, follower_user_id=recipientUserId)
            follower_table.delete()
        except UserFollower.DoesNotExist:
            raise ConflictException("conflict in request; authUserId unable to unfollow recipientUserId that is not being followed", 409)
        try:
            following_table = UserFollowing.objects.using('default').get(user_id=recipientUserId, following_user_id=authUserId)
            following_table.delete()
        except UserFollowing.DoesNotExist:
            raise ConflictException("conflict in request; authUserId unable to unfollow recipientUserId that is not being followed", 409)
        follower_count= UserFollower.objects.using('default').filter(user_id=authUserId).count()

        return RemoveFollowerUserMutation(message="successfully removed provided recipientUserId from followers",  followerAggregate=aggregateOutputObjectType(aggregate=aggregateOutput(count=follower_count)), recipientUserId = recipientUserId, authUserId=authUserId)
         
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
        if uid is not None:
            try:
                User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        try:
            user_profile = UserProfile.objects.using('default').get(user_id=uid)
        except UserProfile.DoesNotExist:
            raise NotFoundException("userId provided has not created a profile", 404)

        aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
        folder_name = "user-profile-media/"
        file_name = "featured_video_"+str(uid)+".mp4"
        media_link = aws_link+folder_name+file_name
        success_upload = upload_to_aws(media, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
        if success_upload:
            user_profile = UserProfile.objects.using('default').get(user_id=uid)
            # media_user = MediaUser.objects.create(media_user_id=MediaUser.objects.all().aggregate(Max('media_user_id'))+1 if MediaUser.objects.count() != 0 else: 1)
            user_profile.featured_video = media_link
            user_profile.save()
            print(success_upload)
            print(media_link)
            return UploadFeaturedVideoMutation(message="Successfully uploaded the video", url = media_link)
        return UploadFeaturedVideoMutation(message="Unsuccessful upload")


"""
    Edit Username in User Profile
"""
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
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
            try:
                userprofile = UserProfile.objects.using('default').get(user_id=uid)
                if username is not None:
                    if (username and username.strip()):
                        try:
                            username_list = User.objects.using('default').get(username=username)
                            if username_list.user_id != uid:
                                raise ConflictException("conflict in request; username provided already used", 409)
                            else:
                                user.username = username
                                user.save()
                                return EditUsernameMutation(message="Successfully updated username", username= username, user_id=userId)
                        except User.DoesNotExist:
                            user.username = username
                            user.save() 
                            return EditUsernameMutation(message="Successfully updated username", username= username, user_id=userId)
                    else:
                        raise BadRequestException("invalid request; username provided is empty", 400)
                else:
                    raise BadRequestException("invalid request; username provided is invalid", 400)
            except UserProfile.DoesNotExist:
                raise NotFoundException("user profile for provided userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        

"""
    Update User Profile
"""
class EditUserProfileMutation(graphene.Mutation):
    message = graphene.String()
    userId = graphene.Field(BigInt)
    name = graphene.String()
    location = graphene.Field(LocationObject)
    bio = graphene.String()
    bioLink = graphene.String()

    class Arguments():
        userId = graphene.Argument(BigInt)
        name = graphene.String()
        location = locationObject()
        bio = graphene.String()
        bioLink = graphene.String()

    def mutate(self, info, **kwargs):
        uid = kwargs.get('userId')
        name = kwargs.get('name')
        # username = username
        location = kwargs.get('location')
        bio = kwargs.get('bio')
        bio_link = kwargs.get('bioLink')
        if uid is not None:
            try:
                User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        try:
            UserProfile.objects.using('default').get(user_id=uid)
        except UserProfile.DoesNotExist:
            raise NotFoundException("user profile for provided userId not found", 404)
        if name is not None:
            pass
        else:
            raise BadRequestException("invalid request; name provided is invalid", 400)
        
        if location is not None:
            pass
        else:
            raise BadRequestException("invalid request; location provided is invalid", 400)

        
        if uid is not None:
            user = User.objects.using('default').get(user_id=uid)
            userprofile = UserProfile.objects.using('default').get(user_id=uid)
            # #username edited
            # if username != user.username:
            #     user.username = username
            # else:
            #     pass

            #name edited
            if name != userprofile.name:
                userprofile.name = name
            else:
                pass

            #bio
            if bio is not None:
                #bio edited
                userprofile.bio = bio
                #extract hastags and mentions 
                hashtag_list, mentioned_list = extract_tags_mentions(bio)
                #adding the hashtag words into the respective tables in DB.
                for word in hashtag_list:
                    try:
                        go = Tag.objects.using('default').get(name=word)
                        try:
                            user_profile_tag = UserBioTag.objects.using('default').get(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)
                        except UserBioTag.DoesNotExist:

                            UserBioTag.objects.create(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)
                    except Tag.DoesNotExist:
                        go = Tag.objects.create(name=word)
                        try:
                            user_profile_tag = UserBioTag.objects.using('default').get(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)
                        except UserBioTag.DoesNotExist:
                            UserBioTag.objects.create(user_profile_id=userprofile.profile_id, tag_id=go.tag_id)


                #adding the mentions username into the respective tables in DB.
                for m_username in mentioned_list:
                    try:
                        go  = User.objects.using('default').get(username=m_username)
                        try:
                            UserBioMention.objects.using('default').get(user_profile_id=userprofile.profile_id, user_id=go.user_id)
                        except UserBioMention.DoesNotExist:
                            UserBioMention.objects.create(user_profile_id=userprofile.profile_id, user_id=go.user_id)
                    except User.DoesNotExist:
                        pass
       
            else:
                raise BadRequestException("invalid request; bio provided is invalid", 400)

            #Bio Link
            if bio_link is not None:
                userprofile.bio_link = bio_link
            else:
                raise BadRequestException("invalid request; bioLink provided is invalid", 400)
            
            #location
            if location is not None:
                try:
                    location_obj = Location.objects.using('default').get(city=location.city, country=location.country)
                
                except Location.DoesNotExist:
                    if location == {}:
                        location_obj = None
                    else:
                        location_obj = Location.objects.create(
                            city = location.city,
                            country = location.country,
                            latitude = location.latitude,
                            longitude = location.longitude
                        )
                        location_obj.save()
                userprofile.location = location_obj
            #save data 
            user.save()
            userprofile.save()

            return EditUserProfileMutation(message="Successfully edited the profile provided", userId = uid, name=name, bio=bio, location=location, bioLink=bio_link)
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
        if uid is not None:
            try:
                User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        try:
            UserProfile.objects.using('default').get(user_id=uid)
        except UserProfile.DoesNotExist:
            raise NotFoundException("user profile for provided userId not found", 404)  
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
        for tag in tags_list:
            try:
                user_profile_tag_obj = UserProfileTag.objects.using('default').get(user_profile_tag_id=tag)
            except UserProfileTag.DoesNotExist:
                user_profile_tag_obj = UserProfileTag.objects.create(user_profile_tag_id=tag)
            user_profile_tag_obj.save()
            try:
                user_tag_obj = UserTag.objects.using('default').get(user_id=uid, user_profile_tag_id=user_profile_tag_obj.user_profile_tag_id)
            except UserTag.DoesNotExist:
                user_tag_obj = UserTag.objects.create(user_id=uid, user_profile_tag_id=user_profile_tag_obj.user_profile_tag_id)
            user_tag_obj.save()
        try:
            list_obj = UserProfileTagList.objects.using('default').get(user_id=uid)
            list_obj.user_profile_tag_list = tags_list
            list_obj.save()
        except UserProfileTagList.DoesNotExist:
            list_obj = UserProfileTagList.objects.create(
               user_id = uid,
               user_profile_tag_list = tags_list 
            )
            list_obj.save()
        
        
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
                last_user_profile_tag = UserProfileTag.objects.using('default').all().aggregate(Max('user_profile_tag_id'))
                if last_user_profile_tag['user_profile_tag_id__max']:
                    last_user_profile_tag_id = last_user_profile_tag['user_profile_tag_id__max']+1
                else:
                    last_user_profile_tag_id = 1
                try:

                    user_profile_tag = UserProfileTag.objects.using('default').create(
                        user_profile_tag_id = last_user_profile_tag_id,
                        name = name
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
        gender = graphene.String()
        dob = graphene.Date()

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        email = kwargs.get('email')
        phoneNumber = kwargs.get('phoneNumber')
        gender = kwargs.get('gender')
        dob = kwargs.get('dob')

        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId porvided is not found")
        else:
            raise BadRequestException("invalid request; userId proivded is invalid")
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
        

        if email is not None or user.email is None:
            user.email = email
        if phoneNumber is not  None or user.phone_number is None:
            user.phone_number = phoneNumber
        if user.gender is None or gender is not None:
            user.gender = gender
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
        print(authUserId)
        print(recipientUserId)
        if authUserId is not None:
            try:
                user = User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found")
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid")
        if recipientUserId is not None:
            try:
                blockUser = User.objects.using('default').get(user_id=recipientUserId)
                try:
                    UserBlocked.objects.using('default').get(user_id=recipientUserId, block_user_id=authUserId)
                    raise ConflictException("conflict in request; blockedUSerId provided does not exist")
                except UserBlocked.DoesNotExist:
                    pass
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided is not found")
        else:
            raise BadRequestException("invalid request; recipientUserId is invalid")
        
        try:
            last_user_blocked_id = UserBlocked.objects.using('default').all().aggregate(Max('user_blocked_id'))
            lastUserBlockedId = last_user_blocked_id['user_blocked_id__max']+1 if last_user_blocked_id['user_blocked_id__max'] else 1
            user_blocked = UserBlocked.objects.using('default').create(
                user_blocked_id = lastUserBlockedId,
                user_id = authUserId,
                block_user_id = recipientUserId 
            )
            user_blocked.save()
        except :
            raise BadRequestException("recipientUserId provided is already blocked")

        return BlockUserMutation(message="successfull blocked the provided recipientUserId", authUserId=authUserId, recipientUserId=recipientUserId)

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
        print(authUserId)
        print(blockUserId)
        if authUserId is not None:
            try:
                user = User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found")
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid")
        if blockUserId is not None:
            try:
                blockUser = User.objects.using('default').get(user_id=blockUserId)
                # removeBlock = []
                try:
                    removeBlock = UserBlocked.objects.using('default').get(user_id=authUserId, block_user_id=blockUserId)
                    removeBlock.delete()
                    return RemoveBlockUserMutation(message="successful removed blocked user provided", authUserId=authUserId, recipientUserId=blockUserId)
                except UserBlocked.DoesNotExist:
                    raise ConflictException("conflict in request; recipientUserId provided is not blocked")
                        
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided is not found")
        else:
            raise BadRequestException("invalid request; recipientUserId is invalid")

        
"""..................................................................................END USER................................................................................................"""


"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                                                                        USER ACCOUNT MUTATION
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""  


"""
    Login User
"""
class userType(graphene.InputObjectType):
    userId = graphene.Argument(BigInt)
    username = graphene.String()
    email = graphene.String()
    name = graphene.String()

class LoginUserMutation(graphene.Mutation):
    user = graphene.Field(UserType)
    message = graphene.String()
    #token = graphene.String()
    # user = userType()
    # verification_prompt = graphene.String()

    class Arguments:
        username = graphene.String()
        password = graphene.String()
        

    def mutate(self, info, username, password):
        if username is not None:
            pass
        else:
            raise BadRequestException("invalid request; email provided is invalid", 400)
        if password is not None:
            pass
        else:
            raise BadRequestException("invalid request; password provided is invalid", 400)
        
        
        s = SessionStore()
        
        user = authenticateLogin(email=username, password=password)
        
        error_message = 'username or password provided is not authorized to login'
        success_message = "user provided logged in successfully"
        verification_error = 'conflict in request; provided email is not verified'
        if user is not None:
            try:
                userToken = UserToken.objects.using('default').get(user_id=user.user_id)
            except UserToken.DoesNotExist:
                userToken = UserToken.objects.create(user_token = UserToken.objects.count()+1, user_id=user.user_id)
            user.last_login = datetime.datetime.now()
            user.save()
            userTokenPayload = {
                'userId': user.user_id,
                'username': user.username,
                'recommendedPosts': []
            }
            # payload = jwt_payload(userTokenPayload)
            token = jwt_encode(userTokenPayload)
            token = str(token)
            if user.is_activated:
                userToken.token = token
                
                #Session login
                user_session = {
                    'username': user.username,
                    'userId': user.user_id,
                    'avatar': user.avatar,
                    'token': token,
                    'history': {}
                }
                # if s.SessionStore(session_key=):
                #     request.user.session_key
                # else:
                user_id = str(user.user_id)
                info.context.session[user_id] = {}
                if info.context.session[user_id] != {}:
                    raise AuthorizationException("you are already logged in", 401)
                else:
                    print("here")
                    info.context.session[user_id] = user_session
                    print(info.context.session[user_id])
                    
                # s.create()
                # s['user_info'] = user_session
                # s.set_expiry(None)
                # print(s.get_expiry_date())
                # print(s.keys())
                # print(s.session_key)

                userToken.save()
                client = redis_connect()
                cache = set_routes_to_cache(client, user.user_id, token)
                key  = str(user.user_id)+"_search_history"
                # print(get_hashmap_from_cache(client, key))
                if get_hashmap_from_cache(client, key):
                    print("there")
                    search_cache = get_hashmap_from_cache(client, key)
                else:
                    print("not there")
                    search_history_cache = LRUCache(35)
                    # search_history_cache.put()
                    search_cache = set_hashmap_to_cache(client, key, search_history_cache)
                if cache :
                    return LoginUserMutation(user = user, message=success_message)
            else:
                raise AuthorizationException(verification_error, 409)

        raise AuthorizationException(error_message, 401)

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
                reportPost.date_modified = datetime.datetime.now()
                reportPost.save()
                response = sendPostReportMailToUser(postUser.username, postUser.email, reason.reason)
                if response:
                    return ReportPostMutation(message="successfully updated report for the provided post", reasonId=reasonId, postId=postId, reporterId=reporterId)
        except ReportPost.DoesNotExist:
            print("in Except block")
            reportPost = ReportPost.objects.create(
                report_post_id = ReportPost.objects.count()+1,
                reason_id = reason.report_post_reason_id,
                reporter_id = user.user_id,
                post_id = post.post_id,
                count = 1,
                date_created = datetime.datetime.now(),
                date_modified = datetime.datetime.now(),
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
                reportUser.date_modified = datetime.datetime.now()
                reportUser.save()
                response = sendUserReportMailToUser(user2.username, user2.email, reason.reason)
                
                if response:
                    return ReportUserMutation(message="successfully updated report for the provided user", reasonId=reasonId, userId=userId, reporterId = reporterId)
        except ReportUser.DoesNotExist:

            reportUser = ReportUser.objects.create(
                report_user_id = ReportUser.objects.count()+1,
                reporter_id = user1.user_id,
                user_id = user2.user_id,
                reason_id = reason.report_user_reason_id,
                count = 1,
                date_created = datetime.datetime.now(),
                date_modified = datetime.datetime.now()
            )
            response = sendUserReportMailToUser(user2.username, user2.email, reason.reason)
            reportUser.save()
            if response:
                return ReportUserMutation(message="successfully reported the provided user", reasonId=reasonId, userId=userId)


"""..................................................................................END USER ACCOUNT................................................................................................"""

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                                                                        VENUE MUTATION
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""  


"""
This is a Mutation Function to insert Venue(venue_id, is_external)
"""
class InputVenueType(graphene.InputObjectType):
    class Meta:
        model = Venue
    venue_id = graphene.String()
    is_external = graphene.Boolean()
    venue_price = graphene.String()
    venue_location = graphene.String()

    def resolve_venue_price(self, info):
        if self.is_external:
            return None
        else:
            result_venue = VenueInternal.objects.using('default').get(pk=self.venue_id)
            return str(result_venue.price) 
    def resolve_venue_location(self, info):
        if self.is_external:
            obj = VenueExternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.location)
        else:
            obj = VenueInternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.location)

# class CreateVenueMutation(graphene.Mutation):
#     class Arguments:
#         vendorId= graphene.Int()
#         title= graphene.Int()


"""
This is a Mutation Function to insert Internal Venue
""" 
class InputVenueInternalType(graphene.InputObjectType):
    class Meta:
        model = VenueInternal
    name = graphene.String(), 
    price = graphene.Boolean(), 
    description = graphene.String(), 
    location = graphene.String(), 
    latitude = graphene.Boolean(), 
    longitude = graphene.Boolean(), 
    venue_id = graphene.String(), 
    type = graphene.String()

class CreateVenueInternalMutation(graphene.Mutation):
    class Arguments:
        venue_data = InputVenueInternalType()
    venue_internal = graphene.Field(VenueInternalType)
    def mutate(self, info, venue_data):
        venue_internal = models.VenueInternal.objects.create(
            name = venue_data.name, 
            price = venue_data.name, 
            description = venue_data.description, 
            location = venue_data.location, 
            latitude = venue_data.latitude, 
            longitude = venue_data.longitude, 
            venue_id = venue_data.venue_id, 
            type = venue_data.type
        )
        venue_internal.save()

"""
This is a Mutation Function to insert External Venue
"""
class InputVenueExternalType(graphene.InputObjectType):
    class Meta:
        model = VenueExternal
    api_id = graphene.String(),
    name = graphene.String(),  
    description = graphene.String(), 
    location = graphene.String(), 
    latitude = graphene.Boolean(), 
    longitude = graphene.Boolean(), 
    venue_id = graphene.String()

class CreateVenueExternalMutation(graphene.Mutation):
    class Arguments:
        venue_data = InputVenueExternalType()
    venue_external = graphene.Field(VenueExternalType)
    def mutate(self, info, venue_data):
        venue_external = models.VenueExternal.objects.create(
            name = venue_data.name, 
            price = venue_data.name, 
            description = venue_data.description, 
            location = venue_data.location, 
            latitude = venue_data.latitude, 
            longitude = venue_data.longitude, 
            venue_id = venue_data.venue_id, 
            type = venue_data.type
        )
        venue_external.save()


"""..................................................................................END VENUE............................................................................................."""

"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                                                                        CHAT MUTATION
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""  


"""
    Chat - Send Message 
"""
class ChatSendMessageMutation(graphene.Mutation):
    message_id = graphene.Int()
    thread_id = graphene.Int()
    auth_user_id = graphene.Int()
    recipient_user_id = graphene.List(UserIdFieldType)

    class Arguments:
        authUserId = graphene.Int()
        recipientUserId = graphene.List(BigInt)
        threadId = graphene.Int()
        message = graphene.String()

    def mutate(self, info, **kwargs):
        sender_user_id = kwargs.get('authUserId')
        receiver_user_id = kwargs.get('recipientUserId')
        thread_id = kwargs.get('threadId')
        text = kwargs.get('message')
        temp_threads =[]
        if sender_user_id is not None:
            try: 
                User.objects.using('default').get(user_id=sender_user_id)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found", 404)
        else:
            BadRequestException("invalid request; authUserId provided is invalid")
        if receiver_user_id:
            for each in receiver_user_id:
                try: 
                    User.objects.using('default').get(user_id=each)
                except User.DoesNotExist:
                    raise NotFoundException("recipientUserId provided is not found ---"+str(each)+"-- userId", 404)
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid")
        if text is None or text=="":
            raise NoContentException("invalid request; message provided is empty")
        if thread_id is not None:
            participants = []
            participants += receiver_user_id
            participants.append(sender_user_id)
            participants = list(set(sorted(participants)))
            try:
                thread = ChatThread.objects.using('default').get(participant_id__in=[participants])
                for each in thread.participant_id:
                    if each in participants:
                        print("here")
                        is_approved = True
                    else:
                        raise AuthorizationException("threadId provided doesnt match with authUserId")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")

        try:

            last_message = ChatMessage.objects.all().aggregate(Max('message_id'))
            if last_message['message_id__max']:
                message_id = last_message['message_id__max']+1
            else:
                message_id = 1
            participants = []
            participants += receiver_user_id
            participants.append(sender_user_id)
            participants = list(set(sorted(participants)))
            # print(participants)
            following = []
            # for each in participants: 
            temp_threads =[]
            for each in participants:
                following += UserFollowing.objects.using('default').filter(following_user_id=sender_user_id, user_id=each).values_list('user_id', flat=True)
                print(following)
                if following !=[]:
                    is_approved = True
                else:
                    temp_threads += ChatThread.objects.using('default').filter(created_by__in=receiver_user_id, participant_id__icontains=sender_user_id).values_list('thread_id', flat=True)
                    print(temp_threads)
                    if not temp_threads ==[]:
                        print("here")
                        is_approved = True
                        
                    else:
                        print("else")
                        is_approved = False

            dialog = ChatThread.objects.using('default').get(participant_id__in=[participants])
            print(dialog.thread_id)
            dialog.modified = datetime.datetime.now()
            # for each in dialog.participant_id:
            #     if each in participants:
            #         print("here")
            #         is_approved = True
                    
            if is_approved:
                dialog.is_approved = True
                
                
            chat_message = ChatMessage.objects.create(
                created = datetime.datetime.now(),
                modified = datetime.datetime.now(),
                is_removed = False,
                message_id = message_id,
                text = text,
                read = False,
                recipient_id = list(set(sorted(receiver_user_id))),
                sender_id = sender_user_id,
                thread_id = dialog.thread_id
            )
            try:
                deleteThread = ChatDeleteThread.objects.using('default').filter(thread_id=dialog.thread_id)
                print("fsd")
                print(deleteThread)
                for each in deleteThread:
                    each.delete()
            except ChatDeleteThread.DoesNotExist:
                pass
            chat_message.save()
            dialog.save()
        except ChatThread.DoesNotExist:
            print('ds')
            # raise Exception
            participants = []
            participants += receiver_user_id
            participants.append(sender_user_id)
            participants = list(set(sorted(participants)))
            following = []
            temp_threads = []
            for each in participants:
                following += UserFollowing.objects.using('default').filter(following_user_id=sender_user_id, user_id=each).values_list('user_id', flat=True)
                print(following)
                if following !=[]:
                    is_approved = True
                else:
                    temp_threads += ChatThread.objects.using('default').filter(created_by__in=receiver_user_id, participant_id__icontains=sender_user_id).values_list('thread_id', flat=True)
                    print(temp_threads)
                    if not temp_threads ==[]:
                        print("here")
                        is_approved = True
                        
                    else:
                        print("else")
                        is_approved = False
            

            last_dialogs = ChatThread.objects.all().aggregate(Max('thread_id'))
            if last_dialogs['thread_id__max']:
                dialog_id = last_dialogs['thread_id__max']+1
            else:
                dialog_id = 1
            last_message = ChatMessage.objects.all().aggregate(Max('message_id'))
            if last_message['message_id__max']:
                message_id = last_message['message_id__max']+1
            else:
                message_id = 1
            name =''
            for one in participants:
                one = User.objects.using('default').get(user_id=one)
                
                name += one.username
                if len(participants)>2:
                    name += ','
            if len(participants)>2:
                name = None
            dialog = ChatThread.objects.create(
                created = datetime.datetime.now(),
                modified = datetime.datetime.now(),
                thread_id = dialog_id,
                name = name,
                participant_id = list(set(sorted(participants))),
                is_approved = is_approved,
                created_by = sender_user_id,
                admin = [sender_user_id]
            )
            dialog.save()
            chat_message = ChatMessage.objects.create(
                created = datetime.datetime.now(),
                modified = datetime.datetime.now(),
                is_removed = False,
                message_id = message_id,
                text = text,
                read = False,
                recipient_id = list(set(sorted(receiver_user_id))),
                sender_id = sender_user_id,
                thread_id = dialog.thread_id
            )
            
            
            chat_message.save()

        return ChatSendMessageMutation(recipient_user_id=[{"user_id": each} for each in receiver_user_id], message_id=chat_message.message_id, thread_id = chat_message.thread_id, auth_user_id=sender_user_id)


"""
    Post/Venue - Share Message
"""
class TemplateObjectType(graphene.InputObjectType):
    type = graphene.String()
    id = graphene.String()

class ShareObjectType(graphene.InputObjectType) :
    template = graphene.Field(TemplateObjectType)
    link = graphene.String()

class AttachmentOutputObjectType(graphene.ObjectType) :
    type = graphene.String()
    id = graphene.String()

class ChatSendMessageSharesMutation(graphene.Mutation):

    message_id = graphene.Int()
    recipient_user_id = graphene.List(UserIdFieldType)
    auth_user_id = graphene.Int()
    threadId = graphene.Int()
    # attachment = graphene.Field(AttachmentOutputObjectType)

    class Arguments:
        authUserId = graphene.Int()
        recipientUserId = graphene.List(BigInt)
        message = graphene.String()
        threadId = graphene.Int()
        # isPost = graphene.Boolean()
        shareObj = graphene.Argument(ShareObjectType)

    def mutate(self, info, **kwargs):
        auth_user_id = kwargs.get('authUserId')
        receiver_user_id = kwargs.get('recipientUserId')
        thread_id = kwargs.get('threadId')
        text = kwargs.get('message')
        # is_post = kwargs.get('isPost')
        shareObj = kwargs.get('shareObj')

        if auth_user_id is not None:
            try: 
                User.objects.using('default').get(user_id=auth_user_id)
                try:
                    deleteThread = ChatDeleteThread.objects.using('default').filter(thread_id=thread_id)
                    print("dsad")
                    for each in deleteThread:
                        each.delete()
                except ChatDeleteThread.DoesNotExist:
                    pass
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid")
        
        if receiver_user_id is not None:
            for each in receiver_user_id:
                try: 
                    User.objects.using('default').get(user_id=each)
                except User.DoesNotExist:
                    raise NotFoundException("recipientUserId provided is not found ---"+str(each)+"-- userId", 404)
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid")
        # if text is None or text=="":
        #     raise NoContentException("text is empty")
        if shareObj:
            try:
                print(shareObj.template.type)
                shareTypeObj = ShareType.objects.using('default').get(name = shareObj.template.type)
            except ShareType.DoesNotExist:
                raise NotFoundException("shareType provided is not found")
            if shareObj.template.type =='post':
                try:
                    postObj = Post.objects.using('default').get(post_id=str(shareObj.template.id))
                except ValueError:
                    raise BadRequestException("postId provided not found")
                except Post.DoesNotExist:
                    raise NotFoundException("postId provided not found")
            elif shareObj.template.type == 'venue':
                try:
                    venueObj = Venue.objects.using('default').get(venue_id=shareObj.template.id)
                except Venue.DoesNotExist:
                    raise NotFoundException("venueId provided not found")
        else:
            raise BadRequestException("invalid request; shareObj provided is invalid")
        temp_threads=[]
        following=[]
        if thread_id is not None:
            participants = []
            participants += receiver_user_id
            participants.append(auth_user_id)
            participants = list(set(sorted(participants)))
            for each in participants:
                following += UserFollowing.objects.using('default').filter(following_user_id=auth_user_id, user_id=each).values_list('user_id', flat=True)
                print(following)
                if following !=[]:
                    is_approved = True
                else:
                    temp_threads += ChatThread.objects.using('default').filter(created_by__in=receiver_user_id, participant_id__icontains=auth_user_id).values_list('thread_id', flat=True)
                    print(temp_threads)
                    if not temp_threads ==[]:
                        print("here")
                        is_approved = True
                        
                    else:
                        print("else")
                        is_approved = False
            try:
                thread = ChatThread.objects.using('default').get(participant_id__in=[participants])
                for each in thread.participant_id:
                    if each in participants:
                        pass
                    else:
                        raise AuthorizationException("threadId provided doesnt match with authUserId")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")
        
        try:

            last_message = ChatMessage.objects.all().aggregate(Max('message_id'))
            if last_message['message_id__max']:
                message_id = last_message['message_id__max']+1
            else:
                message_id = 1
            participants = []
            participants += receiver_user_id
            participants.append(auth_user_id)
            participants = list(set(sorted(participants)))
            for each in participants:
                following += UserFollowing.objects.using('default').filter(following_user_id=auth_user_id, user_id=each).values_list('user_id', flat=True)
                print(following)
                if following !=[]:
                    is_approved = True
                else:
                    temp_threads += ChatThread.objects.using('default').filter(created_by__in=receiver_user_id, participant_id__icontains=auth_user_id).values_list('thread_id', flat=True)
                    print(temp_threads)
                    if not temp_threads ==[]:
                        print("here")
                        is_approved = True
                        
                    else:
                        print("else")
                        is_approved = False
            # for each in participants:
            #     try:
            #         UserFollowing.objects.using('default').filter(following_user_id=auth_user_id)
            #         is_approved = True
            #     except UserFollowing.DoesNotExist:
            #         try:
            #             ChatThread.objects.using('default').get(participant_id__icontains=[each,auth_user_id])
            #             is_approved = True
            #         except ChatThread.DoesNotExist:
            #             is_approved = False
            dialog = ChatThread.objects.using('default').get(participant_id__in=[participants])
            dialog.modified = datetime.datetime.now()
            
            chat_message = ChatMessage.objects.create(
                created = datetime.datetime.now(),
                modified = datetime.datetime.now(),
                is_removed = False,
                message_id = message_id,
                text = text,
                read = False,
                recipient_id = list(set(sorted(receiver_user_id))),
                sender_id = auth_user_id,
                thread_id = dialog.thread_id,
                share_type_id = shareTypeObj.share_type_id
            )
            try:
                deleteThread = ChatDeleteThread.objects.using('default').filter(thread_id=dialog.thread_id)
                print("fsd")
                print(deleteThread)
                for each in deleteThread:
                    each.delete()
            except ChatDeleteThread.DoesNotExist:
                pass
            chat_message.save()
            dialog.save()
        except ChatThread.DoesNotExist:
            last_dialogs = ChatThread.objects.all().aggregate(Max('thread_id'))
            if last_dialogs['thread_id__max']:
                dialog_id = last_dialogs['thread_id__max']+1
            else:
                dialog_id = 1
            last_message = ChatMessage.objects.all().aggregate(Max('message_id'))
            if last_message['message_id__max']:
                message_id = last_message['message_id__max']+1
            else:
                message_id = 1
            participants = []
            participants += receiver_user_id
            participants.append(auth_user_id)
            participants = list(set(sorted(participants)))
            for each in participants:
                following += UserFollowing.objects.using('default').filter(following_user_id=auth_user_id, user_id=each).values_list('user_id', flat=True)
                print(following)
                if following !=[]:
                    is_approved = True
                else:
                    temp_threads += ChatThread.objects.using('default').filter(created_by__in=receiver_user_id, participant_id__icontains=auth_user_id).values_list('thread_id', flat=True)
                    print(temp_threads)
                    if not temp_threads ==[]:
                        print("here")
                        is_approved = True
                        
                    else:
                        print("else")
                        is_approved = False
            name =''
            for one in participants:
                one = User.objects.using('default').get(user_id=one)
                
                name += one.username
                if len(participants)>2:
                    name += ','
            if len(participants)>2:
                name = None
            dialog = ChatThread.objects.create(
                created = datetime.datetime.now(),
                modified = datetime.datetime.now(),
                thread_id = dialog_id,
                name= name,
                participant_id = list(set(sorted(participants))),
                is_approved = is_approved,
                created_by = auth_user_id,
                admin = [auth_user_id]
            )
            dialog.save()
            chat_message = ChatMessage.objects.create(
                created = datetime.datetime.now(),
                modified = datetime.datetime.now(),
                is_removed = False,
                message_id = message_id,
                text = text,
                read = False,
                recipient_id = list(set(sorted(receiver_user_id))),
                sender_id = auth_user_id,
                thread_id = dialog.thread_id,
                share_type_id = shareTypeObj.share_type_id
            )
            chat_message.save()

        if shareObj.template:
            if shareObj.template.type=='Post':
                try:
                    shareObj.template.id= int(shareObj.template.id)
                    postObj = Post.objects.using('default').get(post_id=shareObj.template.id)
                    last_post_shared = PostShared.objects.using('default').all().aggregate(Max('post_shared_id'))['post_shared_id__max']
                    postSharedObj = PostShared.objects.using('default').create(
                        post_shared_id = last_post_shared + 1 if last_post_shared else 1,
                        post_id = postObj.post_id,
                        sender_user_id = auth_user_id,
                        receiver_user_id = list(set(sorted(receiver_user_id))),
                        chat_message_id = chat_message.message_id
                    )

                    postSharedObj.save()
                except Post.DoesNotExist:
                    raise NotFoundException("postId provided not found")
                
            elif shareObj.template.type=='Venue':
                try:
                    venueObj = Venue.objects.using('default').get(venue_id=shareObj.template.id)
                    last_venue_shared = VenueShared.objects.using('default').all().aggregate(Max('venue_shared_id'))['venue_shared_id__max']
                    venueSharedObj = VenueShared.objects.using('default').create(
                        venue_shared_id = last_venue_shared + 1 if last_venue_shared else 1,
                        venue_id = venueObj.venue_id,
                        sender_id = auth_user_id,
                        receiver_id = list(set(sorted(receiver_user_id))),
                        chat_message = chat_message
                    )

                    venueSharedObj.save()
                except Venue.DoesNotExist:
                    raise NotFoundException("venueId provided not found")

        else:
            raise BadRequestException("invalid request; shareObj provided is invalid")

        return ChatSendMessageSharesMutation(recipient_user_id=[{"user_id": each} for each in receiver_user_id], auth_user_id=auth_user_id, message_id=chat_message.message_id, threadId=dialog.thread_id)#, attachment=AttachmentOutputObjectType(attachment.type,attachment.id))

"""
    Add Reaction to Message
"""
class AddReactionMessageMutation(graphene.Mutation):
    message = graphene.String()
    user_id = graphene.Int()
    message_id = graphene.Int()
    reaction_type_id = graphene.Int()

    class Arguments:
        messageId = graphene.Int()
        userId = graphene.Int()
        reactionTypeId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        messageId = kwargs.get('messageId')
        reactionTypeId = kwargs.get('reactionTypeId')
        if userId:
            try:
                user= User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if messageId:
            try:
                message = ChatMessage.objects.using('default').get(message_id=messageId)
            except ChatMessage.DoesNotExist:
                raise NotFoundException("messageId provided not found")
        else:
            raise BadRequestException("invalid request; messageId provided is invalid")
        if reactionTypeId:
            try:
                reaction = models.ChatMessageReactionType.objects.using('default').get(chat_message_reaction_type_id=reactionTypeId)
            except models.ChatMessageReactionType.DoesNotExist:
                raise NotFoundException("reactionTypeId provided not found")
        else:
            raise BadRequestException("invalid request; reactionTypeId provided is invalid")
        
        

            
       
        try:
            ChatMessage.objects.using('default').get(Q(message_id=messageId) & Q(Q(recipient_id__icontains=[userId]) | Q(sender_id=userId)))
            try:
                ChatMessageReaction.objects.using('default').get(message_id=messageId, user_id=userId, reaction_type_id=reactionTypeId)
            except ChatMessageReaction.DoesNotExist:
                last_chat_message_reaction_obj = ChatMessageReaction.objects.using('default').all().aggregate(Max('chat_message_reaction_id'))
                if last_chat_message_reaction_obj['chat_message_reaction_id__max']:
                    chatmessagereaction_id = last_chat_message_reaction_obj['chat_message_reaction_id__max']+1
                else:
                    chatmessagereaction_id = 1
                chat_message_reaction_obj = ChatMessageReaction.objects.using('default').create(
                    chat_message_reaction_id = chatmessagereaction_id,
                    message = message,
                    user = user,
                    reaction_type = reaction
                )
                chat_message_reaction_obj.save()

            return AddReactionMessageMutation(message="successfully added reaction to this message", message_id=messageId, user_id=userId, reaction_type_id=reactionTypeId)
        except ChatMessage.DoesNotExist:
            raise AuthorizationException("userId provided is not authorized to react to this message")
        
"""
    Delete Reaction to message
"""      
class DeleteReactionMessageMutation(graphene.Mutation):
    message = graphene.String()
    user_id = graphene.Int()
    message_id = graphene.Int()
    reaction_type_id = graphene.Int()
    class Arguments:
        messageId = graphene.Int()
        userId = graphene.Int()
        reactionTypeId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        messageId = kwargs.get('messageId')
        reactionTypeId = kwargs.get('reactionTypeId')
        if userId:
            try:
                user= User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if messageId:
            try:
                message = ChatMessage.objects.using('default').get(message_id=messageId)
            except ChatMessage.DoesNotExist:
                raise NotFoundException("messageId provided not found")
        else:
            raise BadRequestException("invalid request; messageId provided is invalid")
        if reactionTypeId:
            try:
                reaction = models.ChatMessageReactionType.objects.using('default').get(chat_message_reaction_type_id=reactionTypeId)
            except models.ChatMessageReactionType.DoesNotExist:
                raise NotFoundException("reactionTypeId provided not found")
        else:
            raise BadRequestException("invalid request; reactionTypeId provided is invalid")
        
        try:
            ChatMessage.objects.using('default').get(Q(message_id=messageId) & Q(Q(recipient_id__icontains=[userId]) | Q(sender_id=userId)))
            try:
                reaction = ChatMessageReaction.objects.using('default').get(user_id=userId, message_id=messageId, reaction_type_id=reactionTypeId)
                reaction.delete()
                return DeleteReactionMessageMutation(message="successfully delete the reaction ", user_id=userId, message_id=messageId, reaction_type_id=reactionTypeId)
            except ChatMessageReaction.DoesNotExist:
                raise ConflictException("conflict in request; unable to remove reaction that is not liked")   
        except ChatMessage.DoesNotExist:
            raise AuthorizationException("userId provided is not authorized to remove reaction to this message")
            

"""
    Delete Message
"""
class DeleteMessageMutation(graphene.Mutation):
    message = graphene.String()
    userId = graphene.Int()
    message_id = graphene.Int()

    class Arguments:
        userId = graphene.Int()
        messageId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        authUserId = kwargs.get('userId')
        message_id = kwargs.get('messageId')
        if authUserId is not None:
            try:
                User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if message_id is not None:
            try:
                message = ChatMessage.objects.using('default').get(message_id=message_id)
                if message.sender_id == authUserId:
                    message.delete()
                    return DeleteMessageMutation(message="successfully deleted the message", message_id=message_id, userId=authUserId)
                else:
                    raise AuthorizationException("userId provided is not authorized to delete this message")
                
            except ChatMessage.DoesNotExist:
                raise NotFoundException("messageId provided is not found")
        else:
            raise BadRequestException("invalid request; messageId provided is invalid")

"""
    Delete Chat Thread 
"""
class DeleteThreadMutation(graphene.Mutation):
    threadId = graphene.Int()
    userId = graphene.Int()
    message = graphene.String()

    class Arguments:
        userId = graphene.Int()
        threadId = graphene.Int()
    
    def mutate(self, info, **kwagrs):
        userId = kwagrs.get('userId')
        threadId = kwagrs.get('threadId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if threadId is not None:
            try:
                thread = ChatThread.objects.using('default').get(thread_id=threadId)
                if userId in thread.participant_id: 
                    try:
                        ChatDeleteThread.objects.using('default').get(thread_id=threadId, user_id=userId)
                        raise ConflictException("conflict in request; unable to delete provided thread that has already deleted")
                    except ChatDeleteThread.DoesNotExist:
                        last_chat_delete_thread = ChatDeleteThread.objects.using('default').all().aggregate(Max('chat_delete_thread_id'))
                        if last_chat_delete_thread['chat_delete_thread_id__max']:
                            last_chat_delete_thread_id = last_chat_delete_thread['chat_delete_thread_id__max']+1
                        else:
                            last_chat_delete_thread_id = 1
                        deleted_thread = ChatDeleteThread.objects.using('default').create(
                            chat_delete_thread_id = last_chat_delete_thread_id,
                            thread_id = threadId,
                            user_id = userId
                        )
                        deleted_thread.save()
                        return DeleteThreadMutation(message="successful delete thread", userId = userId, threadId = threadId)
                else:
                    raise AuthorizationException("userId provided is not authorized to delete this thread")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")
        
"""
    Add Member To Group Chat Thread
"""     
class AddMemberGroupThreadMutation(graphene.Mutation):
    authUserId = graphene.Int()
    recipientUserId = graphene.Int()
    threadId = graphene.Int()
    message = graphene.String()

    class Arguments:
        authUserId = graphene.Int()
        threadId = graphene.Int()
        recipientUserId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        auth_user_id = kwargs.get('authUserId')
        recipient_user_id = kwargs.get('recipientUserId')
        thread_id = kwargs.get('threadId')
        if auth_user_id is not None:
            try:
                User.objects.using('default').get(user_id=auth_user_id)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found")
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid")
        if recipient_user_id is not None:
            try:
                User.objects.using('default').get(user_id=recipient_user_id)
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided is not found")
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using("default").get(thread_id = thread_id)
                if len(thread.participant_id)<=2:
                    raise ConflictException("conflict in request; unable to add member into a direct chat thread")
                try:
                    ChatThread.objects.using('default').get(participant_id__icontains=auth_user_id, thread_id=thread_id)
                except ChatThread.DoesNotExist:
                    raise AuthorizationException("authUserId provided is not authorized to add member")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")
        
        if recipient_user_id not in thread.participant_id:
            thread.participant_id.append(recipient_user_id)
            thread.participant_id = list(set(sorted(thread.participant_id)))
            thread.save()
            return AddMemberGroupThreadMutation(message="successfully added the userId provide into the chat thread", threadId = thread_id, authUserId=auth_user_id, recipientUserId = recipient_user_id)
        else:
            raise ConflictException("conflict in request; unable to add provided recipientUserId that is already added")
        
"""
    Remove Member from Group Chat Thread
"""            
class RemoveMemberGroupThreadMutation(graphene.Mutation):
    threadId = graphene.Int()
    authUserId = graphene.Int()
    recipientUserId = graphene.Int()
    message = graphene.String()

    class Arguments:
        threadId = graphene.Int()
        authUserId = graphene.Int()
        recipientUserId = graphene.Int()

    def mutate(self, info, **kwargs):
        auth_user_id = kwargs.get('authUserId')
        recipient_user_id = kwargs.get('recipientUserId')
        thread_id = kwargs.get('threadId')
        if auth_user_id is not None:
            try:
                User.objects.using('default').get(user_id=auth_user_id)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found")
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid")
        if recipient_user_id is not None:
            try:
                User.objects.using('default').get(user_id=recipient_user_id)
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided is not found")
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using("default").get(thread_id = thread_id)
                if len(thread.participant_id)<=2:
                    raise ConflictException("conflict in request; unable to remove member from a direct chat thread")
                if auth_user_id not in thread.admin and auth_user_id in thread.participant_id:
                    raise AuthorizationException("authUserId provided is not the group admin to remove member")
                try:
                    ChatThread.objects.using('default').get(participant_id__icontains=auth_user_id, thread_id=thread_id)
                except ChatThread.DoesNotExist:
                    raise AuthorizationException("authUserId provided is not authorized to remove member")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")   
        if recipient_user_id in thread.participant_id:
            thread.participant_id.remove(recipient_user_id)
            thread.participant_id = list(set(sorted(thread.participant_id)))
            thread.save()
            return RemoveMemberGroupThreadMutation(message="successfully removed recipientUserId from provided threadId", threadId=thread_id, authUserId=auth_user_id, recipientUserId = recipient_user_id)
        else:
            raise ConflictException("conflict in request; unable to remove member that is not present")

"""
    Change Group Photo
"""
class ChangeGroupPhotoMutation(graphene.Mutation):
    message = graphene.String()
    threadId = graphene.Int()
    userId = graphene.Int()
    avatar = graphene.String()

    class Arguments:
        threadId = graphene.Int()
        userId = graphene.Int()
        avatar = Upload()
    
    def mutate(self, info, **kwargs):
        user_id = kwargs.get('userId')
        thread_id = kwargs.get('threadId')
        photo = kwargs.get('avatar')
        if user_id is not None:
            try:
                User.objects.using('default').get(user_id=user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using("default").get(thread_id = thread_id)
                if len(thread.participant_id)<=2:
                    raise ConflictException("conflict in request; unable to change photo to a direct chat thread")
                if user_id not in thread.admin:
                    raise AuthorizationException("userId provided is not authorized to change photo of the group")
                try:
                    ChatThread.objects.using('default').get(participant_id__icontains=user_id, thread_id=thread_id)
                except ChatThread.DoesNotExist:
                    raise AuthorizationException("userId provided is not authorized to view this thread")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")  
        if photo is not None:
            # last_post = Post.objects.all().aggregate(Max('post_id'))
            # print(last_post['post_id__max']+1)
            aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
            folder_name = "chat-avatar/"
            file_name = "chat_avatar"+str(thread.thread_id)+".jpg"
            media_link = aws_link+folder_name+file_name
            print(media)
            success_upload = upload_to_aws(media, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
            print(success_upload)
            print(media_link)
            if success_upload:
                thread.photo=media_link
                thread.save()
                return ChangeGroupPhotoMutation(message="successfully modified the avatar", thread_id=thread_id, user_id=user_id, avatar=media_link)
            else:
                return ChangeGroupPhotoMutation(message="upload unsuccessful", thread_id=thread_id, user_id=user_id, avatar=None)

"""
    Change Group Name
"""
class ChangeGroupNameMutation(graphene.Mutation):
    threadId = graphene.Int()
    userId = graphene.Int()
    name = graphene.String()
    message = graphene.String()

    class Arguments:
        userId = graphene.Int()
        threadId = graphene.Int()
        name = graphene.String()
    
    def mutate(self, info, **kwargs):
        user_id= kwargs.get('userId')
        thread_id = kwargs.get('threadId')
        name = kwargs.get('name')
        if user_id is not None:
            try:
                User.objects.using('default').get(user_id=user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using("default").get(thread_id = thread_id)
                if len(thread.participant_id)<=2:
                    raise ConflictException("conflict in request; unable to change name to a direct chat thread")
                ## ADMIN PRIVILEGE CODE 
                # if user_id not in thread.admin and user_id in thread.participant_id:
                #     raise AuthorizationException("userId provided is not the group admin to change name")
                try:
                    ChatThread.objects.using('default').get(participant_id__icontains=user_id, thread_id=thread_id)
                except ChatThread.DoesNotExist:
                    raise AuthorizationException("userId provided is not authorized to view this thread")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")  
        if name is not None and name.strip():
            if len(name)>24:
                raise BadRequestException("invalid request; name provided exceeded the maximum length")
            thread.name = name
            thread.save()
            return ChangeGroupNameMutation(message="successfullly changed the name of the group", userId = user_id, threadId = thread_id, name = name)
        else:
            raise BadRequestException("invalid request; name provided is invalid")



"""
    Accept Request Chat
"""
class AcceptRequestChatThreadMutation(graphene.Mutation):
    user_id = graphene.Int()
    thread_id = graphene.Int()
    message = graphene.String()
    class Arguments:
        userId = graphene.Int()
        threadId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        user_id = kwargs.get('userId')
        thread_id = kwargs.get('threadId')
        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id = user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using('default').get(thread_id=thread_id)
                if thread.is_approved:
                    raise ConflictException("conflict in request; unable to approve since thread is already approved")
                else:
                    if user_id  not in thread.participant_id:
                        raise AuthorizationException("userId provided is not authorized to access this thread")
                    else:
                        thread.is_approved = True
                        thread.save()
                return AcceptRequestChatThreadMutation(message="successfully accepted the chat request", user_id=user_id, thread_id=thread_id)
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")

"""
    Decline Request Chat Thread
"""
class DeclineRequestChatThreadMutation(graphene.Mutation):
    user_id = graphene.Int()
    thread_id = graphene.Int()
    message = graphene.String()
    class Arguments:
        userId = graphene.Int()
        threadId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        user_id = kwargs.get('userId')
        thread_id = kwargs.get('threadId')
        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id = user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using('default').get(thread_id=thread_id)
                if user_id  not in thread.participant_id:
                    raise AuthorizationException("userId provided is not authorized to view this thread")
                else:
                    if thread.is_approved:
                        raise ConflictException("conflict in request; unable to decline threadId provided that is already approved")
                    else:
                        thread.delete()
                        return DeclineRequestChatThreadMutation(message="successfully declined the chat request", user_id=user_id, thread_id=thread_id)
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")

"""..................................................................................END CHAT............................................................................................."""


"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                                                                        ITINERARY MUTATION
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""  

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
                    
                    tagObj = Tag.objects.using('default').get(name = eachtag)
                except Tag.DoesNotExist:
                    last_tag = Tag.objects.using('default').all().aggregate(Max('tag_id'))
                    tagId = last_tag['tag_id__max']+1 if last_tag['tag_id__max'] else 1
                    tagObj = Tag.objects.using('default').create(
                        name = eachtag
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
            user_shared_itinerary_id = userSharedItineraryId,
            user_id = user.user_id,
            name = name,
            thumbnail = thumbnail_media_link,
            description = description,
            date_modified = datetime.datetime.now(),
            date_created = datetime.datetime.now()
        )
        user_shared_itinerary.save()

        #extracting the hashtags word and mentioned usernames separatly
        hashtag_list, mentioned_list = extract_tags_mentions(description)
        print(mentioned_list)
        #adding the hashtag words into the respective tables in DB.
        for word in hashtag_list:
            try:
                go = Tag.objects.using('default').get(name=word)
                try:
                    UserSharedItineraryTag.objects.using('default').get(user_shared_itinerary_id=userSharedItineraryId, tag_id=go.tag_id)
                except UserSharedItineraryTag.DoesNotExist:
                    last_user_shared_itinerary_tag = UserSharedItineraryTag.objects.using('default').all().aggregate(Max('user_shared_itinerary_tag_id'))
                    userSharedItineraryTagId = last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max']+1 if last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max'] else 1
                    UserSharedItineraryTag.objects.using('default').create(user_shared_itinerary_tag_id=userSharedItineraryTagId, user_shared_itinerary_id=userSharedItineraryId, tag_id=go.tag_id)
            except Tag.DoesNotExist:
                go = Tag.objects.create( name=word)
                try:
                    UserSharedItineraryTag.objects.using('default').get(user_shared_itinerary_id=userSharedItineraryId, tag_id=go.tag_id)
                except UserSharedItineraryTag.DoesNotExist:
                    last_user_shared_itinerary_tag = UserSharedItineraryTag.objects.using('default').all().aggregate(Max('user_shared_itinerary_tag_id'))
                    userSharedItineraryTagId = last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max']+1 if last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max'] else 1
                    UserSharedItineraryTag.objects.using('default').create(user_shared_itinerary_tag_id=userSharedItineraryTagId, user_shared_itinerary_id=userSharedItineraryId, tag_id=go.tag_id)

        # #adding the mentions username into the respective tables in DB.
        for username in mentioned_list:
            print(username)
            try:
                last_user_shared_itinerary_mention = UserSharedItineraryMention.objects.using('default').all().aggregate(Max('user_shared_itinerary_mention_id'))
                userSharedItineraryMentionId = last_user_shared_itinerary_mention['user_shared_itinerary_mention_id__max']+1 if last_user_shared_itinerary_mention['user_shared_itinerary_mention_id__max'] else 1
                go  = User.objects.using('default').get(username=username)
                print(go)
                UserSharedItineraryMention.objects.using('default').create( user_shared_itinerary_mention_id = userSharedItineraryMentionId, user_shared_itinerary_id=userSharedItineraryId, user_id=go.user_id)
            except User.DoesNotExist:
                pass
        #Separate Tags fields
        if tagObjs != []:
            for eachTagObj in tagObjs:
                last_user_shared_itinerary_tag = UserSharedItineraryTag.objects.using('default').all().aggregate(Max('user_shared_itinerary_tag_id'))
                userSharedItineraryTagId = last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max']+1 if last_user_shared_itinerary_tag['user_shared_itinerary_tag_id__max'] else 1
                user_shared_itinerary_tag = UserSharedItineraryTag.objects.using('default').create(
                    user_shared_itinerary_tag_id = userSharedItineraryTagId,
                    user_shared_itinerary_id = userSharedItineraryId,
                    tag_id = eachTagObj.tag_id
                )
                user_shared_itinerary_tag.save()
        else:
            pass
        
        if postObjs !=[]:
            for eachPostObj in postObjs:
                last_user_shared_itinerary_post = UserSharedItineraryPost.objects.using('default').all().aggregate(Max('user_shared_itinerary_post_id'))
                userSharedItineraryPostId = last_user_shared_itinerary_post['user_shared_itinerary_post_id__max']+1 if last_user_shared_itinerary_post['user_shared_itinerary_post_id__max'] else 1
                user_shared_itinerary_post = UserSharedItineraryPost.objects.using('default').create(
                    user_shared_itinerary_post_id = userSharedItineraryPostId,
                    user_shared_itinerary_id = userSharedItineraryId,
                    post_id = eachPostObj.post_id
                )
                user_shared_itinerary_post.save()
        else:
            raise NotFoundException("no posts found for provided postIds")

        return CreateItineraryMutation(user_shared_itinerary_id=userSharedItineraryId)

"""...........................................................................END ITINERARY........................................................................................................"""



"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                                                                        PAYMENT MUTATION
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""  

"""
    Payment - Add Card Option
"""
class PaymentCardMutation(graphene.Mutation):
    payment_option_id = graphene.Int()
    last_four_digits = graphene.Int()

    class Arguments:
        user_id = graphene.Int()
        card_number = graphene.Argument(BigInt)
        expiry_month = graphene.Int()
        expiry_year = graphene.Int()
        security_code = graphene.Int()
        cardName = graphene.String()
        billingName = graphene.String()
        streetAddress = graphene.String()
        city = graphene.String()
        state = graphene.String()
        zipcode = graphene.Int()

    def mutate(self, info, **kwargs):
        userId = kwargs.get('user_id')
        cardNumber = kwargs.get('card_number')
        expiryMonth = kwargs.get('expiry_month')
        expiryYear = kwargs.get('expiry_year')
        securityCode = kwargs.get('security_code')
        cardName = kwargs.get('cardName')
        billingName = kwargs.get('billingName')
        streetAddress = kwargs.get('streetAddress')
        city = kwargs.get('city')
        state = kwargs.get('state')
        zipcode = kwargs.get('zipcode')

        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if cardNumber is not None:
            print(cardNumber)
            last_four_digits = str(int(cardNumber))[-4:]
            print(last_four_digits)
            password_provided = "password"  # This is input in the form of a string
            password = password_provided.encode()  # Convert to type bytes
            salt = b'salt_'  # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100100,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password)) 
            f = Fernet(key)
            encrypted_card_number = f.encrypt(str(cardNumber).encode())
            print(encrypted_card_number)
        else:
            raise BadRequestException("invalid request; cardNumber provided is invalid", 400) 
        if expiryMonth is not None:
            if expiryMonth > 12:
                raise BadRequestException("invalid request; expiryMonth provided is invalid", 400)
            else:
                pass
        else:
            raise BadRequestException("invalid request; expiryMonth provided is invalid", 400) 
        if expiryYear is not None:
            pass
        else:
            raise BadRequestException("invalid request; expiryYear provided is invalid", 400) 
        if securityCode is not None:

            password_provided = "password"  # This is input in the form of a string
            password = password_provided.encode()  # Convert to type bytes
            salt = b'salt_'  # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password)) 
            f = Fernet(key)
            encrypted_security_card = f.encrypt(str(securityCode).encode())
            print(encrypted_security_card)
            
            # password_provided = "password"  # This is input in the form of a string
            # password = password_provided.encode()  # Convert to type bytes
            # salt = b'salt_'  # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
            # kdf = PBKDF2HMAC(
            #     algorithm=hashes.SHA256(),
            #     length=32,
            #     salt=salt,
            #     iterations=100000,
            #     backend=default_backend()
            # )
            # key = base64.urlsafe_b64encode(kdf.derive(password)) 
            # f = Fernet(key)
            # encrypted = b'gAAAAABh4gTuKyshpkptPVn0K9m3zoJ12bJ5cxzdKI3ZkLgcTKsB0jeJc0ZnfZmWQ792AfOHxtgrcKqIgAIdPwsrL3r_JahGqw=='
            # decrypted = f.decrypt(encrypted)
            # print(decrypted.decode()) 
        else:
            raise BadRequestException("invalid request; securityCode provided is invalid", 400) 
        if cardName is not None:
            if (cardName and cardName.strip()):
                pass
            else:
                raise BadRequestException("invalid request; cardName provided is empty")
        else:
            raise BadRequestException("invalid request; cardName provided is invalid")

        if billingName is not None:
            if (billingName and billingName.strip()):
                pass
            else:
                raise BadRequestException("invalid request; billingName provided is empty")
        else:
            raise BadRequestException("invalid request; billingName provided is invalid")
        
        if streetAddress is not None:
            if (streetAddress and streetAddress.strip()):
                pass
            else:
                raise BadRequestException("invalid request; streetAddress provided is empty")
        else:
            raise BadRequestException("invalid request; streetAddress provided is invalid")

        if city is not None:
            if (city and city.strip()):
                pass
            else:
                raise BadRequestException("invalid request; city provided is empty")
        else:
            raise BadRequestException("invalid request; city provided is invalid")

        if state is not None:
            if (state and state.strip()):
                pass
            else:
                raise BadRequestException("invalid request; state provided is empty")
        else:
            raise BadRequestException("invalid request; state provided is invalid")

        if zipcode is not None:
            pass
        else:
            raise BadRequestException("invalid request; zipcode provided is invalid")

        last_payment_option = PaymentOption.objects.using('payments').all().aggregate(Max('payment_option_id'))
        payment_option_id = last_payment_option['payment_option_id__max']+1 if last_payment_option['payment_option_id__max'] else 1
        
        option = PaymentOption.objects.using('payments').create(
            payment_option_id =payment_option_id,
            payment_option_type_id = 1,
            user_id = userId
        )
        option.save()

        last_billing_address = BillingAddress.objects.using('payments').all().aggregate(Max('billing_address_id'))
        billing_address_id = last_billing_address['billing_address_id__max']+1 if last_billing_address['billing_address_id__max'] else 1

        billing_address = BillingAddress.objects.using('payments').create(
            billing_address_id = billing_address_id,
            billing_name = billingName,
            email = user.email,
            address = streetAddress,
            city = city,
            state = state,
            zip = zipcode
        )
        billing_address.save()

        last_card_payment_detail = CardPaymentDetail.objects.using('payments').all().aggregate(Max('card_payment_detail_id'))
        card_payment_detail_id = last_card_payment_detail['card_payment_detail_id__max']+1 if last_card_payment_detail['card_payment_detail_id__max'] else 1 

        card = CardPaymentDetail.objects.using('payments').create(
            card_payment_detail_id = card_payment_detail_id,
            card_number = encrypted_card_number,
            expiry_month = expiryMonth,
            expiry_year = expiryYear,
            security_code = encrypted_security_card,
            billing_address_id = billing_address.billing_address_id,
            payment_option_id = option.payment_option_id,
            card_name = cardName
        )
        card.save()
        
        return PaymentCardMutation(payment_option_id=option.payment_option_id, last_four_digits= last_four_digits)
        

        
        
        # decryptor = PKCS1_OAEP.new(keyPair)
        # decrypted = decryptor.decrypt(encrypted)
        # print('Decrypted:', int(float(decrypted.decode())))

"""...........................................................................END PAYMENT........................................................................................................"""

""""-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                                                                        BADGES MUTATION
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
"""
    Pin Badges -- Array of 3
"""
class PinBadgesMutation(graphene.Mutation):
    message = graphene.String()
    badgesPinned = graphene.List(graphene.String)
    userId = graphene.Int()

    class Arguments:
        userId = graphene.Int()
        userBadges = graphene.List(graphene.Int)
    
    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        badges = kwargs.get('userBadges')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if badges is not None:
            if len(badges)<=3:
                pass
            else:
                raise BadRequestException("invalid request; userBadges provided exceeds limit (only 3 pinned badges allowed)")
            # try:
                # badgeObjs = Badge.objects.using('default').filter(badge_id=badges)
            for each in badges:
                try:
                    # print(each)
                    
                    userBadge = UserBadge.objects.using('default').get(user_id = userId, user_badge_id = each)
                    badge= Badge.objects.using('default').get(badge_id=userBadge.badge_id)
                    # except UserBadge.
                    if userBadge.is_pinned is None or userBadge.is_pinned == False:
                        userBadge.is_pinned = True
                        userBadge.save()
                        
                    # elif userBadge.is_pinned ==True:
                    #     return PinBadgesMutation(message="successfully pinned badges provided", badgesPinned=badges, userId = userId)
                except UserBadge.DoesNotExist:
                    raise NotFoundException("provided userBadgeId "+str(each)+" is not associated with provided userId")
                except Badge.DoesNotExist:
                    raise NotFoundException("badgeId: "+str(badge.badge_id)+" provided is not found")
            userBadges = UserBadge.objects.using('default').filter(user_id=userId)
            for each in userBadges:
                if each.badge_id not in badges:
                    each.is_pinned = False
                    each.save()
            return PinBadgesMutation(message="successfully pinned userBadges provided", badgesPinned = badges, userId = userId)
        else:
            raise BadRequestException("invalid request; userBadges provided is invalid")
        
        
        
    



"""...........................................................................END BADGES....................................................................................................."""
"""
    On Application Startup
"""
# class StartUpMutation(graphene.Mutation):
    #class Arguments:
        #pass
    #def mutate:
        #pass
        # def connection(WebSocket):
        #     """
        #         This is the function which should be initaited when you pull a message.
        #     """


class Mutation(graphene.ObjectType):
    #------------------------------------------------------------------------
    # on_opening = StartUpMutation.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    revoke_token = graphql_jwt.Revoke.Field()
    login = LoginUserMutation.Field()
    reset_password = ResetPasswordMutation.Field()
    
    register_user = CreateUserMutation.Field()
    # update_user = UpdateUserMutation.Field()

    report_post = ReportPostMutation.Field()
    report_user = ReportUserMutation.Field()

    #----------------------------------------------------------------------------
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
    #------------------------------------------------------------------------------
    # create_venue = CreateVenueMutation.Field()
    create_venue_internal = CreateVenueInternalMutation.Field()
    create_venue_external = CreateVenueExternalMutation.Field()

    
    #-------------------------------------------------------------------------------
    create_post = CreatePostMutation.Field()
    update_post = EditPostMutation.Field()
    delete_post = DeletePostMutation.Field()

    add_post_like = CreateAddPostLikeMutation.Field()
    delete_post_like = UpdatePostLikeMutation.Field()

    add_post_comment = PostCommentMutation.Field()
    update_post_comment = UpdatePostCommentMutation.Field()
    delete_post_comment = DeletePostCommentMutation.Field()
    add_post_comment_like  = CommentLikeMutation.Field()
    delete_post_comment_like = CommentUnLikeMutation.Field()

    add_post_save = SavePostMutation.Field()
    delete_post_save = UnSavePostMutation.Field()
    
    #-----------------------------------------------------------------------
    send_message = ChatSendMessageMutation.Field()
    shared_attachment = ChatSendMessageSharesMutation.Field()
    add_reaction_message = AddReactionMessageMutation.Field()
    delete_reaction_message = DeleteReactionMessageMutation.Field()
    delete_message = DeleteMessageMutation.Field()
    delete_thread = DeleteThreadMutation.Field()
    accept_chat_request = AcceptRequestChatThreadMutation.Field()
    decline_chat_request = DeclineRequestChatThreadMutation.Field()

    change_group_name = ChangeGroupNameMutation.Field()
    change_group_photo = ChangeGroupPhotoMutation.Field()

    add_chat_member = AddMemberGroupThreadMutation.Field()
    remove_chat_member = RemoveMemberGroupThreadMutation.Field()
    #----------------------------------------------------------------------
    add_payment = PaymentCardMutation.Field()

    #---------------------------------------------------------------
    create_itinerary = CreateItineraryMutation.Field()

    
    ##-------------------------------------------------
    pin_user_badges = PinBadgesMutation.Field()


    
