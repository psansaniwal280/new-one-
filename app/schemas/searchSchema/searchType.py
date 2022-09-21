import graphene
from app.schemas.commonObjects.objectTypes import PageInfoObject
from app.schemas.userSchema.userType import UserListType
from app.schemas.postSchema.postType import PostListType
from app.models import *
from django.db.models import Max, Avg

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
    rel_score = graphene.Float()


# class AllSearchSuggestionsType(graphene.ObjectType):
#     hashtags = graphene.List(SearchAllSuggestionsHashTagType)
#     venues = graphene.List(SearchAllSuggestionsVenueType)
#     users = graphene.List(SearchAllSuggestionsUsersType)

class SearchSuggestionsType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    rel_score = graphene.Float()
    type = graphene.String()

class AllSearchSuggestionsType(graphene.ObjectType):
    results = graphene.List(SearchSuggestionsType)
    page_info = graphene.Field(PageInfoObject)

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

    def resolve_rating(self, info):
        rating = Post.objects.using('default').filter(venue_id=self.venue_id).aggregate(Avg('user_rating'))['user_rating__avg']
        return rating if rating else 0

    def resolve_noOfRatings(self, info):
        return Post.objects.using('default').filter(venue_id=self.venue_id).count()


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
    page_info = graphene.Field(PageInfoObject)
    tags = graphene.List(SearchTagsValueType)


class SearchTagsValuePostListType(graphene.ObjectType):
    tag_id = graphene.Int()
    hashtag = graphene.String()
    posts = graphene.List(PostListType)
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
    # typeId = graphene.Int()
    # type = graphene.String()


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
    # is_post = graphene.Boolean()
    template = graphene.Field(SearchListTemplateType)
    # price = graphene.String()


class SearchAllExperienceListType(graphene.ObjectType):
    message = graphene.String()
    experiences = graphene.List(SearchListTemplateType)
    page_info = graphene.Field(PageInfoObject)


class AllSearchExperienceListType(graphene.ObjectType):
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


# ----------------------------------------------------------------------------------------------------------------------------
class SearchRecommendedListType(graphene.ObjectType):
    pass


class SearchUserListType(graphene.ObjectType):
    user_id = graphene.Int()
    relevancy_score = graphene.Float()


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


class SearchHistoryType(graphene.ObjectType):
    searchTerm = graphene.String()
    searchDate = graphene.DateTime()


class SearchRecommendedType(graphene.ObjectType):
    message = graphene.String()


class CountryObjectType(graphene.ObjectType):
    country_id = graphene.Int()
    country_name = graphene.String()
    country_code_two_char = graphene.String()
    country_code_three_char = graphene.String()


class StateObjectType(graphene.ObjectType):
    state_id = graphene.Int()
    state_name = graphene.String()
    state_code = graphene.String()
    country = graphene.Field(CountryObjectType)


class CityObjectType(graphene.ObjectType):
    city_id = graphene.Int()
    rel_score = graphene.Float()
    city_name = graphene.String()
    latitude = graphene.String()
    longitude = graphene.String()
    state = graphene.Field(StateObjectType)


class CityPageListType(graphene.ObjectType):
    cities = graphene.List(CityObjectType)
    page_info = graphene.Field(PageInfoObject)


class StatePageListType(graphene.ObjectType):
    states = graphene.List(StateObjectType)
    page_info = graphene.Field(PageInfoObject)


class CountryPageListType(graphene.ObjectType):
    countries = graphene.List(CountryObjectType)
    page_info = graphene.Field(PageInfoObject)


class SearchLocationObjectType(graphene.ObjectType):
    city = graphene.Field(CityPageListType)
    state = graphene.Field(StatePageListType)
    country = graphene.Field(CountryPageListType)

class SearchLocationObjectConcatType(graphene.ObjectType):
    cities = graphene.List(CityObjectType)
    states = graphene.List(StateObjectType)
    countries = graphene.List(CountryObjectType)
