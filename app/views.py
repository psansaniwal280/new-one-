import datetime
import json
import requests
import stripe
from decouple import config
from django.shortcuts import render, redirect
import jwt
from django.views.decorators.csrf import csrf_exempt

from .models import User, BookingPurchase, BookingCurrentStatus, BookingStatus, Transaction, PaymentOptionType, PaymentOption

from django.http import HttpResponse, JsonResponse
from django.conf import settings

from .schemas.paymentsSchema.paymentSubscription import PaymentSubscribe
from .utilities.errors import BadRequestException
from .utilities.sendMail import sendMailToUser, sendInvoiceMailToUser
from django.template.loader import render_to_string


def activate_account(request, token):
    domain = "http:127.0.0.1:8000/"
    username = jwt.decode(token, "1232141", algorithms=['HS256'])['user']
    print(username)

    user = User.objects.using('default').get(username=username)

    if username and not user.is_active:
        user.is_active = True
        user.save()
        html = "<html><body><p>Successfully confimed your email address!</p></body></html>"
    elif username and user.is_active:
        html = "<html><body><p>Already confimed your email address!</p></body></html>"
    else:
        html = "<html><body>Error!</body></html>"

    return HttpResponse(html)


def resend_email(request, token):
    print("I am in resend function")
    username = jwt.decode(token, "1232141", algorithms=['HS256'])['user']

    user = User.objects.using('default').get(username=username)

    # user = User.objects.get(username=username)
    name = user.first_name + user.last_name
    email = user.email
    html = "<html><body> Successful!</body></html>"
    print(username)
    if username and not user.is_activated:
        sendMailToUser(name, username, email)
        html = "<html><body>Successfully resent confirmation link to your email.</body></html>"
    return HttpResponse(html)


