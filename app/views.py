import json

import channels_graphql_ws
import requests
import stripe
from decouple import config
from django.shortcuts import render, redirect
import jwt
from django.views.decorators.csrf import csrf_exempt

from .models import User, BookingPurchase
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from .schemas.paymentsSchema.paymentSubscription import PaymentSubscribe
from .utilities.sendMail import sendMailToUser
from django.template.loader import render_to_string


def activate_account(request, token):
    domain = "http:127.0.0.1:8000/"
    username = jwt.decode(token, "1232141", algorithms=['HS256'])['user']
    print(username)

    userObjList = User.objects.using('default').values('user_id', 'username', 'is_active')
    for user_obj in userObjList:
        if user_obj['username'] == username:
            user = User.objects.get(user_id=user_obj['user_id'])

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

    userObjList = User.objects.using('default').values('user_id', 'username', 'is_active')
    for user_obj in userObjList:
        if user_obj['username'] == username:
            user = User.objects.get(user_id=user_obj['user_id'])
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
    stripe.api_key = config('STRIPE_SEC_KEY')
    # endpoint_secret = 'whsec_a4982ab06a4019f4456403b349d22a65997eed18774a8ffebe5a42ac7b87c289'
    # sig_header = request.headers['STRIPE_SIGNATURE']
    try:
        payload = request.body
        event = json.loads(payload)
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    data = stripe.PaymentIntent.retrieve(
        event["data"]["object"]["id"],
    )
    payment_intent_id = event["data"]["object"]["id"]
    # payment_intent_id = 22
    metadata = json.loads(str(data['metadata']))
    # Handle the event
    if event['type'] == 'payment_intent.canceled':
        PaymentSubscribe.broadcast(payload="payment canceled", group=str(payment_intent_id))
    elif event['type'] == 'payment_intent.created':
        PaymentSubscribe.broadcast(payload="payment started", group=str(payment_intent_id))
    elif event['type'] == 'payment_intent.payment_failed':
        PaymentSubscribe.broadcast(payload="payment failed", group=str(payment_intent_id))
    elif event['type'] == 'payment_intent.processing':
        PaymentSubscribe.broadcast(payload="payment processing", group=str(payment_intent_id))
    elif event['type'] == 'payment_intent.requires_action':
        PaymentSubscribe.broadcast(payload="payment requires action", group=str(payment_intent_id))
    elif event['type'] == 'payment_intent.succeeded':
        PaymentSubscribe.broadcast(payload="payment succeed", group=str(payment_intent_id))
    # ... handle other event types
    else:
        print('Unhandled event type {}'.format(event['type']))
    return JsonResponse({"success": True})
