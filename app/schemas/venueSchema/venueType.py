import graphene
from app.models import *
from graphene_django import DjangoObjectType
from app.schemas.commonObjects.objectTypes import *
from app.schemas.searchSchema.searchType import LocationObjectType
from django.db.models import Q
from graphene import Scalar


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
            venue = Venue.objects.using('default').get(pk=result_venue.venue_id)
            price = VenuePrice.objects.using('default').get(pk=venue.venue_id).venue_base_price

            return str(price)

    def resolve_venue_location(self, info):
        if self.is_external:
            obj = VenueExternal.objects.using('default').get(pk=self.venue_id)
            location = Location.objects.using('default').get(pk=obj.location_id)
            return str(location.city)
        else:
            obj = VenueInternal.objects.using('default').get(pk=self.venue_id)
            location = Location.objects.using('default').get(pk=obj.location_id)
            return str(location.city)

    def resolve_venue_name(self, info):
        if self.is_external:
            obj = VenueExternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.venue_external_name)
        else:
            obj = VenueInternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.venue_internal_name)

    def resolve_venue_type(self, info):
        if self.is_external:
            obj = VenueExternal.objects.using('default').get(pk=self.venue_id)
            venue_type_obj = VenueType.objects.using('default').get(pk=obj.venue_type_id)
            return venue_type_obj.venue_type_name
        else:
            obj = VenueInternal.objects.using('default').get(pk=self.venue_id)
            venue_type_obj = VenueType.objects.using('default').get(pk=obj.venue_type_id)
            return venue_type_obj.venue_type_name


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


class VenueUserObjectType(graphene.ObjectType):
    user_id = graphene.Int()
    # username = graphene.String()
    # avatar = graphene.String()
    # level = graphene.Int()
    # phone_number = graphene.Field(BigInt)
    # rating = graphene.Float()


class FeaturedVideoObjectType(graphene.ObjectType):
    url = graphene.String()


class VenueRatingObjectType(graphene.ObjectType):
    venue_rating = graphene.Float()
    venue_rating_aggregate = graphene.Field(aggregateObjectType)


class whatToBringObjectType(graphene.ObjectType):
    name = graphene.String()
    short_description = graphene.String()


class whatWeProvideObjectType(graphene.ObjectType):
    name = graphene.String()
    short_description = graphene.String()


class accessRestrictionObjectType(graphene.ObjectType):
    name = graphene.String()
    short_description = graphene.String()


class cancellationObjectType(graphene.ObjectType):
    name = graphene.String()
    short_description = graphene.String()


class Any(Scalar):
    @staticmethod
    def serialize(dt):
        return dt


class ViewVenueObjectType(graphene.ObjectType):
    venue_id = graphene.String()
    venue_type = graphene.String()
    language = graphene.String()
    featured_video = graphene.Field(FeaturedVideoObjectType)
    what_to_bring = graphene.List(graphene.String)
    what_we_provide = graphene.Field(Any)
    access_restrictions = graphene.Field(accessRestrictionObjectType)
    cancellation_policy = graphene.Field(cancellationObjectType)
    title = graphene.String()
    location = graphene.Field(LocationObjectType)
    # price = graphene.Float()
    # price_with_tax = graphene.Float()
    # rating = graphene.Float()
    # no_of_ratings = graphene.Int()
    # is_refundable = graphene.Boolean()
    shared_by = graphene.Field(VenueUserObjectType)
    short_description = graphene.String()
    gallery = graphene.List(MediaObjectType)
    vendor_venue_id = graphene.Int()
    vendor_id = graphene.Int()


class DurationUnitType(graphene.ObjectType):
    value = graphene.Int()
    unit = graphene.String()


# class VenueBookingOptionObjectType(graphene.ObjectType):
      # start_date = graphene.Date()
      # end_date = graphene.Date()
      # start_time = graphene.Time()
      # end_time = graphene.Time()
      # duration = graphene.Field(DurationUnitType)

#     venue_experience_booking_option_id = graphene.Int()
#     option_name = graphene.String()
#     price = graphene.Float()
#     guests_limit = graphene.Int()
#     short_description = graphene.String()

class DescriptionObjectType(graphene.ObjectType):
    content = graphene.String()
    hashtags = graphene.List(hashtagSection)
    mentions = graphene.List(mentionSection)


class VenueBookingOptionsIdsType(graphene.ObjectType):
    Ids = graphene.List(graphene.Int)


class TimeslotObjectType(graphene.ObjectType):
    timeslot_id = graphene.Int()
    start_time = graphene.Time()
    end_time = graphene.Time()
    remaining_capacity = graphene.Int()


class VenueBookingOptionObjectType(graphene.ObjectType):
    timeslots = graphene.List(TimeslotObjectType)
    venue_experience_booking_option_id = graphene.Int()
    option_name = graphene.String()
    price = graphene.Float()
    guests_limit = graphene.Int()
    short_description = graphene.String()


# class TagObjectType(DjangoObjectType):
#     class Meta:
#         model = Tag
#     tag_id = graphene.Int()
#     name = graphene.String()

#     # def resolve_hashtag(self, info):
#     #     return self.name


# class VenueAvailabilityObjectType(graphene.ObjectType):
#     date = graphene.DateTime()
#     booking_options = graphene.List(VenueBookingOptionObjectType)

class VenueAvailableDatesObjectType(graphene.ObjectType):
    # ids = graphene.List(graphene.Int)
    dates = graphene.List(graphene.String)


class ExperienceCategory(graphene.ObjectType):
    name = graphene.String()
    id = graphene.Int()


class ExperienceCategoriesList(graphene.ObjectType):
    categories = graphene.List(ExperienceCategory)
