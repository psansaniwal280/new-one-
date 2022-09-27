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

    paymentPage = graphene.Field(PaymentPageObject,
                                 billing_address_id=graphene.Int(),
                                 userId=graphene.Int(required=True),
                                 bookingOptionId=graphene.Int(required=True),
                                 bookingOptionPrice=graphene.Int(required=True),
                                 expVenueAvailabilityTimeslotId=graphene.Int(required=True),
                                 numOfPeople=graphene.Int(required=True),
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
                                 startDate=graphene.String(required=True),
                                 endDate=graphene.String(),
                                 venueId=graphene.Int(required=True)
                                 )

    billingAddresses = graphene.List(BillingAddressesObject, userId=graphene.Int())
    billingAddressDetails = graphene.Field(BillingAddressDetailsObject, userId=graphene.Int(), billingAddressId=graphene.Int())

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

    def resolve_paymentPage(self, info, **kwargs):
        userId = kwargs.get("userId")
        billing_address_id = kwargs.get("billingAddressId")
        bookingOptionId = kwargs.get("bookingOptionId")
        bookingOptionPrice = kwargs.get("bookingOptionPrice")
        expVenueAvailabilityTimeslotId = kwargs.get('expVenueAvailabilityTimeslotId')
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
        endDate = kwargs.get('endDate') if kwargs.get('endDate') else startDate
        venueId = kwargs.get('venueId')

        user = Verification.user_verify(userId)
        user_profile = Verification.user_profile(userId)
        booking_option = Verification.expVenueOption_verify(bookingOptionId)
        timeslot = Verification.exp_venue_timeslot(expVenueAvailabilityTimeslotId)
        venue = Verification.venue_verify(venueId)
        start_date = datetime.date(int(startDate.split('-')[0]), int(startDate.split('-')[1]), int(startDate.split('-')[2]))

        Verification.past_date_verify(start_date.day, start_date.month, start_date.year)
        if endDate:
            end_date = datetime.date(int(endDate.split('-')[0]), int(endDate.split('-')[1]), int(endDate.split('-')[2]))
            Verification.past_date_verify(end_date.day, end_date.month, end_date.year)

        if billing_address_id:
            billing_address = Verification.address_verify(billing_address_id, userId)
        else:
            try:
                billing_address = BillingAddress.objects.using('payments').get(default_source=True, user_id=userId)
            except BillingAddress.DoesNotExist:
                raise NotFoundException("No default billing address is set")

        stripe.api_key = config('STRIPE_SEC_KEY')

        if billing_address_id:
            billing_address = Verification.address_verify(billing_address_id,userId)
        else:
            try:
                billing_address = BillingAddress.objects.using('payments').get(default_source=True,user_id=userId)
            except BillingAddress.DoesNotExist:
                raise NotFoundException("No default billing address is set")

        try:
            customer = stripe.Customer.create(
                id="cus_" + str(userId),
                address={
                    # "city": billing_address.city,
                    "country": billing_address.country_code_two_char,
                    "postal_code": billing_address.zip,
                    # "state": billing_address.state_code
                },
                description=str(user.user_id),
                email=user.email,
                name=user.username,
                phone=user.phone_number,
                # created=str(datetime.datetime.now().timestamp()),
                # livemode=False
            )
        except Exception as e:

            stripe.Customer.modify(
                "cus_" + str(userId),
                address={
                    # "city": billing_address.city,
                    "country": billing_address.country_code_two_char,
                    "postal_code": billing_address.zip,
                    # "state": billing_address.state_code
                },
                description=str(user.user_id),
                email=user.email,
                name=user.username,
                phone=user.phone_number,
                # created=str(datetime.datetime.now().timestamp()),
                # livemode=False

            )
            customer = stripe.Customer.retrieve("cus_" + str(userId))
            print(customer)

        paymentIntent = stripe.PaymentIntent.create(
            amount=bookingOptionPrice,
            currency='inr',
            customer=customer['id'],
            setup_future_usage='off_session',
            description="good",  # str(bookingOptionId.booking_option_name),
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

    def resolve_billingAddressDetails(self, info, **kwargs):
        userId = kwargs.get('userId')
        billingAddressId = kwargs.get('billingAddressId')
        Verification.user_verify(userId)
        billing_details = Verification.address_verify(billingAddressId, userId)
        Verification.single_address_default(userId)
        return BillingAddressDetailsObject(
            billing_address_id=billing_details.billing_address_id,
            billing_name=billing_details.billing_name,
            userId=billing_details.user_id,
            email=billing_details.email,
            mobile_phone=billing_details.mobile_phone,
            country_name=billing_details.country_name,
            country_code_two_char=billing_details.country_code_two_char,
            city=billing_details.city,
            state=billing_details.state,
            state_code=billing_details.state_code,
            zip=billing_details.zip,
            address=billing_details.address,
            default_source=billing_details.default_source
        )

    def resolve_billingAddresses(self, info, **kwargs):
        userId = kwargs.get('userId')
        Verification.user_verify(userId)
        Verification.single_address_default(userId)
        billing_addresses = BillingAddress.objects.using('payments').filter(user_id=userId).values('billing_address_id', 'default_source')
        return billing_addresses
