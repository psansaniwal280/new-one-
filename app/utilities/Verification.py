import datetime
import json

from app.models import *
from app.utilities.errors import NotFoundException, BadRequestException
from app.utilities.redis import redis_connect, get_hashmap_from_cache, set_hashmap_to_cache


def user_verify(userId):
    if userId is not None:
        try:
            print(userId)
            user = User.objects.using('default').get(user_id=userId)
            print(user)
            if not user.is_active:
                raise BadRequestException("invalid request; userId provided is inactive", 400)
            else:
                return user
        except User.DoesNotExist:
            raise NotFoundException("userId provided not found", 404)
    else:
        raise BadRequestException("invalid request; userId provided is invalid", 400)


def user_profile(userId):
    if userId is not None:
        try:
            userProfile = UserProfile.objects.using('default').get(user_id=userId)
            return userProfile
        except User.DoesNotExist:
            raise NotFoundException("userId provided has not created a profile", 404)
    else:
        raise BadRequestException("invalid request; userId provided is invalid", 400)


def post_verify(postId):
    if postId is not None:
        try:
            post = Post.objects.using('default').get(post_id=postId)
            return post
        except Post.DoesNotExist:
            raise NotFoundException("postId provided not found", 404)
    else:
        raise BadRequestException("invalid request; postId provided is invalid", 400)


def venue_verify(venueId):
    if venueId is not None:
        try:
            venue = Venue.objects.using('default').get(venue_id=venueId)
            return venue
        except:
            raise NotFoundException("venueId provided not found")
    else:
        raise BadRequestException("invalid request; venueId provided is invalid")


def venue_internal_verify(venueInternalId):
    if venueInternalId is not None:
        try:
            venue_internal = VenueInternal.objects.using('default').get(venue_internal_id=venueInternalId)
            return venue_internal
        except:
            raise NotFoundException("venue internal Id provided not found")
    else:
        raise BadRequestException("invalid request; venue internal Id provided is invalid")


def venue_venue_internal_verify(venueId):
    if venueId is not None:
        try:
            venue = VenueInternal.objects.using('default').get(venue_id=venueId)
            return venue
        except:
            raise NotFoundException("venueId provided not found in venue internal")
    else:
        raise BadRequestException("invalid request; venueId provided is invalid")


def past_month_verify(month, year):
    curr_time = datetime.datetime.now()
    curr_date = curr_time.date()
    curr_day = curr_time.day
    curr_month = curr_time.month
    curr_year = curr_time.year
    if year > curr_year:
        pass
    elif year == curr_year:
        if month >= curr_month:
            pass
        else:
            raise BadRequestException("please enter current or future month")
    else:
        raise BadRequestException("please enter current or future month/year")


def past_date_verify(day, month, year):
    curr_time = datetime.datetime.now()
    curr_date = curr_time.date()
    verify_date = datetime.date(year, month, day)
    if verify_date >= curr_date:
        pass
    else:
        raise BadRequestException("please enter current or future date")


def city_verify(city_id):
    if city_id is not None:
        try:
            city = City.objects.using('default').get(city_id=city_id)
            return city
        except City.DoesNOtExist():
            raise NotFoundException("cityId provided not found")
    else:
        raise BadRequestException("invalid request; city provided is invalid")


def state_verify(state_id):
    if state_id is not None:
        try:
            state= States.objects.using('default').get(state_id=state_id)
            return state
        except States.DoesNOtExist():
            raise NotFoundException("State Id provided not found")
    else:
        raise BadRequestException("invalid request; state provided is invalid")


def country_verify(country_id):
    if country_id is not None:
        try:
            country = Country.objects.using('default').get(country_id=country_id)
            return country
        except States.DoesNOtExist():
            raise NotFoundException("country Id provided not found")
    else:
        raise BadRequestException("invalid request; country provided is invalid")


def zip_verify(zip_code_id):
    if zip_code_id is not None:
        try:
            zip_code = ZipCode.objects.using('default').get(zip_code_id=zip_code_id)
            return zip_code
        except ZipCode.DoesNOtExist():
            raise NotFoundException("zip_code Id provided not found")
    else:
        raise BadRequestException("invalid request; zip_code provided is invalid")


def category_verify(venue_category_id):
    if venue_category_id is not None:
        try:
            venue_category = VenueCategory.objects.using('default').get(venue_category_id=venue_category_id)
            return venue_category
        except:
            raise NotFoundException("categoryId provided not found")
    else:
        raise BadRequestException("invalid request; categoryId provided is invalid")


def post_comment_verify(postCommentId):
    if postCommentId is not None:
        try:
            reply = PostComment.objects.using('default').get(post_comment_id=postCommentId)
            return reply
        except PostComment.DoesNotExist:
            raise NotFoundException("Unable to reply to non existing comment", 404)
    else:
        raise BadRequestException("invalid request; postcommentId provided is invalid", 400)