@csrf_exempt
def webhook(request):
    print("webhook got the event")
    stripe.api_key = config('STRIPE_SEC_KEY')
    try:
        payload = request.body
        event = json.loads(payload)
        error = event["data"]["object"]["last_payment_error"]
        if error and "message" in error:
            print("Error--->", error['message'])
            return JsonResponse({"success": False})

    except ValueError as e:
        raise e
    except stripe.error.SignatureVerificationError as e:
        raise e

    try:
        data = stripe.PaymentIntent.retrieve(
            event["data"]["object"]["id"],
        )
        payment_intent_id = event["data"]["object"]["id"]
        metadata = json.loads(str(data['metadata']))
        customer = event["data"]["object"]["customer"]

        billing_address_city = event["data"]["object"]["charges"]["data"][0]['billing_details']['address']['city']
        billing_address_country = event["data"]["object"]["charges"]["data"][0]['billing_details']['address']['country']
        billing_address_line1 = event["data"]["object"]["charges"]["data"][0]['billing_details']['address']['line1']
        billing_address_line2 = event["data"]["object"]["charges"]["data"][0]['billing_details']['address']['line2']
        billing_address_postal_code = event["data"]["object"]["charges"]["data"][0]['billing_details']['address']['postal_code']
        billing_address_postal_state = event["data"]["object"]["charges"]["data"][0]['billing_details']['address']['state']
        payment_method_id = event["data"]["object"]["charges"]["data"][0]['payment_method']

        billing_name = event["data"]["object"]["charges"]["data"][0]['billing_details']['name']
        billing_email = event["data"]["object"]["charges"]["data"][0]['billing_details']['email']
        billing_phone = event["data"]["object"]["charges"]["data"][0]['billing_details']['phone']

        if "bookingPurchaseId" not in metadata:
            print("creating data in bookin gpurxhase table")

            bookingPurchase = BookingPurchase.objects.create(
                exp_venue_availability_timeslot_id=metadata.get('expVenueAvailabilityTimeslotId'),
                user_id=metadata.get('userId'),
                num_of_people=metadata.get('numOfPeople'),
                base_price=metadata.get('basePrice'),
                price_pay=metadata.get('pricePay'),
                base_deal_amt=metadata.get('baseDealAmt'),
                deal_amt_pay=metadata.get('dealAmtPay'),
                base_tax_amt=metadata.get('baseTaxAmt'),
                tax_amt_pay=metadata.get('taxAmtPay'),
                base_service_amt=metadata.get('baseServiceAmt'),
                service_amt_pay=metadata.get('serviceAmtPay'),
                base_total_amt=metadata.get('baseTotalAmt'),
                total_amt_pay=metadata.get('totalAmtPay'),
                created_by=metadata.get('userId'),
                start_date=metadata.get('startDate'),
                end_date=metadata.get('endDate'),
                venue_id=metadata.get('venueId'))
            bookingPurchase.save()
            print("saving booking purchase id in payment intent metadata")

            stripe.PaymentIntent.modify(payment_intent_id, metadata={"bookingPurchaseId": bookingPurchase.booking_purchase_id})
            metadata["bookingPurchaseId"] = bookingPurchase.booking_purchase_id

        data = stripe.PaymentIntent.retrieve(
            event["data"]["object"]["id"],
        )
        payment_intent_id = event["data"]["object"]["id"]
        metadata = json.loads(str(data['metadata']))

        # Handle the event
        if event['type'] == 'payment_intent.canceled':
            print("payment cancelled")
            if "bookingCurrentStatusId" not in metadata:
                print("creating the status cancel")
                bookingCurrentStatus = BookingCurrentStatus.objects.using('default').create(
                    booking_purchase_id=int(metadata.get('bookingPurchaseId')),
                    booking_status_id=BookingStatus.objects.get(booking_status_name="Cancelled").booking_status_id,
                    created_by=int(metadata.get('userId'))
                )
                bookingCurrentStatus.save()
                stripe.PaymentIntent.modify(payment_intent_id, metadata={"bookingCurrentStatusId": bookingCurrentStatus.booking_current_status_id})
            else:
                print("updating the status cancel")
                bookingCurrentStatus = BookingCurrentStatus.objects.using('default').filter(booking_current_status_id=int(metadata.get('bookingCurrentStatusId'))).update(
                    booking_status_id=BookingStatus.objects.get(booking_status_name="Cancelled").booking_status_id,
                )

        elif event['type'] == 'payment_intent.payment_failed':
            print("Payment Failed")
            if "bookingCurrentStatusId" not in metadata:
                print("creating the status failed")
                bookingCurrentStatus = BookingCurrentStatus.objects.using('default').create(
                    booking_purchase_id=int(metadata.get('bookingPurchaseId')),
                    booking_status_id=BookingStatus.objects.get(booking_status_name="Failed").booking_status_id,
                    created_by=int(metadata.get('userId'))
                )
                bookingCurrentStatus.save()
                print("modifying the payment intent metadata fail status")
                stripe.PaymentIntent.modify(payment_intent_id, metadata={"bookingCurrentStatusId": bookingCurrentStatus.booking_current_status_id})

            else:
                print("modifying  the status fail")
                bookingCurrentStatus = BookingCurrentStatus.objects.using('default').filter(booking_current_status_id=int(metadata['bookingCurrentStatusId'])).update(
                    booking_status_id=BookingStatus.objects.get(booking_status_name="Failed").booking_status_id,
                )

        elif event['type'] == 'payment_intent.processing':
            print("payment processing --------------")
            if "bookingCurrentStatusId" not in metadata:
                print("creating   the status processing")
                bookingCurrentStatus = BookingCurrentStatus.objects.using('default').create(
                    booking_purchase_id=int(metadata.get('bookingPurchaseId')),
                    booking_status_id=BookingStatus.objects.get(booking_status_name="Pending").booking_status_id,
                    created_by=int(metadata.get('userId'))
                )
                bookingCurrentStatus.save()
                print("modifying the payment intent metadata fail processing")
                stripe.PaymentIntent.modify(payment_intent_id, metadata={"bookingCurrentStatusId": bookingCurrentStatus.booking_current_status_id})

            else:
                print("modifying  the status processing")
                bookingCurrentStatus = BookingCurrentStatus.objects.using('default').filter(booking_current_status_id=int(metadata['bookingCurrentStatusId'])).update(
                    booking_status_id=BookingStatus.objects.get(booking_status_name="Pending").booking_status_id,
                )

        elif event['type'] == 'payment_intent.requires_action':
            print("payment requires action")

        elif event['type'] == 'payment_intent.succeeded':
            print("payment succeeded")
            if event["data"]["object"]["charges"]["data"][0]['payment_method_details']['type'] == 'card':
                print("payment success getting the card details")
                fingerprint = event["data"]["object"]["charges"]["data"][0]['payment_method_details']['card']['fingerprint']

                payment_method_list = stripe.Customer.list_payment_methods(
                    customer,
                    type="card",
                )
                print("payment success get payment method list", )
                detach_payment_method = 0
                flag = 0
                l1 = []
                if len(payment_method_list["data"]) > 1:
                    for p in payment_method_list["data"]:
                        print(p["id"])
                        if p["card"]["fingerprint"] == fingerprint:
                            l1.append(p)
                            print("finger print matched")
                            stripe.PaymentMethod.modify(
                                p["id"],
                                billing_details={
                                    "address": {
                                        "city": billing_address_city,
                                        "country": billing_address_country,
                                        "line1": billing_address_line1,
                                        "line2": billing_address_line2,
                                        "postal_code": billing_address_postal_code,
                                        "state": billing_address_postal_state
                                    },
                                    'email': billing_email,
                                    'name': billing_name,
                                    'phone': billing_phone})
                            print("modified the billing address")

                if len(l1) > 1:
                    detach_payment_method = payment_method_id
                    try:
                        print("detaching the payment method id ", payment_method_id)
                        stripe.PaymentMethod.detach(
                            detach_payment_method,
                        )
                    except Exception as e:
                        print(e)

            if "bookingCurrentStatusId" not in metadata:
                print("creating   the status succeed")
                bookingCurrentStatus = BookingCurrentStatus.objects.using('default').create(
                    booking_purchase_id=int(metadata.get('bookingPurchaseId')),
                    booking_status_id=BookingStatus.objects.get(booking_status_name="Completed").booking_status_id,
                    created_by=int(metadata.get('userId'))
                )
                bookingCurrentStatus.save()
                print("modifying  the status succeed in payment intent metadata ")
                stripe.PaymentIntent.modify(payment_intent_id, metadata={"bookingCurrentStatusId": bookingCurrentStatus.booking_current_status_id})

            else:
                print("modifying  the status succeed")
                bookingCurrentStatus = BookingCurrentStatus.objects.using('default').filter(booking_current_status_id=int(metadata.get('bookingCurrentStatusId'))).update(
                    booking_status_id=BookingStatus.objects.get(booking_status_name="Completed").booking_status_id,
                )
                print(bookingCurrentStatus, "booking status")

            print("adding or getting the payment method type")
            payment_option_type, is_added = PaymentOptionType.objects.using('payments').get_or_create(
                payment_option_type=event["data"]["object"]['payment_method_types'][0]
            )

            print("linking the payment method type and user id")
            paymentOption = PaymentOption.objects.using('payments').create(
                user_id=int(metadata.get('userId')),
                payment_option_type_id=payment_option_type.payment_option_type_id
            )
            print("adding the data in transaction")
            Transaction.objects.using('payments').create(
                user_payment_type_id=paymentOption.payment_option_id,
                date_created=datetime.datetime.now(),
                booking_purchase_id=int(metadata.get('bookingPurchaseId'))
            )

        else:
            print('Unhandled event type {}'.format(event['type']))

        # content = requests.get(url=event["data"]["object"]["charges"]["data"][0]['receipt_url']).text
        print("sending invoice to", billing_email)
        res = sendInvoiceMailToUser(billing_name, billing_email, event["data"]["object"]["charges"]["data"][0]['receipt_url'])
        print(res)
        return JsonResponse({"success": True})
    except Exception as e:
        raise e
