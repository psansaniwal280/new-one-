import graphene
from .venueType import *
from app.models import *
from app.utilities.errors import *
from django.db.models import Max, Avg
import datetime
from django.db.models import Q
from app.schemas.commonObjects.objectTypes import *
import pytz

from ...utilities import Verification, CommonOperations
from ...utilities.filterDateVenueObjs import dates_between, calculate_alldays, month_days_between, calculateExpVenueAvailability, calendar_dict, bookingStatusCheck


class Query(graphene.ObjectType):
    # Get Venue Object by Venue Id
    venue = graphene.Field(ViewVenueObjectType, venueId=graphene.Int(), userId=graphene.Int(), postId=graphene.Int())

    # Get Venue Rating by Venue Id
    venueRating = graphene.Field(VenueRatingObjectType, venueId=graphene.Int())

     #Get Available Dates of a Venue
    venueAvailableDates = graphene.Field(VenueAvailableDatesObjectType, venueId = graphene.Int(), userId = graphene.Int(),month=graphene.Int(),year=graphene.Int(),noOfPeople=graphene.Int())

    # Get Available timeslots for a venue
    # bookingOptionTimeslots = graphene.Field(VenueAvailableTimeSlotsObjectType, userId=graphene.Int(), venueBookingOptionId=graphene.Int(), dateOfBooking=graphene.String(), noOfPeople=graphene.Int())

    # Get Booking Options for that particular date
    venueBookingOptions = graphene.Field(VenueBookingOptionsIdsType, userId=graphene.Int(), venueId=graphene.Int(), date=graphene.String())  # '''dateIds = graphene.List(graphene.Int)'''

    # Get Booking Option with Venue Booking Option Id
    venueBookingOption = graphene.Field(VenueBookingOptionObjectType, userId=graphene.Int(), venueBookingOptionId=graphene.Int(), dateOfBooking=graphene.String(), noOfPeople=graphene.Int())

    # Get all venue categories list
    experienceCategories = graphene.Field(ExperienceCategoriesList)

    # Get Venue by venueId
    def resolve_venue(self, info, **kwargs):
        venueId = kwargs.get('venueId')
        postId = kwargs.get('postId')
        userId = kwargs.get('userId')
        Verification.user_verify(userId)
        Verification.venue_verify(venueId)
        venue = Venue.objects.using('default').get(venue_id=venueId)
        if venue.is_external:
            pass
        else:
            post = CommonOperations.default_get_or_none(Post, post_id=postId) if postId is not None else None
            shared_by = VenueUserObjectType(post.user_id) if post is not None else None
            venueInternal = VenueInternal.objects.using('default').get(venue_id=venue.venue_id)
            venue_type = VenueType.objects.using("default").get(venue_type_name='Experiences')
            if venueInternal.venue_type_id == venue_type.venue_type_id:
                featuredVideo = FeaturedVideoObjectType(url=venueInternal.featured_video if venueInternal.featured_video else None)
                title = venueInternal.venue_internal_name
                address = Address.objects.using('default').get(address_id=venueInternal.address_id)
                zip = ZipCode.objects.using('default').get(zip_code_id=address.zip_code_id)
                city = City.objects.using('default').get(city_id=zip.city_id)
                state = States.objects.using('default').get(state_id=city.state_id)
                country = Country.objects.using('default').get(country_id=state.country_id)
                location = LocationObjectType(
                    city=city.city_name,
                    state=state.state_name,
                    country=country.country_name,
                    latitude=city.latitude,
                    longitude=city.longitude
                )
                shortDescription = venueInternal.venue_internal_description
                venue_language = CommonOperations.default_get_or_none(VenueLanguages, venue_internal_id=venueInternal.venue_internal_id)
                language = Languages.objects.using('default').get(language_id=venue_language.language_id).language_name if venue_language else None

                whatToBring = WhatToBring.objects.using('default').filter(venue_internal_id=venueInternal.venue_internal_id).values('what_to_bring_name')
                whatToBringOutputObj = [item.get('what_to_bring_name') for item in whatToBring] if len(whatToBring) > 0 else None

                whatWeProvideOutputObj = {}
                whatWeProvide = WhatWeProvide.objects.using('default').filter(venue_internal_id=venueInternal.venue_internal_id).values('what_we_provide_option_id')
                if len(whatWeProvide) > 0:
                    for item in whatWeProvide:
                        whatWeProvideOption = WhatWeProvideOption.objects.using('default').get(
                            what_we_provide_option_id=item.get('what_we_provide_option_id'))
                        whatWeProvideCategory = WhatWeProvideCategory.objects.using('default').get(what_we_provide_category_id=
                                                                                                   whatWeProvideOption.what_we_provide_category_id)
                        if whatWeProvideCategory.what_we_provide_category_name not in whatWeProvideOutputObj:
                            whatWeProvideOutputObj[whatWeProvideCategory.what_we_provide_category_name] = [whatWeProvideOption.what_we_provide_option_name]
                        else:
                            whatWeProvideOutputObj[whatWeProvideCategory.what_we_provide_category_name].append(whatWeProvideOption.what_we_provide_option_name)

                accessRestrictions = CommonOperations.default_get_or_none(AccessRestriction, access_restriction_id=venueInternal.access_restriction_id) if venueInternal.access_restriction_id else None
                accessRestrictionsOutputObj = accessRestrictionObjectType(name=accessRestrictions.access_restriction_name, short_description=accessRestrictions.access_restriction_description) if accessRestrictions is not None else {}

                cancellationPolicy = CommonOperations.default_get_or_none(CancellationPolicy, cancellation_policy_id=venueInternal.cancellation_policy_id) if venueInternal.cancellation_policy_id else None
                cancellationPolicyOutputObj = cancellationObjectType(name=cancellationPolicy.cancellation_policy_name, short_description=cancellationPolicy.cancellation_policy_description) if cancellationPolicy is not None else {}

                venueMedias = VenueMedia.objects.using('default').filter(venue_internal_id=venueInternal.venue_internal_id).values('venue_media_id',
                                                                                                                                   'media_venue_url', 'media_venue_type_id')
                media = []
                for venueMedia in venueMedias:
                    media_venue_type = MediaVenueType.objects.using('default').get(media_venue_type_id=venueMedia.get('media_venue_type_id'))
                    media.append(MediaObjectType(id=venueMedia.get('venue_media_id'),
                                                 url=venueMedia.get('media_venue_url'),
                                                 type=MediaTypeObject(
                                                     type_id=media_venue_type.media_venue_type_id,
                                                     type_name=media_venue_type.media_venue_type_name)))

                vendorVenue = VendorVenue.objects.using('default').get(venue_id=venue.venue_id)
                venueObj = ViewVenueObjectType(venue_id=venueId,
                                               venue_type=venue_type.venue_type_name,
                                               language=language,
                                               featured_video=featuredVideo,
                                               what_to_bring=whatToBringOutputObj,
                                               what_we_provide=whatWeProvideOutputObj,
                                               access_restrictions=accessRestrictionsOutputObj,
                                               cancellation_policy=cancellationPolicyOutputObj,
                                               title=title,
                                               location=location,  # Database Location Object
                                               shared_by=shared_by,
                                               short_description=shortDescription,
                                               gallery=media,  # Media Object with {'id', 'url'}
                                               vendor_venue_id=vendorVenue.vendor_venue_id,  # vendorVenue.vendor.name, vendorVenue.vendor.avatar, vendorVenue.vendor.bio_url, vendorVenue.vendor.short_description, vendorRating, venueRatingCount)   #Database Vendor Object
                                               vendor_id=vendorVenue.vendor_id)
                return venueObj
        return None

    # Get Number of Ratings and Aggregate Rating
    def resolve_venueRating(self, info, **kwargs):
        venueId = kwargs.get('venueId')
        Verification.venue_verify(venueId)
        venue = Venue.objects.using('default').get(venue_id=venueId)
        venueRating = Post.objects.using('default').filter(venue_id=venueId).aggregate(Avg('user_rating'))['user_rating__avg']
        venueRatingCount = Post.objects.using('default').filter(venue_id=venueId).count()
        return VenueRatingObjectType(venue_rating=venueRating, venue_rating_aggregate=aggregateObjectType(aggregate=aggregate(count=venueRatingCount)))


    # Get Available Date for one venue
    def resolve_venueAvailableDates(self, info, **kwargs):
        venueId = kwargs.get('venueId')
        userId = kwargs.get('userId')
        month = kwargs.get('month')
        year = kwargs.get('year')
        noOfPeople = kwargs.get('noOfPeople')
        if noOfPeople is None or (noOfPeople < 0 or noOfPeople == 0):
            raise BadRequestException("Invalid number of people, number of people should be equal to or more than 1")

        venue_ch = Verification.venue_verify(venueId)
        Verification.user_verify(userId)
        if year is None:
            year = datetime.date.year
        if month is None:
            month = datetime.date.month
        Verification.past_month_verify(month, year)

        if venue_ch.is_external:
            # Not done logic for external
            pass
        else:
            venueInternal = Verification.venue_venue_internal_verify(venue_ch.venue_id)
            v_id = venueInternal.venue_internal_id
            Verification.exp_availability_timeslot_checker(v_id)
            if venueInternal.venue_type_id == 1:
                venue = Verification.venue_venue_internal_verify(venue_ch.venue_id)
                start_date = datetime.datetime(year, month, 1)
                nxt_mnth = start_date.replace(day=28) + datetime.timedelta(days=4)
                res = nxt_mnth - datetime.timedelta(days=nxt_mnth.day)
                end_date = res

                cal_dict = calendar_dict(calculate_alldays(month,year))

                blackoutAvailabilityIds = BlackoutDate.objects.filter(exp_venue_availability_id__venue_internal_id__venue_id=venueId)
                blackout_dates = []

                for i in blackoutAvailabilityIds:
                    if i.blackout_date_start_date.month == month and i.blackout_date_end_date.month == month:  # --calculate the Bo dates between the start and end date if both dates months is same to the input months
                        blackout_dates.extend(dates_between(str(i.blackout_date_start_date.strftime("%Y-%m-%d")), str(i.blackout_date_end_date.strftime("%Y-%m-%d"))))
                    elif i.blackout_date_start_date.month == month and i.blackout_date_end_date.month != month:  # --calulate the Bo dates between the start and end date of the input month as if end date of the blackout dates is come in next month
                        blackout_dates.extend(dates_between(str(i.blackout_date_start_date.strftime("%Y-%m-%d")), str(end_date.strftime("%Y-%m-%d"))))
                    elif i.blackout_date_start_date.month != month and i.blackout_date_end_date.month == month:
                        blackout_dates.extend(dates_between(str(start_date.strftime("%Y-%m-%d")), str(i.blackout_date_end_date.strftime("%Y-%m-%d"))))
                blackout_dates = list(set(blackout_dates))

                #  -------- fetching the availability id, their recurring value , start date and end date using the venue internal id
                ExpAvailabilities = ExpVenueAvailability.objects.using("default").filter(venue_internal_id=venueInternal.venue_internal_id)
                avb_dict = calculateExpVenueAvailability(ExpAvailabilities, cal_dict)

                bookingPurchases = BookingPurchase.objects.using("default").filter(exp_venue_availability_timeslot_id__exp_venue_availability_id__venue_internal_id =venueInternal.venue_internal_id)

                avb_book_dict = bookingStatusCheck(bookingPurchases,avb_dict)
                available = []
                for avb, avb_obj in avb_book_dict.items():
                    for mon, mon_obj in avb_obj.items():
                        for day, day_obj in mon_obj.items():
                            for dte, dte_obj in day_obj.items():
                                for tme, capacity in dte_obj.items():
                                    if capacity >= noOfPeople and mon == month:
                                        available.append(dte)

                if len(available) > 0:
                    available = list(set(available))
                    if len(blackout_dates) > 0:
                        for dte in blackout_dates:
                            if dte in available:
                                available.remove(dte)
                    return {"dates": sorted(available)}

            return {"dates": []}

    # Get Venue Booking Options Id List for a particular date
    def resolve_venueBookingOptions(self, info, **kwargs):
        userId = kwargs.get('userId')
        venueId = kwargs.get('venueId')
        date_book = kwargs.get('date')
        if date_book is None:
            raise BadRequestException("Invalid date, please enter a date")
        date_of_book = datetime.date(int(date_book.split('-')[0]), int(date_book.split('-')[1]), int(date_book.split('-')[2]))
        Verification.past_date_verify(date_of_book.day,date_of_book.month,date_of_book.year)
        Verification.user_verify(userId)
        Verification.venue_verify(venueId)
        venue = Venue.objects.using('default').get(venue_id=venueId)
        if venue.is_external:
            pass
        else:
            Verification.venue_venue_internal_verify(venueId)
            venueInternal = VenueInternal.objects.using('default').get(venue_id=venue.venue_id)
            Verification.exp_availability_timeslot_checker(venueInternal.venue_internal_id)
            cal_dict = calendar_dict([date_book])
            expVenueAvailabilities = ExpVenueAvailability.objects.using("default").filter(venue_internal=venueInternal.venue_internal_id)
            avb_dict = calculateExpVenueAvailability(expVenueAvailabilities, cal_dict,date_book)
            bookingPurchases = BookingPurchase.objects.using('default').filter(exp_venue_availability_timeslot_id__exp_venue_availability_id__venue_internal_id=venueInternal.venue_internal_id)
            book_dict = bookingStatusCheck(bookingPurchases, avb_dict)

            bookingOptions = ExpVenueOption.objects.using('default').filter(venue_internal_id=venueInternal.venue_internal_id)
            print("booking option",bookingOptions)

            available_booking_options = []
            for bookingOption in bookingOptions:
                for avb, avb_obj in book_dict.items():
                    for mon, mon_obj in avb_obj.items():
                        for day, day_obj in mon_obj.items():
                            for dte, dte_obj in day_obj.items():
                                for tme, capacity in dte_obj.items():
                                    if capacity >= bookingOption.per_group and bookingOption.exp_venue_option_id not in available_booking_options:
                                        available_booking_options.append(bookingOption.exp_venue_option_id)

            return VenueBookingOptionsIdsType(Ids=available_booking_options)
        return []

    # Get Booking Option
    # def resolve_venueBookingOption(self, info, **kwargs):
    #     userId = kwargs.get('userId')
    #     Verification.user_verify(userId)
    #     venueBookingOptionId = kwargs.get('venueBookingOptionId')
    #     Verification.expVenueOption_verify(venueBookingOptionId)
    #     venueOption = ExpVenueOption.objects.using('default').get(exp_venue_option_id=venueBookingOptionId)
    #     print(venueOption)
    #     Verification.exp_availability_timeslot_checker(venueOption.venue_internal_id)
    #     venuePrice = ExpVenueOptionPrice.objects.get(exp_venue_option_id=venueOption.exp_venue_option_id)
    #
    #     result = {
    #         "venue_experience_booking_option_id": venueOption.exp_venue_option_id,
    #         "option_name": venueOption.exp_venue_option_name,
    #         "price": venuePrice.venue_base_price,
    #         "guests_limit": venueOption.per_group,
    #         "short_description": venueOption.exp_venue_option_description,
    #
    #     }
    #
    #     return result

    # ---------- fetching all the categories -------------
    def resolve_experienceCategories(self, info, **kwargs):
        venue_type = VenueType.objects.using("default").get(venue_type_id=1)
        venueCategories = VenueCategory.objects.using("default").filter(venue_type_id = venue_type.venue_type_id)
        result = []
        for i in venueCategories:
            result.append(ExperienceCategory(id=i.venue_category_id, name=i.venue_category_name))
        return ExperienceCategoriesList(
            categories=result
        )

    def resolve_venueBookingOption(self, info, **kwargs):
        userId = kwargs.get('userId')
        Verification.user_verify(userId)
        venueBookingOptionId = kwargs.get('venueBookingOptionId')
        date_of_booking = kwargs.get('dateOfBooking')
        noOfPeople = kwargs.get('noOfPeople')
        if noOfPeople is None or (noOfPeople < 0 or noOfPeople == 0):
            raise BadRequestException("Invalid number of people, number of people should be equal to or more than 1")
        if date_of_booking is None:
            raise BadRequestException("Invalid date, please enter a date")
        date_of_book = datetime.date(int(date_of_booking.split('-')[0]), int(date_of_booking.split('-')[1]), int(date_of_booking.split('-')[2]))
        Verification.past_date_verify(date_of_book.day,date_of_book.month,date_of_book.year)

        Verification.expVenueOption_verify(venueBookingOptionId)
        expVenueOption = ExpVenueOption.objects.using("default").get(exp_venue_option_id=venueBookingOptionId)
        Verification.exp_availability_timeslot_checker(expVenueOption.venue_internal_id)
        cal_dict = calendar_dict([date_of_booking])

        expVenueAvailabilities = ExpVenueAvailability.objects.using("default").filter(venue_internal=expVenueOption.venue_internal_id)
        avb_dict = calculateExpVenueAvailability(expVenueAvailabilities,cal_dict,date_of_booking)
        print(avb_dict)
        bookingPurchases = BookingPurchase.objects.using('default').filter(exp_venue_availability_timeslot_id__exp_venue_availability_id__venue_internal_id=expVenueOption.venue_internal_id)
        book_dict = bookingStatusCheck(bookingPurchases,avb_dict)
        available_time_slot = []

        flag = 0
        for avb, avb_obj in book_dict.items():
            for mon, mon_obj in avb_obj.items():
                for day, day_obj in mon_obj.items():
                    for dte, dte_obj in day_obj.items():
                        for tme, capacity in dte_obj.items():
                            if capacity >= noOfPeople and flag != tme:
                                exp_time = ExpVenueAvailabilityTimeslot.objects.using('default').get(exp_venue_availability_timeslot_id = tme)
                                available_time_slot.append(TimeslotObjectType(start_time=exp_time.start_time, end_time=exp_time.end_time, remaining_capacity=capacity, timeslot_id=tme))
                                flag = tme

        venuePrice = ExpVenueOptionPrice.objects.get(exp_venue_option_id=expVenueOption.exp_venue_option_id)
        return VenueBookingOptionObjectType(venue_experience_booking_option_id= expVenueOption.exp_venue_option_id,
                                            option_name= expVenueOption.exp_venue_option_name,
                                            price= venuePrice.venue_base_price,
                                            guests_limit= expVenueOption.per_group,
                                            short_description= expVenueOption.exp_venue_option_description,
                                            timeslots=available_time_slot)

