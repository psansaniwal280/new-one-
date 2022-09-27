from . import Verification
from ..models import *
from django.db.models import Count, Sum
from datetime import datetime, date, time, timezone, timedelta
import datetime
from django.db.models import Q


def getDateFilteredVenueObjects(dates_in_the_range, venue_type, searchCheckInDate, searchCheckOutDate, noOfPeople, venueIds):
    start_date = date(int(searchCheckInDate.split('-')[0]), int(searchCheckInDate.split('-')[1]), int(searchCheckInDate.split('-')[2]))
    curr_time = datetime.datetime.now()
    if searchCheckInDate and searchCheckInDate.strip() and searchCheckOutDate and searchCheckOutDate.strip():
        end_date = date(int(searchCheckOutDate.split('-')[0]), int(searchCheckOutDate.split('-')[1]), int(searchCheckOutDate.split('-')[2]))
        Verification.past_date_verify(end_date.day, end_date.month, end_date.year)
        blackoutAvailabilityIds = BlackoutDate.objects.filter(blackout_date_start_date=dates_in_the_range[0], blackout_date_end_date=dates_in_the_range[-1]).values_list('exp_venue_availability_id', flat=True)
        # ExpAvailabilityVenueIds = ExpVenueAvailability.objects.filter(Q(start_date__in=dates_in_the_range, end_date__in=dates_in_the_range, venue_internal_id__venue_type_id=venue_type) |
        #                                                               Q(start_date__in=dates_in_the_range, venue_internal_id__venue_type_id=venue_type) |
        #                                                               Q(end_date__in=dates_in_the_range, venue_internal_id__venue_type_id=venue_type)).values_list('venue_internal_id__venue_id', flat=True).exclude(exp_venue_availability_id__in=list(blackoutAvailabilityIds))
        # ExpAvailabilities = ExpVenueAvailability.objects.filter(Q(start_date__in=dates_in_the_range, end_date__in=dates_in_the_range, venue_internal_id__venue_type_id=venue_type) |
        #                                                         Q(start_date__in=dates_in_the_range, venue_internal_id__venue_type_id=venue_type) |
        #                                                         Q(end_date__in=dates_in_the_range, venue_internal_id__venue_type_id=venue_type)).exclude(exp_venue_availability_id__in=list(blackoutAvailabilityIds))
        ExpAvailabilityVenueIds = ExpVenueAvailability.objects.filter(venue_internal_id__venue_id__in = venueIds).values_list('venue_internal_id__venue_id', flat=True).exclude(exp_venue_availability_id__in=list(blackoutAvailabilityIds))
        ExpAvailabilities = ExpVenueAvailability.objects.filter(venue_internal_id__venue_id__in = venueIds).exclude(exp_venue_availability_id__in=list(blackoutAvailabilityIds))

        cal_dict = calendar_dict(dates_in_the_range)

        # ----- fetching whether the user input start and end month of the dates has some events or not, as what is the start date of recurring event is not in date range but the month is

        # month_range = month_days_between(start_date.month, end_date.month)
        # ExpAvailabilityPatternVenueIds_month = ExpVenuePattern.objects.using('default').filter(month_of_year__in=month_range).values_list('exp_venue_availability__venue_internal_id__venue_id', flat=True)
        # ExpAvailabilitiesPattern_month = ExpVenuePattern.objects.using('default').filter(month_of_year__in=month_range)

    elif searchCheckInDate and searchCheckInDate.strip() and searchCheckOutDate is None:
        Verification.past_date_verify(start_date.day, start_date.month, start_date.year)
        blackoutAvailabilityIds = BlackoutDate.objects.filter(blackout_date_start_date=dates_in_the_range[0]).values_list('exp_venue_availability_id', flat=True)
        # ExpAvailabilityVenueIds = ExpVenueAvailability.objects.filter(start_date__in=dates_in_the_range, venue_internal_id__venue_type_id=venue_type).values_list('venue_internal_id__venue_id', flat=True).exclude(exp_venue_availability_id__in=list(blackoutAvailabilityIds))
        #
        # ExpAvailabilities = ExpVenueAvailability.objects.filter(start_date__in=dates_in_the_range, venue_internal_id__venue_type_id=venue_type).exclude(exp_venue_availability_id__in=list(blackoutAvailabilityIds))

        ExpAvailabilityVenueIds = ExpVenueAvailability.objects.filter(venue_internal_id__venue_id__in = venueIds).values_list('venue_internal_id__venue_id', flat=True).exclude(exp_venue_availability_id__in=list(blackoutAvailabilityIds))

        ExpAvailabilities = ExpVenueAvailability.objects.filter(venue_internal_id__venue_id__in = venueIds).exclude(exp_venue_availability_id__in=list(blackoutAvailabilityIds))

        cal_dict = calendar_dict(calculate_alldays(start_date.month))

        # ExpAvailabilityPatternVenueIds_month = ExpVenuePattern.objects.using('default').filter(month_of_year=start_date.month).values_list('exp_venue_availability__venue_internal_id__venue_id', flat=True)
        # ExpAvailabilitiesPattern_month = ExpVenuePattern.objects.using('default').filter(month_of_year=start_date.month)

    bookingPurchases = BookingPurchase.objects.using("default").filter(exp_venue_availability_timeslot_id__exp_venue_availability_id__venue_internal_id__venue_id__in=(list(ExpAvailabilityVenueIds)))

    avb_dict = calculateExpVenueAvailability(ExpAvailabilities, cal_dict)
    # avb_pat_dict = calculateExpVenueAvailabilityPattern(ExpAvailabilitiesPattern_month, avb_dict, cal_dict)
    avb_pat_book_dict = bookingStatusCheck(bookingPurchases, avb_dict)

    available = []
    for avb, avb_obj in avb_pat_book_dict.items():
        for mon, mon_obj in avb_obj.items():
            for day, day_obj in mon_obj.items():
                for dte, dte_obj in day_obj.items():
                    for tme, capacity in dte_obj.items():
                        if capacity >= noOfPeople:
                            available.append(avb)

    return list(set(list(ExpVenueAvailability.objects.using("default").filter(exp_venue_availability_id__in=available).values_list('venue_internal_id__venue_id', flat=True))))


