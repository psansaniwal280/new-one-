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


class PaymentStatusResultObject(graphene.ObjectType):
    success = graphene.Boolean()


class PaymentPayloadObject(graphene.InputObjectType):
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
