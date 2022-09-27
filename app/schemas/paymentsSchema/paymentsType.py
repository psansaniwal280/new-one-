import graphene
from app.models import *


class BillingAddressType(graphene.ObjectType):
    class Meta:
        model = BillingAddress

    billing_name = graphene.String()
    address = graphene.String()
    city = graphene.String()
    state = graphene.String()
    zip = graphene.Int()


class UserPaymentCardType(graphene.ObjectType):
    card_payment_detail_id = graphene.Int()
    last_four_digits = graphene.Int()
    expiry_month = graphene.Int()
    expiry_year = graphene.Int()
    # security_code = graphene.Int()+
    card_name = graphene.String()
    billing_address = graphene.Field(BillingAddressType)


class PaymentOptionType(graphene.ObjectType):
    payment_option_id = graphene.Int()
    name = graphene.String()
    last_four_digits = graphene.Int()
    expiry_date = graphene.String()


class PaymentOptionField(graphene.ObjectType):
    cards = graphene.List(PaymentOptionType)


class PaymentPageObject(graphene.ObjectType):
    payment_intent_client_secret_id = graphene.String()
    customer_id = graphene.String()
    payment_intent_id = graphene.String()
    ephemeralKey_id = graphene.String()


class BillingAddressResultObject(graphene.ObjectType):
    message = graphene.Boolean()
    billingAddressId = graphene.Int()


class PaymentPayloadObject(graphene.InputObjectType):
    billingAddressId= graphene.Int()
    userId = graphene.Int()
    bookingOptionId = graphene.Int()
    bookingOptionPrice = graphene.Int()
    expVenueAvailabilityTimeslotId = graphene.Int()
    numOfPeople = graphene.Int()
    basePrice = graphene.Int()
    pricePay = graphene.Int()
    baseDealAmt = graphene.Int()
    dealAmtPay = graphene.Int()
    baseTaxAmt = graphene.Int()
    taxAmtPay = graphene.Int()
    baseServiceAmt = graphene.Int()
    serviceAmtPay = graphene.Int()
    baseTotalAmt = graphene.Int()
    totalAmtPay = graphene.Int()
    startDate = graphene.String()
    endDate = graphene.String()
    venueId = graphene.Int()


class BillingAddressesObject(graphene.ObjectType):
    billing_address_id = graphene.Int()
    default_source = graphene.Boolean()


class BillingAddressDetailsObject(graphene.ObjectType):
    billing_address_id = graphene.Int()
    billing_name = graphene.String()
    userId = graphene.Int()
    email = graphene.String()
    mobile_phone = graphene.String()
    country_name = graphene.String()
    country_code_two_char = graphene.String()
    city = graphene.String()
    state = graphene.String()
    state_code = graphene.String()
    zip = graphene.Int()
    address = graphene.String()
    default_source = graphene.Boolean()
