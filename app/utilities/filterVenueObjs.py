import json

from django.db.models import Q

from . import Verification
from ..models import Amenity, VenueAmenity, Post, VenueCategory, VenueInternal, VenueExternal, VenueSubCategory, ExpVenueAvailability
import datetime


def filterStayVenueObjs(json_result, input_json_filter_content):
    print(json_result)
    json_result_ids = []

    # Filter by Type/ Unique stay_type
    filtered_venue_id_by_staytype = []
    if 'stay_type' in input_json_filter_content.keys() and input_json_filter_content['stay_type'] != []:
        result_stay_type = []
        stay_type_obj = []
        stay_type_array = input_json_filter_content['stay_type']
        stay_type_array += input_json_filter_content['unique_stay']

        stay_type_numbers = StayType.objects.filter(name__in=stay_type_array)
        for stay in stay_type_numbers:
            stay_type_obj += VenueStayType.objects.filter(stay_type_id=stay).values_list('venue_id')

        for a in range(len(stay_type_obj)):
            stay_type_obj[a] = stay_type_obj[a][0]

        for each in range(len(json_result)):
            if json_result[each]['venue']['venue_id'] in stay_type_obj:
                result_stay_type.append(json_result[each])
        json_result = result_stay_type

    # Filter by amenities
    filtered_venue_id_by_amenity = []
    if 'amenities' in input_json_filter_content.keys() and input_json_filter_content['amenities'] != []:
        result_amenities = []
        amenity_obj = []
        amenities_array = input_json_filter_content['amenities']
        amenity_ids = Amenity.objects.filter(name__in=amenities_array)

        for each_amenity_id in amenity_ids:
            amenity_obj += VenueAmenity.objects.filter(amenity_id=each_amenity_id).values_list('venue_id')

        for a in range(len(amenity_obj)):
            amenity_obj[a] = amenity_obj[a][0]
        print(amenity_obj)

        for each in range(len(json_result)):
            if json_result[each]['venue']['venue_id'] in amenity_obj:
                result_amenities.append(json_result[each])
        json_result = result_amenities

    # Filter by Pricing
    if 'max_price' in input_json_filter_content.keys() and 'min_price' in input_json_filter_content.keys():  # and input_json_filter_content['max_price'] != 0 and input_json_filter_content['min_price'] != 10000:
        result_pricing = []
        max_price = input_json_filter_content['max_price']
        min_price = input_json_filter_content['min_price']

        for k in range(len(json_result)):
            if json_result[k]['price'] is not None:

                if float(json_result[k]['price']) <= float(max_price) and float(json_result[k]['price']) >= float(
                        min_price):
                    result_pricing.append(json_result[k])

        json_result = result_pricing

    # Filter By Rating
    if 'rating' in input_json_filter_content.keys() and input_json_filter_content['rating'] != "any":
        result_rating = []
        rating_array = input_json_filter_content['rating']
        rating_array = rating_array.split('+')[0]
        for each in range(len(json_result)):
            if json_result[each]['user'] is not None:
                if float(json_result[each]['user']['rating']) >= float(rating_array):
                    result_rating.append(json_result[each])

        json_result = result_rating

    # Filter By No of Guests
    if 'noOfGuests' in input_json_filter_content.keys() and input_json_filter_content['noOfGuests'] != 0:
        result_guests = []
        for each in range(len(json_result)):
            guests = input_json_filter_content['noOfGuests']
            try:
                if VenueInternal.objects.get(venue_id=json_result[each]['venue']['venue_id']).max_guests >= guests:
                    result_guests.append(json_result[each])
            except:
                pass
            try:
                if VenueExternal.objects.get(venue_id=json_result[each]['venue']['venue_id']).max_guests >= guests:
                    result_guests.append(json_result[each])
            except:
                pass
        json_result = result_guests

    # Sort By
    sorted_venue_ids = []
    sorted_json_result = json_result
    if 'sort_by' in input_json_filter_content.keys() and input_json_filter_content['sort_by'] != "":

        sort_by = input_json_filter_content['sort_by']
        if sort_by == 'Price Low-High':
            sorted_json_result = sorted(json_result,
                                        key=lambda x: float('inf') if x['price'] is None else float(x['price']))
            # print(sorted_json_result)
        if sort_by == 'Price High-Low':
            sorted_json_result = sorted(json_result,
                                        key=lambda x: -1 * float('inf') if x['price'] is None else float(x['price']),
                                        reverse=True)
            # print(sorted_json_result)
        if sort_by == 'Most Popular':
            sorted_json_result = sorted(json_result, key=lambda x: Post.objects.get(
                venue_id=x['venue']['venue_id']).count() if not Post.DoesNotExist else 0)
            # print(sorted_json_result)
        """---------------------------------------------------------------------------------To Do----------------------------------------------------------------------------------------------"""
        if sort_by == 'Recommended':
            pass
        """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""

    return sorted_json_result


def filterExperienceVenueObjs(venue_type_id, json_result, input_json_filter_content, searchContent):
    # ---------------------Filter by Categories --------------------------------
    result_category = []
    if input_json_filter_content.get('categories') and len(input_json_filter_content.get('categories')) > 0:
        category_array = input_json_filter_content['categories']
        for c in category_array:
            Verification.category_verify(c)
        category_id_array = VenueCategory.objects.filter(Q(venue_category_id__in=category_array) | Q(venue_category_name__icontains=searchContent) | Q(venue_category_name__icontains=searchContent, venue_category_id__in=category_array)).values_list('venue_category_id', flat=True)
        category_objs = VenueSubCategory.objects.filter(Q(venue_category_id__in=list(category_id_array)) | Q(venue_subcategory_name__icontains=searchContent) | Q(venue_category_id__in=list(category_id_array), venue_subcategory_name__icontains=searchContent)).values_list('venue_category_id__venue_type_id', flat=True)
        venue_id_lists = list(set(list(VenueInternal.objects.using('default').filter(venue_type_id__in=category_objs).values_list('venue_id', flat=True))))

        for each in range(len(json_result)):
            if json_result[each]['venue']['venue_id'] in venue_id_lists:
                result_category.append(json_result[each])
        # if len(result_category) > 0:
        json_result = result_category
        print(json_result,"categories")
    else:
        category_id_array = VenueCategory.objects.filter(venue_category_name__icontains=searchContent).values_list('venue_category_id', flat=True)

        category_objs = VenueSubCategory.objects.filter(Q(venue_category_id__in=list(category_id_array)) | Q(venue_subcategory_name__icontains=searchContent) | Q(venue_category_id__in=list(category_id_array), venue_subcategory_name__icontains=searchContent)).values_list('venue_category_id__venue_type_id', flat=True)
        venue_id_lists = list(set(list(VenueInternal.objects.using('default').filter(venue_type_id__in=category_objs).values_list('venue_id', flat=True))))

        for each in range(len(json_result)):
            if json_result[each]['venue']['venue_id'] and json_result[each]['venue']['venue_id'] in venue_id_lists:
                result_category.append(json_result[each])
        if len(result_category) > 0:
            json_result = result_category
        print(json_result, "categories")

    # -------------------------filtering by max and min price ----------------
    result_pricing = []
    if isinstance(input_json_filter_content.get('max_price'), (int, str, float)) and isinstance(input_json_filter_content.get('min_price'), (int, str, float)):
        result_pricing = []
        max_price = float(input_json_filter_content['max_price'])
        min_price = float(input_json_filter_content['min_price'])

        for k in range(len(json_result)):
            if json_result[k]['price'] is not None:
                if float(json_result[k]['price']) and max_price >= float(json_result[k]['price']) >= min_price:
                    result_pricing.append(json_result[k])
        #
        # if len(result_pricing) > 0:
        json_result = result_pricing
        print(json_result, "max min price")

    # ------------------------------Filter By Rating ---------------------------------------------
    if isinstance(input_json_filter_content.get('rating'), (str, int, float)) and str(input_json_filter_content.get('rating')).strip() != "any":
        result_rating = []
        rating_array = input_json_filter_content['rating']
        if "+" in str(rating_array):
            rating_array = rating_array.split('+')[0]

        for each in range(len(json_result)):
            if json_result[each] is not None:
                if json_result[each].get('rating') and float(json_result[each]['rating']) >= float(rating_array):
                    result_rating.append(json_result[each])
        #
        # if len(result_rating) > 0:
        json_result = result_rating
        print(json_result, "rating")

    # -----------------Filter By No of Guests---------------------
    # if isinstance(input_json_filter_content.get('noOfGuests'), (str, int)) and int(input_json_filter_content.get('noOfGuests')) != 0:
    #     result_guests = []
    #     for each in range(len(json_result)):
    #         guests = int(input_json_filter_content['noOfGuests'])
    #         try:
    #             m_guest = VenueInternal.objects.get(venue_id=json_result[each]['venue']['venue_id'])
    #             if m_guest.max_guests <= guests:
    #                 result_guests.append(json_result[each])
    #         except Exception as e:
    #             print("noOfGuests", e)
    #             pass
    # try:
    #     if VenueExternal.objects.get(venue_id=json_result[each]['venue']['venue_id']).max_guests >= guests:
    #         result_guests.append(json_result[each])
    # except:
    #     pass
    # if len(result_category) > 0:
    # json_result = result_guests
    # print(json_result, "guests")

    # ---------------------------Sort By ---------------------------------------------

    sorted_json_result = json_result
    if input_json_filter_content.get('sort_by') and input_json_filter_content['sort_by'].strip():
        sort_by = input_json_filter_content.get('sort_by').strip().replace("  ", "").lower()
        if sort_by == 'price low-high':
            sorted_json_result = sorted(json_result,
                                        key=lambda x: float('inf') if x['price'] is None else float(x['price']))
            # print(sorted_json_result)
        if sort_by == 'price high-low':
            sorted_json_result = sorted(json_result,
                                        key=lambda x: -1 * float('inf') if x['price'] is None else float(x['price']),
                                        reverse=True)
            # print(sorted_json_result)
    #     if sort_by == 'most popular':
    #         sorted_json_result = sorted(json_result, key=lambda x: Post.objects.get(
    #             venue_id=x['venue']['venue_id']).count() if not Post.DoesNotExist else 0)
    #         # print(sorted_json_result)
    #     """---------------------------------------------------------------------------------To Do----------------------------------------------------------------------------------------------"""
    #     if sort_by == 'recommended':
    #         pass
    #     """------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""
    # print(sorted_json_result)
    # Filter by Time of Day
    # filtered_venue_id_by_time_of_day = []
    # if 'time_of_day' in input_json_filter_content.keys() and input_json_filter_content['time_of_day'] != []:
    #     result_time_of_day = []
    #     time_of_day_venue_objs = []
    #     time_of_day_array = input_json_filter_content['time_of_day']
    #     if 'Morning' in time_of_day_array:
    #         time_of_day_venue_objs += ExperienceVenueAvailability.objects.filter(
    #             start_time__range=[datetime.time(4, 0, 0), datetime.time(11, 58, 59)]).values_list(
    #             'venue_internal_id__venue_id')
    #     if 'Afternoon' in time_of_day_array:
    #         time_of_day_venue_objs += ExperienceVenueAvailability.objects.filter(
    #             start_time__range=[datetime.time(12, 1, 0), datetime.time(17, 59, 59)]).values_list(
    #             'venue_internal_id__venue_id')
    #     if 'Evening' in time_of_day_array:
    #         time_of_day_venue_objs += ExperienceVenueAvailability.objects.filter(
    #             start_time__range=[datetime.time(18, 0, 0), datetime.time(3, 59, 0)]).values_list(
    #             'venue_internal_id__venue_id')
    #     print(time_of_day_venue_objs)
    #     for a in range(len(time_of_day_venue_objs)):
    #         if time_of_day_venue_objs[a]:
    #             time_of_day_venue_objs[a] = time_of_day_venue_objs[a][0]
    #     # for a in range(len(time_of_day_venue_objs)):
    #     #     time_of_day_venue_objs[a]=time_of_day_venue_objs[a][0]
    #     for each in range(len(json_result)):
    #         if json_result[each]['venue']['venue_id'] in time_of_day_venue_objs:
    #             result_time_of_day.append(json_result[each])
    #     print(result_time_of_day)
    #     json_result = result_time_of_dayb

    return sorted_json_result


