import graphene

from app.schemas.paymentsSchema.paymentsType import BillingAddressResultObject
from app.utilities import Verification
from app.utilities.toBigInt import BigInt
from app.models import *
from app.utilities.errors import *
from django.db.models import Max, Avg
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

"""
    Payment - Add Card Option
"""
import graphene


class PaymentCardMutation(graphene.Mutation):
    payment_option_id = graphene.Int()
    last_four_digits = graphene.Int()

    class Arguments:
        user_id = graphene.Int()
        card_number = graphene.Argument(BigInt)
        expiry_month = graphene.Int()
        expiry_year = graphene.Int()
        security_code = graphene.Int()
        cardName = graphene.String()
        billingName = graphene.String()
        streetAddress = graphene.String()
        city = graphene.String()
        state = graphene.String()
        zipcode = graphene.Int()

    def mutate(self, info, **kwargs):
        userId = kwargs.get('user_id')
        cardNumber = kwargs.get('card_number')
        expiryMonth = kwargs.get('expiry_month')
        expiryYear = kwargs.get('expiry_year')
        securityCode = kwargs.get('security_code')
        cardName = kwargs.get('cardName')
        billingName = kwargs.get('billingName')
        streetAddress = kwargs.get('streetAddress')
        city = kwargs.get('city')
        state = kwargs.get('state')
        zipcode = kwargs.get('zipcode')

        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if cardNumber is not None:
            print(cardNumber)
            last_four_digits = str(int(cardNumber))[-4:]
            print(last_four_digits)
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
            encrypted_card_number = f.encrypt(str(cardNumber).encode())
            print(encrypted_card_number)
        else:
            raise BadRequestException("invalid request; cardNumber provided is invalid", 400)
        if expiryMonth is not None:
            if expiryMonth > 12:
                raise BadRequestException("invalid request; expiryMonth provided is invalid", 400)
            else:
                pass
        else:
            raise BadRequestException("invalid request; expiryMonth provided is invalid", 400)
        if expiryYear is not None:
            pass
        else:
            raise BadRequestException("invalid request; expiryYear provided is invalid", 400)
        if securityCode is not None:

            password_provided = "password"  # This is input in the form of a string
            password = password_provided.encode()  # Convert to type bytes
            salt = b'salt_'  # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            f = Fernet(key)
            encrypted_security_card = f.encrypt(str(securityCode).encode())
            print(encrypted_security_card)

            # password_provided = "password"  # This is input in the form of a string
            # password = password_provided.encode()  # Convert to type bytes
            # salt = b'salt_'  # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
            # kdf = PBKDF2HMAC(
            #     algorithm=hashes.SHA256(),
            #     length=32,
            #     salt=salt,
            #     iterations=100000,
            #     backend=default_backend()
            # )
            # key = base64.urlsafe_b64encode(kdf.derive(password)) 
            # f = Fernet(key)
            # encrypted = b'gAAAAABh4gTuKyshpkptPVn0K9m3zoJ12bJ5cxzdKI3ZkLgcTKsB0jeJc0ZnfZmWQ792AfOHxtgrcKqIgAIdPwsrL3r_JahGqw=='
            # decrypted = f.decrypt(encrypted)
            # print(decrypted.decode()) 
        else:
            raise BadRequestException("invalid request; securityCode provided is invalid", 400)
        if cardName is not None:
            if (cardName and cardName.strip()):
                pass
            else:
                raise BadRequestException("invalid request; cardName provided is empty")
        else:
            raise BadRequestException("invalid request; cardName provided is invalid")

        if billingName is not None:
            if (billingName and billingName.strip()):
                pass
            else:
                raise BadRequestException("invalid request; billingName provided is empty")
        else:
            raise BadRequestException("invalid request; billingName provided is invalid")

        if streetAddress is not None:
            if (streetAddress and streetAddress.strip()):
                pass
            else:
                raise BadRequestException("invalid request; streetAddress provided is empty")
        else:
            raise BadRequestException("invalid request; streetAddress provided is invalid")

        if city is not None:
            if (city and city.strip()):
                pass
            else:
                raise BadRequestException("invalid request; city provided is empty")
        else:
            raise BadRequestException("invalid request; city provided is invalid")

        if state is not None:
            if (state and state.strip()):
                pass
            else:
                raise BadRequestException("invalid request; state provided is empty")
        else:
            raise BadRequestException("invalid request; state provided is invalid")

        if zipcode is not None:
            pass
        else:
            raise BadRequestException("invalid request; zipcode provided is invalid")

        # last_payment_option = PaymentOption.objects.using('payments').all().aggregate(Max('payment_option_id'))
        # payment_option_id = last_payment_option['payment_option_id__max']+1 if last_payment_option['payment_option_id__max'] else 1

        option = PaymentOption.objects.using('payments').create(
            # payment_option_id =payment_option_id,
            payment_option_type_id=1,
            user_id=userId
        )
        option.save()

        # last_billing_address = BillingAddress.objects.using('payments').all().aggregate(Max('billing_address_id'))
        # billing_address_id = last_billing_address['billing_address_id__max']+1 if last_billing_address['billing_address_id__max'] else 1

        billing_address = BillingAddress.objects.using('payments').create(
            # billing_address_id = billing_address_id,
            billing_name=billingName,
            email=user.email,
            address=streetAddress,
            city=city,
            state=state,
            zip=zipcode
        )
        billing_address.save()

        # last_card_payment_detail = CardPaymentDetail.objects.using('payments').all().aggregate(Max('card_payment_detail_id'))
        # card_payment_detail_id = last_card_payment_detail['card_payment_detail_id__max']+1 if last_card_payment_detail['card_payment_detail_id__max'] else 1 

        card = CardPaymentDetail.objects.using('payments').create(
            # card_payment_detail_id = card_payment_detail_id,
            card_number=encrypted_card_number,
            expiry_month=expiryMonth,
            expiry_year=expiryYear,
            security_code=encrypted_security_card,
            billing_address_id=billing_address.billing_address_id,
            payment_option_id=option.payment_option_id,
            card_name=cardName
        )
        card.save()

        return PaymentCardMutation(payment_option_id=option.payment_option_id, last_four_digits=last_four_digits)

        # decryptor = PKCS1_OAEP.new(keyPair)
        # decrypted = decryptor.decrypt(encrypted)
        # print('Decrypted:', int(float(decrypted.decode())))