def calculateVenueStayPrice(obj, date_venue_objs):
    for x in date_venue_objs:
        if x['exp_venue_option_id__venue_internal_id__venue_id'] == obj.venue_id:
            price = str(x['venue_base_price'])
            return price


def month_days_between(start_month, end_month):
    months = []
    for i in range(start_month, end_month + 1):
        months.append(i)
    return months


def dates_between(start_date, end_date):
    dates = []
    start_date = start_date.strip()
    start_date = date(int(start_date.split('-')[0]), int(start_date.split('-')[1]), int(start_date.split('-')[2]))
    if end_date and end_date.strip():
        end_date = date(int(end_date.split('-')[0]), int(end_date.split('-')[1]), int(end_date.split('-')[2]))
        delta = end_date - start_date
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            dates.append(str(day.strftime("%Y-%m-%d")))
    else:
        dates.append(str(start_date.strftime("%Y-%m-%d")))

    return dates


# def range_day_of_month(start_date, end_date):
#     range_day_of_months = []
#     if start_date <= end_date:
#         for i in range(start_date, end_date + 1):
#             range_day_of_months.append(i)
#     else:
#         for i in range(end_date, start_date + 1):
#             range_day_of_months.append(i)
#     return range_day_of_months


# def range_of_week_number_of_month(start_date_value, end_date_value):
#     range_week_of_month = []
#     s_d = start_date_value.isocalendar()[1] - start_date_value.replace(day=1).isocalendar()[1] + 1
#     e_d = end_date_value.isocalendar()[1] - end_date_value.replace(day=1).isocalendar()[1] + 1
#     for i in range(s_d, e_d + 1):
#         range_week_of_month.append(i)
#     return range_week_of_month


def calculate_alldays(month , year=None):
    if year is None:
        now = datetime.datetime.now()  # -------- calculate today date
        test_date = datetime.datetime(now.year, month, 1)  # -------- get the first date of the given input month
    else:
        test_date = datetime.datetime(year, month, 1)  # -------- get the first date of the given input month
    nxt_mnth = test_date.replace(day=28) + datetime.timedelta(days=4)
    res = nxt_mnth - datetime.timedelta(days=nxt_mnth.day)  # -------- calculate the end date of the input month
    start_date = test_date  # start date of that month
    l1 = []
    for i in range(0, res.day):
        l1.append(str(start_date.strftime("%Y-%m-%d")))
        start_date = start_date + datetime.timedelta(days=1)
    return l1