def filterTransportationVenueObjs(json_result, input_json_filter_content):
    # Filter by Vehicle Type
    filtered_venue_id_by_type = []
    if 'vehicle_type' in input_json_filter_content.keys() and input_json_filter_content['vehicle_type'] != []:
        result_vehicle_type = []
        vehicle_objs = []
        vehicle_name_array = input_json_filter_content['vehicle_type']
        vehicle_type_id_array = TransportationType.objects.filter(name__in=vehicle_name_array).values_list(
            'transportation_type_id')
        for vehicle in vehicle_type_id_array:
            vehicle_objs += (
                VenueTransportationType.objects.filter(transportation_type_id=vehicle[0]).values_list('venue_id'))

        for a in range(len(vehicle_objs)):
            vehicle_objs[a] = vehicle_objs[a][0]

        for each in range(len(json_result)):
            if json_result[each]['venue']['venue_id'] in vehicle_objs:
                result_vehicle_type.append(json_result[each])
        json_result = result_vehicle_type

    # Filter by Capacity
    if 'capacity' in input_json_filter_content.keys() and input_json_filter_content['capacity'] != 0:
        result_capacity = []
        guests = input_json_filter_content['capacity']
        for each in range(len(json_result)):
            print(json_result[each])
            try:
                if VenueInternal.objects.get(venue_id=json_result[each]['venue']['venue_id']).max_guests >= guests:
                    result_capacity.append(json_result[each])
            except:
                pass
            try:
                if VenueExternal.objects.get(venue_id=json_result[each]['venue']['venue_id']).max_guests >= guests:
                    result_capacity.append(json_result[each])
            except:
                pass
        json_result = result_capacity

    # Filter by Pricing
    if 'max_price' in input_json_filter_content.keys() and 'min_price' in input_json_filter_content.keys():
        result_pricing = []
        max_price = input_json_filter_content['max_price']
        min_price = input_json_filter_content['min_price']

        for k in range(len(json_result)):
            if json_result[k]['price'] is not None:
                if float(json_result[k]['price']) <= float(max_price) and float(json_result[k]['price']) >= float(
                        min_price):
                    result_pricing.append(json_result[k])

        json_result = result_pricing

    # Sort By
    sorted_venue_ids = []
    sorted_json_result = json_result
    if 'sort_by' in input_json_filter_content.keys():

        sort_by = input_json_filter_content['sort_by']
        if sort_by == 'Price Low-High':
            sorted_json_result = sorted(json_result,
                                        key=lambda x: float('inf') if x['price'] is None else float(x['price']))
            # print(sorted_json_result)
        if sort_by == 'Price High-Low':
            sorted_json_result = sorted(json_result,
                                        key=lambda x: -1 * float('inf') if x['price'] is None else float(x['price']),
                                        reverse=True)
            # print(sorted_json_result)
        if sort_by == 'Most Popular':
            sorted_json_result = sorted(json_result, key=lambda x: Post.objects.get(
                venue_id=x['venue']['venue_id']).count() if not Post.DoesNotExist else 0)
            # print(sorted_json_result)
        if sort_by == 'Recommended':
            pass

    return sorted_json_result