class AddBillingAddress(graphene.Mutation):
    message = graphene.String()
    billingAddressId = graphene.Int()

    class Arguments:
        billing_name = graphene.String(required=True)
        userId = graphene.Int(required=True)
        email = graphene.String(required=True)
        mobile_phone = graphene.String()
        country_id = graphene.Int(required=True)
        city_id = graphene.Int(required=True)
        state_id = graphene.Int(required=True)
        zip_code_id = graphene.String(required=True)
        address = graphene.String(required=True)
        default_source = graphene.Boolean()

    def mutate(self, info, **kwargs):
        billing_name = kwargs.get('billing_name')
        userId = kwargs.get('userId')
        email = kwargs.get('email')
        mobile_phone = kwargs.get('mobile_phone')
        country = kwargs.get('country_id')
        city = kwargs.get('city_id')
        state = kwargs.get('state_id')
        address = kwargs.get('address')
        zip = kwargs.get('zip_code_id')
        default_source = kwargs.get('default_source') if kwargs.get('default_source') else False

        Verification.user_verify(userId)
        Verification.single_address_default(userId)
        city_data = Verification.city_verify(city)
        country_data = Verification.country_verify(country)
        state_data = Verification.state_verify(state)
        Verification.country_state_city_relation(country, state, city)

        no_of_address = BillingAddress.objects.using('payments').filter(user_id=userId).count()
        if no_of_address == 0:
            default_source = True

        billing_address, is_already_added = BillingAddress.objects.using('payments').get_or_create(billing_name=billing_name.strip(),
                                                                                                   user_id=userId,
                                                                                                   email=email.strip(),
                                                                                                   address=address.strip(),
                                                                                                   city=city_data.city_name,
                                                                                                   state=state_data.state_name,
                                                                                                   zip=zip.strip(),
                                                                                                   mobile_phone=mobile_phone.strip() if mobile_phone else None,
                                                                                                   country_code_two_char=country_data.country_code_two_char,
                                                                                                   state_code=state_data.state_code,
                                                                                                   country_name=country_data.country_name
                                                                                                   )

        if is_already_added is False:
            raise BadRequestException("These billing details is already added")
        else:
            no_of_address = BillingAddress.objects.using('payments').filter(user_id=userId).count()
            if default_source is True:
                if no_of_address >= 1:
                    BillingAddress.objects.using('payments').filter(user_id=userId, default_source=True).update(default_source=False)
                    BillingAddress.objects.using('payments').filter(billing_address_id=billing_address.billing_address_id).update(default_source=default_source)
            else:
                BillingAddress.objects.using('payments').filter(billing_address_id=billing_address.billing_address_id).update(default_source=default_source)

        return BillingAddressResultObject(
            message="Billing address added successfully",
            billingAddressId=billing_address.billing_address_id
        )