def calculateExpVenueAvailability(ExpAvailabilities, cal_dict,single_date=None):
    print(ExpAvailabilities, cal_dict)
    availability_data = {}
    curr_time = datetime.datetime.now()
    curr_date = curr_time.date()
    for avb in ExpAvailabilities:
        l3 = []
        expVenueTimeslots = ExpVenueAvailabilityTimeslot.objects.using("default").filter(exp_venue_availability_id=avb.exp_venue_availability_id)
        if len(expVenueTimeslots) > 0 and avb.start_date is not None:
            if avb.exp_venue_availability_id not in availability_data:
                availability_data[avb.exp_venue_availability_id] = {}
            ExpAvailabilitiesPatterns = ExpVenuePattern.objects.using('default').filter(exp_venue_availability_id=avb.exp_venue_availability_id)
            if avb.end_date is not None and avb.end_date >= curr_date and len(list(ExpAvailabilitiesPatterns)) == 0:  # -short term events and one day events
                if avb.start_date >= curr_date:
                    l3 = dates_between(str(avb.start_date.strftime("%Y-%m-%d")), str(avb.end_date.strftime("%Y-%m-%d")))
                else:
                    l3 = dates_between(str(curr_date.strftime("%Y-%m-%d")), str(avb.end_date.strftime("%Y-%m-%d")))

            elif avb.end_date is not None and avb.end_date >= curr_date and len(list(ExpAvailabilitiesPatterns)) != 0:
                for pattern in ExpAvailabilitiesPatterns:
                    if pattern.day_of_week is not None and pattern.month_of_year is not None:
                        if cal_dict.get(pattern.month_of_year, {}).get(pattern.day_of_week):
                            l3 += cal_dict.get(pattern.month_of_year, {}).get(pattern.day_of_week)
                    elif pattern.month_of_year is None and pattern.day_of_week is not None:
                        start_month = avb.start_date.month
                        end_month = avb.end_date.month
                        month_range = month_days_between(start_month, end_month)
                        for m in month_range:
                            if cal_dict.get(m, {}).get(pattern.day_of_week):
                                l3.extend(cal_dict.get(m, {}).get(pattern.day_of_week))

            elif avb.end_date is None and len(list(ExpAvailabilitiesPatterns)) != 0:
                for pattern in ExpAvailabilitiesPatterns:
                    if pattern.day_of_week is not None and pattern.month_of_year is not None:
                        if cal_dict.get(pattern.month_of_year, {}).get(pattern.day_of_week):
                            l3.extend(cal_dict.get(pattern.month_of_year, {}).get(pattern.day_of_week))

                    elif pattern.day_of_week is not None and pattern.month_of_year is None:
                        start_month = avb.start_date.month
                        if cal_dict.get(start_month, {}).get(pattern.day_of_week):
                            l3.extend(cal_dict.get(pattern.month_of_year, {}).get(pattern.day_of_week))

                    elif pattern.day_of_week is None and pattern.month_of_year is None:
                        pass

            elif avb.end_date is None and len(list(ExpAvailabilitiesPatterns)) == 0:
                pass

            if single_date is not None:
                if single_date in l3:
                    l3 = [single_date]
                else:
                    l3 = []

            for date_Ymd in list(set(l3)):
                date_type = date(int(date_Ymd.split('-')[0]), int(date_Ymd.split('-')[1]), int(date_Ymd.split('-')[2]))
                month_no = date_type.month
                day_no = date_type.weekday() + 1
                if month_no not in availability_data[avb.exp_venue_availability_id]:
                    availability_data[avb.exp_venue_availability_id][month_no] = {}
                if day_no not in availability_data[avb.exp_venue_availability_id][month_no]:
                    availability_data[avb.exp_venue_availability_id][month_no][day_no] = {}
                if date_Ymd not in availability_data[avb.exp_venue_availability_id][month_no][day_no]:
                    availability_data[avb.exp_venue_availability_id][month_no][day_no][date_Ymd] = {}
                for e in expVenueTimeslots:
                    if e.exp_venue_availability_timeslot_id not in availability_data[avb.exp_venue_availability_id][month_no][day_no][date_Ymd]:
                        availability_data[avb.exp_venue_availability_id][month_no][day_no][date_Ymd][e.exp_venue_availability_timeslot_id] = e.capacity

    return availability_data


def calendar_dict(dates_in_the_range):
    d1 = {}
    curr_time = datetime.datetime.now()
    curr_date = curr_time.date()
    for d in dates_in_the_range:
        dte = date(int(d.split('-')[0]), int(d.split('-')[1]), int(d.split('-')[2]))
        if dte >= curr_date:
            day_no = dte.weekday() + 1
            month_no = dte.month
            if month_no not in d1:
                d1[month_no] = {}
            if day_no not in d1[month_no]:
                d1[month_no][day_no] = []
            d1[month_no][day_no].append(d)

    return d1


