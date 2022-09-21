import graphene
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
            payment_option_type_id = 1,
            user_id = userId
        )
        option.save()

        # last_billing_address = BillingAddress.objects.using('payments').all().aggregate(Max('billing_address_id'))
        # billing_address_id = last_billing_address['billing_address_id__max']+1 if last_billing_address['billing_address_id__max'] else 1

        billing_address = BillingAddress.objects.using('payments').create(
            # billing_address_id = billing_address_id,
            billing_name = billingName,
            email = user.email,
            address = streetAddress,
            city = city,
            state = state,
            zip = zipcode
        )
        billing_address.save()

        # last_card_payment_detail = CardPaymentDetail.objects.using('payments').all().aggregate(Max('card_payment_detail_id'))
        # card_payment_detail_id = last_card_payment_detail['card_payment_detail_id__max']+1 if last_card_payment_detail['card_payment_detail_id__max'] else 1 

        card = CardPaymentDetail.objects.using('payments').create(
            # card_payment_detail_id = card_payment_detail_id,
            card_number = encrypted_card_number,
            expiry_month = expiryMonth,
            expiry_year = expiryYear,
            security_code = encrypted_security_card,
            billing_address_id = billing_address.billing_address_id,
            payment_option_id = option.payment_option_id,
            card_name = cardName
        )
        card.save()
        
        return PaymentCardMutation(payment_option_id=option.payment_option_id, last_four_digits= last_four_digits)
        

        
        
        # decryptor = PKCS1_OAEP.new(keyPair)
        # decrypted = decryptor.decrypt(encrypted)
        # print('Decrypted:', int(float(decrypted.decode())))

class Mutation(graphene.ObjectType):
    add_payment = PaymentCardMutation.Field()