def searchContent_verify(search_content):
    if search_content and search_content.strip() is not None:
        return search_content
    else:
        raise BadRequestException("invalid request; searchContent provided is invalid", 400)


def searchContent_verify_redis_delete_term(search_content, uid):
    if search_content and search_content.strip():
        client = redis_connect()
        search_history_cache = get_hashmap_from_cache(client, str(uid) + "_search_history")
        if search_history_cache is not None:
            user_search_history = json.loads(search_history_cache)
            if search_content.strip() in list(user_search_history.values()):
                ind = list(user_search_history.values()).index(search_content.strip())
                date_time = list(user_search_history.keys())[ind]
                del user_search_history[date_time]
                state = set_hashmap_to_cache(client, str(uid) + "_search_history", json.dumps(user_search_history))
                return True
            else:
                return False
        else:
            return False
    else:
        raise BadRequestException("invalid request; searchContent provided is empty", 400)


def searchContent_verify_redis_add_update_term(search_content, uid):
    if search_content and search_content.strip():
        client = redis_connect()
        search_history_cache = get_hashmap_from_cache(client, str(uid) + "_search_history")
        user_search_history = {}
        if search_history_cache:
            user_search_history = json.loads(search_history_cache)
            if search_content.strip() in list(user_search_history.values()):
                ind = list(user_search_history.values()).index(search_content.strip())
                date_time = list(user_search_history.keys())[ind]
                del user_search_history[date_time]
            else:
                user_search_history[datetime.datetime.now().timestamp()] = search_content.strip()
                state = set_hashmap_to_cache(client, str(uid) + "_search_history", json.dumps(user_search_history))
                return state
        user_search_history[datetime.datetime.now().timestamp()] = search_content.strip()
        state = set_hashmap_to_cache(client, str(uid) + "_search_history", json.dumps(user_search_history))
        return state

    else:
        raise BadRequestException("invalid request; searchContent provided is empty", 400)


def expVenueOption_verify(VenueOptionId):
    if VenueOptionId is not None:
        try:
            venueOption = ExpVenueOption.objects.using('default').get(exp_venue_option_id=VenueOptionId)
            return venueOption
        except ExpVenueOption.DoesNotExist:
            raise NotFoundException("venueExperienceBookingOptionId provided not found")
    else:
        raise BadRequestException("invalid request; venueExperienceBookingOptionId provided is invalid")


def exp_availability_timeslot_checker(venueInternalId):
    print(venueInternalId)
    ExpAvailabilities = ExpVenueAvailability.objects.using("default").filter(venue_internal_id=venueInternalId)
    if len(ExpAvailabilities) == 0:
        raise BadRequestException("Error in request. This venue option has no availability information provided.")
    ExpAvailabilities_list = ExpVenueAvailability.objects.using("default").filter(venue_internal_id=venueInternalId).values_list('exp_venue_availability_id', flat=True)
    expVenueTimeslots = ExpVenueAvailabilityTimeslot.objects.using("default").filter(exp_venue_availability_id__in=ExpAvailabilities_list)
    if len(expVenueTimeslots) == 0:
        raise BadRequestException('Error in request. This venue option has no timeslots provided.')


def exp_venue_timeslot(timeslot_id):
    if timeslot_id is not None:
        try:
            timeslot = ExpVenueAvailabilityTimeslot.objects.using('default').get(exp_venue_availability_timeslot_id=timeslot_id)
            return timeslot
        except ExpVenueAvailabilityTimeslot.DoesNotExist:
            raise NotFoundException("timeslot provided not found")
    else:
        raise BadRequestException("invalid request; time slot provided is invalid")


def address_verify(billing_address_id,user_id):
    if billing_address_id is not None:
        try:
            billing_address = BillingAddress.objects.using('payments').get(billing_address_id=billing_address_id,user_id=user_id)
            return billing_address
        except BillingAddress.DoesNotExist:
            raise NotFoundException("BillingAddress provided not found")
    else:
        raise BadRequestException("invalid request; BillingAddress provided is invalid")


def single_address_default(userId):
    if userId is not None:
        if BillingAddress.objects.using('payments').filter(user_id=userId).count() > 0:
            try:
                billing_address = BillingAddress.objects.using('payments').get(user_id=userId, default_source=True)
                return billing_address
            except BillingAddress.DoesNotExist:
                raise NotFoundException("Either there is no billing address set as default or more than one address set as default")
    else:
        raise BadRequestException("invalid request; userId provided is invalid")


def country_state_city_relation(countryId, stateId, cityId):
    try:
        city = City.objects.get(city_id=cityId, state_id=stateId, state_id__country_id=countryId)
        return city
    except City.DoesNotExist:
        raise NotFoundException('Not found any relation between city, state, country')