def calculateExpVenueAvailabilityPattern(ExpAvailabilitiesPattern_month, availability_data, cal_dict):
    print(ExpAvailabilitiesPattern_month, availability_data, cal_dict)
    for pattern_month_avb in ExpAvailabilitiesPattern_month:
        l3 = []
        expVenueTimeslots = ExpVenueAvailabilityTimeslot.objects.using("default").filter(exp_venue_availability_id=pattern_month_avb.exp_venue_availability_id)
        if len(expVenueTimeslots) > 0 and pattern_month_avb.exp_venue_availability.start_date is not None:
            if pattern_month_avb.exp_venue_availability_id not in availability_data:
                availability_data[pattern_month_avb.exp_venue_availability_id] = {}
            if cal_dict.get(pattern_month_avb.month_of_year, {}).get(pattern_month_avb.day_of_week):
                l3 = cal_dict.get(pattern_month_avb.month_of_year, {}).get(pattern_month_avb.day_of_week)

            for date_Ymd in l3:
                date_type = date(int(date_Ymd.split('-')[0]), int(date_Ymd.split('-')[1]), int(date_Ymd.split('-')[2]))
                month_no = date_type.month
                day_no = date_type.weekday() + 1
                if month_no not in availability_data[pattern_month_avb.exp_venue_availability_id]:
                    availability_data[pattern_month_avb.exp_venue_availability_id][month_no] = {}
                if day_no not in availability_data[pattern_month_avb.exp_venue_availability_id][month_no]:
                    availability_data[pattern_month_avb.exp_venue_availability_id][month_no][day_no] = {}
                if date_Ymd not in availability_data[pattern_month_avb.exp_venue_availability_id][month_no][day_no]:
                    availability_data[pattern_month_avb.exp_venue_availability_id][month_no][day_no][date_Ymd] = {}
                for e in expVenueTimeslots:
                    if e.exp_venue_availability_timeslot_id not in availability_data[pattern_month_avb.exp_venue_availability_id][month_no][day_no][date_Ymd]:
                        availability_data[pattern_month_avb.exp_venue_availability_id][month_no][day_no][date_Ymd][e.exp_venue_availability_timeslot_id] = e.capacity

    return availability_data


def bookingStatusCheck(bookingPurchases, availability_data):
    try:
        cancel_status = BookingStatus.objects.using("default").get(booking_status_name="Cancelled")
    except BookingStatus.DoesNotExist:
        cancel_status = None
    
    for booking_purchase in bookingPurchases:
        l3 = []
        if cancel_status is not None:
            status_list = BookingCurrentStatus.objects.using("default").filter(booking_purchase_id=booking_purchase.booking_purchase_id, booking_status_id=cancel_status.booking_status_id).values_list('booking_status_id__booking_status_name')
        else:
            status_list = BookingCurrentStatus.objects.using("default").filter(booking_purchase_id=booking_purchase.booking_purchase_id).values_list('booking_status_id__booking_status_name')
        if booking_purchase.start_date is not None and booking_purchase.end_date is not None:
            l3 = dates_between(str(booking_purchase.start_date.strftime("%Y-%m-%d")), str(booking_purchase.end_date.strftime("%Y-%m-%d")))
        elif booking_purchase.start_date is not None and booking_purchase.end_date is None:
            l3 = [booking_purchase.start_date.strftime("%Y-%m-%d")]
        elif booking_purchase.start_date is None and booking_purchase.end_date is not None:
            l3 = [booking_purchase.end_date.strftime("%Y-%m-%d")]

        for book_date in l3:
            date_type = date(int(book_date.split('-')[0]), int(book_date.split('-')[1]), int(book_date.split('-')[2]))
            avail_id = booking_purchase.exp_venue_availability_timeslot.exp_venue_availability_id
            time_id = booking_purchase.exp_venue_availability_timeslot_id
            month_no = date_type.month
            day_no = date_type.weekday() + 1
            if availability_data.get(avail_id, {}).get(month_no, {}).get(day_no, {}).get(book_date, {}).get(time_id) is not None:
                if "Cancelled" not in status_list:
                    availability_data[avail_id][month_no][day_no][book_date][time_id] = availability_data[avail_id][month_no][day_no][book_date][time_id] - booking_purchase.num_of_people

    return availability_data
