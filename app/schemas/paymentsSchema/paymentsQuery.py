import json

import graphene
import stripe
from decouple import config

from .paymentSubscription import PaymentSubscribe
from .paymentsType import *
from app.models import *
from app.utilities.errors import *
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

from ...utilities import Verification


class Query(graphene.ObjectType):
    # Get Payment Options
    paymentInfo = graphene.Field(UserPaymentCardType, paymentOptionId=graphene.Int(), userId=graphene.Int())

    paymentOptions = graphene.Field(PaymentOptionField, userId=graphene.Int())

    paymentPage = graphene.Field(PaymentPageObject, userId=graphene.Int(), bookingOptionId=graphene.Int(), bookingOptionPrice=graphene.Int(),
                                 expVenueAvailabilityTimeslotId=graphene.Int(),
                                 numOfPeople=graphene.Int(),
                                 basePrice=graphene.Int(),
                                 pricePay=graphene.Int(),
                                 baseDealAmt=graphene.Int(),
                                 dealAmtPay=graphene.Int(),
                                 baseTaxAmt=graphene.Int(),
                                 taxAmtPay=graphene.Int(),
                                 baseServiceAmt=graphene.Int(),
                                 serviceAmtPay=graphene.Int(),
                                 baseTotalAmt=graphene.Int(),
                                 totalAmtPay=graphene.Int(),
                                 startDate=graphene.String(),
                                 endDate=graphene.String(),
                                 venueId=graphene.Int()
                                 )

    paymentStatusResult = graphene.Field(PaymentStatusResultObject, message=graphene.String(), response=PaymentPayloadObject(), paymentIntentId=graphene.String())

    # Get Payment Info
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

        result = {"card_payment_detail_id": card.card_payment_detail_id, "last_four_digits": str(int(float(decrypted_card_number.decode())))[-4:], "expiry_month": card.expiry_month, "expiry_year": card.expiry_year, 'card_name': card.card_name, 'billing_address': card.billing_address}

        return result

    # Get List of Payment Option by User Id
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
        card = []

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

            expiryDate = str(cardObj.expiry_month) + "/" + str(cardObj.expiry_year)
            if each[2] == 1:
                card.append({"payment_option_id": each[0], "name": nameObj.billing_name, "last_four_digits": str(int(float(decrypted_card_number.decode())))[-4:], "expiry_date": expiryDate})
            #    cards= PaymentOptionType(, nameObj.billing_name, str(int(float(decrypted_card_number.decode())))[-4:], expiryDate)
        result = {
            "cards": card
        }
        print("result", result)
        return result

    def resolve_paymentStatusResult(self, info, **kwargs):
        message = kwargs.get("message")
        response = kwargs.get("response")
        paymentIntentId = kwargs.get("paymentIntentId")
        payload = {
            "message": message,
            "response": response
        }
        # payload="hello"
        PaymentSubscribe.broadcast(payload=payload, group=paymentIntentId)
        return PaymentStatusResultObject(
            success=True
        )

    def resolve_paymentPage(self, info, **kwargs):
        userId = kwargs.get("userId")
        bookingOptionId = kwargs.get("bookingOptionId")
        bookingOptionPrice = kwargs.get("bookingOptionPrice")
        expVenueAvailabilityTimeslotId = 1
        numOfPeople = kwargs.get('numOfPeople')
        basePrice = kwargs.get('basePrice')
        pricePay = kwargs.get('pricePay')
        baseDealAmt = kwargs.get('baseDealAmt')
        dealAmtPay = kwargs.get('dealAmtPay')
        baseTaxAmt = kwargs.get('baseTaxAmt')
        taxAmtPay = kwargs.get('taxAmtPay')
        baseServiceAmt = kwargs.get('baseServiceAmt')
        serviceAmtPay = kwargs.get('serviceAmtPay')
        baseTotalAmt = kwargs.get('baseTotalAmt')
        totalAmtPay = kwargs.get('totalAmtPay')
        startDate = kwargs.get('startDate')
        endDate = kwargs.get('endDate')
        venueId = kwargs.get('venueId')
        # Verification.user_verify(userId)
        # Verification.expVenueOption_verify(bookingOptionId)
        stripe.api_key = config('STRIPE_SEC_KEY')
        try:
            customer = stripe.Customer.create(
                id="cus_" + str(userId)
            )
        except Exception as e:
            customer = stripe.Customer.retrieve("cus_" + str(userId))

        paymentIntent = stripe.PaymentIntent.create(
            amount=bookingOptionPrice,
            currency='usd',
            customer=customer['id'],
            payment_method_types=['card'],
            metadata={
                "userId": userId,
                "bookingOptionId": bookingOptionId,
                "bookingOptionPrice": bookingOptionPrice,
                "expVenueAvailabilityTimeslotId": expVenueAvailabilityTimeslotId,
                "numOfPeople": numOfPeople,
                "basePrice": basePrice,
                "pricePay": pricePay,
                "baseDealAmt": baseDealAmt,
                "dealAmtPay": dealAmtPay,
                "baseTaxAmt": baseTaxAmt,
                "taxAmtPay": taxAmtPay,
                "baseServiceAmt": baseServiceAmt,
                "serviceAmtPay": serviceAmtPay,
                "baseTotalAmt": baseTotalAmt,
                "totalAmtPay": totalAmtPay,
                "startDate": startDate,
                "endDate": endDate,
                "venueId": venueId
            }
        )

        ephemeralKey = stripe.EphemeralKey.create(
            customer=customer['id'],
            stripe_version='2022-08-01',
        )

        return PaymentPageObject(
            payment_intent_client_secret_id=paymentIntent.client_secret,
            customer_id=customer.id,
            payment_intent_id=paymentIntent['id'],
            ephemeralKey_id=ephemeralKey.secret

        )
