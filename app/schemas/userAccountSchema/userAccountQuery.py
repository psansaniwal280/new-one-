import email
import graphene
from .userAccountType import *
from app.utilities.errors import *
from app.utilities.redis import *
from app.utilities.standardizemethods import *
from app.utilities.sendMail import *
from app.models import *


class Query(graphene.ObjectType):
    
    #Logout
    logout = graphene.Field(stringType, userId=graphene.Int())

    #Send Reset Password Code
    resetPasswordCode = graphene.Field(responseResetPasswordType, email=graphene.String())
    # resendResetPasswordCode = graphene.Field(responseResetPasswordType, email=graphene.String())

    verifyresetpasswordcode = graphene.Field(stringType, code=graphene.String(), token=graphene.String())

    #Get Cache 
    getTokenFromCache = graphene.Field(stringType, userId=graphene.Int())

    #Resend User Activation Link
    resendActivation = graphene.Field(stringType, email=graphene.String())


    #Resend Email to acitvate account
    def resolve_resendActivation(parent, info, **kwargs):
        email = kwargs.get('email')
        if email is not None:
            try:    
                # username = jwt.decode(email, "1232141",algorithms=['HS256'])['user']
                # user = User.objects.using('default').get(email=email)

                user = User.objects.using('default').get(email=email)
                # for user_obj in userObjList:
                #     if user_obj['email'] == email:
                #         user = User.objects.get(user_id=user_obj['user_id'])

                profile = UserProfile.objects.using('default').get(user_id=user.user_id)
                name = profile.user_profile_name
                username = user.username
                
                if username and not user.is_active:
                    sendMailToUser(name, username, email)
                    return stringType(str("successfully resent the activation link"))
                elif username and user.is_active:
                    raise ConflictException("conflict in request; account already activated", 409)
            except User.DoesNotExist:
                raise NotFoundException("email provided is not found")
            except jwt.DecodeError:
                raise BadRequestException("invalid request; email provided is invalid", 400)
        else:
            raise BadRequestException("invalid request; email provided is invalid", 400)

 #Get Cache
    def resolve_getTokenFromCache(slef, info, **kwargs):
        userId= kwargs.get('userId')
        client  = redis_connect()
        if get_routes_from_cache(client, userId) is not None:
            return stringType(str(get_routes_from_cache(client, userId).decode("utf-8")))
        else:
            raise AuthorizationException("userId provided has logged out", 401)

 #Logout
    def resolve_logout(self, info, **kwargs):
        userId = kwargs.get('userId')
        client = redis_connect()
        user = User.objects.using('default').get(user_id=userId)
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjIwMjEwMTA2LCJ1c2VybmFtZSI6IlVzZXI4QGxvb3AiLCJyZWNvbW1lbmRlZFBvc3RzIjpbXX0.4srgfk2N2zgoPzq26RRq0dCZHZtN2C2W97D_5J7o6Ok"
        # print(info.context.session[user.user_id])
        # print(user.user_id)
        if info.context.session[str(user.user_id)]:
            # set_routes_to_cache()
            info.context.session[str(user.user_id)] = {}
            # delete_routes_from_cache(client, str(userId)+"_search_history")
            # delete_routes_from_cache(client, userId)
            return stringType("logout successful")
        else:
            raise AuthorizationException("userId provided has already logged out", 401)

 #SendResetPasswordCode
    def resolve_resetPasswordCode(self, info, **kwargs):
        useremail = kwargs.get('email')
        response = {}
        # sessionObj = {
        #     # 'email': "",
        #     # 'username': "",
        #     # 'userId': "",
        #     'secret': "",
        #     'verified': False
        # }
        if useremail is not None:
            username =''
            email = ''
            userId = 0
            if useremail and useremail.strip():
                try:
                    usr= User.objects.using('default').get(Q(email=useremail) or Q(username=useremail))
                    username = usr.username
                    email = usr.email
                    userId = usr.user_id
                except User.DoesNotExist:
                    raise NotFoundException("username/email provided not found", 404)
                response = sendPasswordResetCodeMailToUser(email, username, userId)
                # sessionObj = {
                #     # 'email': user.email,
                #     # 'username': user.username,
                #     # 'userId': user.user_id,
                #     'secret': response['secretcode'],
                #     'verified': False
                # }
                # sessionId = 'reset'+str(user.user_id)
                info.context.session[response['secretcode']]=False
                if response['code'] == 202:
                    return responseResetPasswordType(response['message'], response['secretcode'])
                else:
                    raise NoContentException("email not sent to the provided email")
            else:
                raise BadRequestException("invalid request; username/email provided is empty", 400)
        else:
            raise BadRequestException("invalid request; username/email provided is invalid", 400)

 #ResendResetPasswordCode
    # def resolve_resendResetPasswordCode(self, info, **kwargs):
        # useremail = kwargs.get('email')
        # if useremail is not None:
        #     pass
        # else:
        #     raise BadRequestException("email provided is invalid", 400)
        # response = {}
        # # if info.context.session['reset'+str(user_id)] is not None:
        # #     user = info.context.session['reset'+str(user_id)] 
        # if email is not None:
        #     if email and email.strip():
        #         user = User.objects.using('default').get(Q(email__icontains=useremail)|Q(username__icontains=useremail))
        #         response = sendPasswordResetCodeMailToUser(user.email, user.username, user.user_id)
        #         # sessionObj = {
        #         #     'email': user.email,
        #         #     'username': user.username,
        #         #     'userId': user.user_id,
        #         #     'secret': response['secretcode']
        #         # }
        #         # sessionId = 'reset'+str(user.user_id)
        #         # info.context.session[response['secretcode']]=sessionObj
        #         if response['code'] == 202:
        #             return responseResetPasswordType(response['message'], response['secretcode'])
        #         else:
        #             raise NoContentException("email not sent to the provided email")
        #     else:
        #         raise BadRequestException("email provided is empty", 400)
        # else:
        #     raise BadRequestException("email provided is invalid", 400)

 #Verify reset Password Code
    def resolve_verifyresetpasswordcode(self, info, **kwargs):
        code = kwargs.get('code')
        token = kwargs.get('token')
        if token is not None:
            pass
        else:
            raise BadRequestException("invalid request; token provided is invalid", 400)
        # base32secret = pyotp.random_base32()
        sessionObj = info.context.session[token]
        # base32secret = session['secret']
        
        totp = pyotp.TOTP(token, interval=300)
        # totp = pyotp.TOTP("base32secret3232", interval=60)
        if code is not None:
            # print(code)
            # print(type(code))
            response = totp.verify(str(code))

            # print(response)
            if response:
                info.context.session[token] = True
                return stringType(str("successful verified the code"))
            else:
                raise AuthorizationException("code provided is not authorized", 401)
        else:
            raise BadRequestException("invalid request; code provided is invalid", 400)