class UpdateBillingAddress(graphene.Mutation):
    message = graphene.String()
    billingAddressId = graphene.Int()

    class Arguments:
        billing_address_id = graphene.Int(required = True)
        billing_name = graphene.String()
        userId = graphene.Int(required = True)
        email = graphene.String()
        mobile_phone = graphene.String()
        country_id = graphene.Int()
        city_id = graphene.Int()
        state_id = graphene.Int()
        zip_code_id = graphene.String()
        address = graphene.String()
        default_source = graphene.Boolean()

    def mutate(self, info, **kwargs):
        billing_address_id = kwargs.get('billing_address_id')
        billing_name = kwargs.get('billing_name')
        userId = kwargs.get('userId')
        email = kwargs.get('email')
        mobile_phone = kwargs.get('mobile_phone')
        country = kwargs.get('country_id')
        city = kwargs.get('city_id')
        state = kwargs.get('state_id')
        address = kwargs.get('address')
        zip = kwargs.get('zip_code_id')
        default_source = kwargs.get('default_source')

        Verification.user_verify(userId)
        billing_address = Verification.address_verify(billing_address_id,userId)
        Verification.single_address_default(userId)

        if billing_name and billing_name.strip():
            if billing_address.billing_name != billing_name.strip():
                billing_address.billing_name = billing_name.strip()

        if email and email.strip():
            if billing_address.email != email.strip():
                billing_address.email = email.strip()

        if address and address.strip():
            if billing_address.address != address.strip():
                billing_address.address = address.strip()

        # --update zip , country, state and city when they all are given as input
        if city and country and state:
            city_data = Verification.city_verify(city)
            stateDetail = Verification.state_verify(state)
            countryDetail = Verification.country_verify(country)
            Verification.country_state_city_relation(country, state, city)
            cityName = city_data.city_name
            if billing_address.city != cityName:
                billing_address.city = cityName
            if billing_address.state != stateDetail.state_name:
                billing_address.state = stateDetail.state_name
                billing_address.state_code = stateDetail.state_code
            if billing_address.country_name != countryDetail.country_name:
                billing_address.country_name = countryDetail.country_name
                billing_address.country_code_two_char = countryDetail.country_code_two_char
        elif city is None and country is None and state is None:
            pass
        else:
            raise BadRequestException('For updating any of these things city,state, country , please provide all these 3 fields')

        if mobile_phone and mobile_phone.strip():
            if billing_address.mobile_phone != mobile_phone.strip():
                billing_address.mobile_phone = mobile_phone.strip()

        if zip and zip.strip():
            if billing_address.zip != zip.strip():
                billing_address.zip = zip.strip()

        if default_source is not None:
            if billing_address.default_source != default_source:
                no_of_address = BillingAddress.objects.using('payments').filter(user_id=userId).count()
                if billing_address.default_source is True and default_source is False:
                    raise BadRequestException('one default address should be there')
                if billing_address.default_source is False and default_source is True:
                    if no_of_address == 1:
                        print('It is a error -----------------------------')
                        billing_address.default_source = default_source
                    elif no_of_address > 1:
                        BillingAddress.objects.using('payments').filter(user_id=userId, default_source=True).update(default_source=False)
                        billing_address.default_source = default_source

        billing_address.save()

        return BillingAddressResultObject(
            message="successfully updated the billing address ",
            billingAddressId=billing_address_id
        )


class DeleteBillingAddress(graphene.Mutation):
    message = graphene.String()
    billingAddressId = graphene.Int()

    class Arguments:
        billing_address_id = graphene.Int()
        userId = graphene.Int()

    def mutate(self, info, **kwargs):
        billing_address_id = kwargs.get('billing_address_id')
        userId = kwargs.get('userId')

        Verification.user_verify(userId)
        billing_address = Verification.address_verify(billing_address_id,userId)
        Verification.single_address_default(userId)

        if BillingAddress.objects.using('payments').filter(user_id=userId).count() == 1:
            raise BadRequestException("address can't be empty, one default address should be there")

        if billing_address.default_source:
            raise BadRequestException("default address can't be deleted")
        else:
            billing_address.delete()

        return BillingAddressResultObject(
            message="successfully deleted the billing address",
            billingAddressId=None
        )


class Mutation(graphene.ObjectType):
    add_payment = PaymentCardMutation.Field()
    add_address = AddBillingAddress.Field()
    delete_address = DeleteBillingAddress.Field()
    update_address = UpdateBillingAddress.Field()
