from ssl import create_default_context
import graphene
from .userAccountType import *
from app.schemas.userSchema.userType import UserType
from app.utilities.errors import *
from app.models import *
from datetime import datetime, timezone
import datetime
from django.db.models import Max, Avg
from app.utilities.authentication import authenticateLogin
from django.contrib.sessions.backends.db import SessionStore
from graphql_jwt.utils import jwt_encode, jwt_payload
from app.utilities.redis import get_routes_from_api, get_routes_from_cache, set_routes_to_cache, redis_connect, delete_routes_from_cache, get_hashmap_from_cache, set_hashmap_to_cache, delete_hashmap_from_cache
from app.utilities.cache_lru import LRUCache
import graphql_jwt
from app.utilities.sendMail import *
from app.utilities.standardizemethods import *
from app.utilities.toBigInt import BigInt
from app import models
from validate_email_address import validate_email


"""
    Login User
"""
class userType(graphene.InputObjectType):
    userId = graphene.Argument(BigInt)
    username = graphene.String()
    email = graphene.String()
    name = graphene.String()

class LoginUserMutation(graphene.Mutation):
    user = graphene.Field(UserType)
    message = graphene.String()
    #token = graphene.String()
    # user = userType()
    # verification_prompt = graphene.String()

    class Arguments:
        username = graphene.String()
        password = graphene.String()
        

    def mutate(self, info, username, password):
        if username is not None:
            pass
        else:
            raise BadRequestException("invalid request; email provided is invalid", 400)
        if password is not None:
            pass
        else:
            raise BadRequestException("invalid request; password provided is invalid", 400)
        
        
        s = SessionStore()
        
        user = authenticateLogin(email=username, password=password)
        
        error_message = 'username or password provided is not authorized to login'
        success_message = "user provided logged in successfully"
        verification_error = 'conflict in request; provided email is not verified'
        if user is not None:
            try:
                userToken = UserToken.objects.using('default').get(user_id=user.user_id)
            except UserToken.DoesNotExist:
                userToken = UserToken.objects.create(
                    token = UserToken.objects.count()+1, 
                    user_id=user.user_id,
                    created_on = datetime.datetime.now(),
                    modified_on = datetime.datetime.now(),
                    created_by = user.user_id
                    
                    )
            user.last_login = datetime.datetime.now()
            user.save()
            userTokenPayload = {
                'userId': user.user_id,
                'username': user.username,
                'recommendedPosts': []
            }
            # payload = jwt_payload(userTokenPayload)
            token = jwt_encode(userTokenPayload)
            token = str(token)
            if user.is_active:
                userToken.token = token
                
                #Session login
                user_session = {
                    'username': user.username,
                    'userId': user.user_id,
                    'avatar': user.avatar,
                    'token': token,
                    'history': {}
                }
                # if s.SessionStore(session_key=):
                #     request.user.session_key
                # else:
                user_id = str(user.user_id)
                info.context.session[user_id] = {}
                if info.context.session[user_id] != {}:
                    raise AuthorizationException("you are already logged in", 401)
                else:
                    info.context.session[user_id] = user_session
                    
                # s.create()
                # s['user_info'] = user_session
                # s.set_expiry(None)
                # print(s.get_expiry_date())
                # print(s.keys())
                # print(s.session_key)

                userToken.save()
                client = redis_connect()
                cache = set_routes_to_cache(client, user.user_id, token)
                key  = str(user.user_id)+"_search_history"
                # print(get_hashmap_from_cache(client, key))
                if get_hashmap_from_cache(client, key):
                    search_cache = get_hashmap_from_cache(client, key)
                else:
                    search_history_cache = LRUCache(35)
                    # search_history_cache.put()
                    search_cache = set_hashmap_to_cache(client, key, search_history_cache)
                if cache :
                    return LoginUserMutation(user = user, message=success_message)
            else:
                raise AuthorizationException(verification_error, 409)
        else:
            raise AuthorizationException(error_message, 401)

    
'''

Register User 
'''
class CreateUserMutation(graphene.Mutation):
    message = graphene.String()
    token = graphene.String()
    class Arguments:
        email = graphene.String()
        password =  graphene.String()
        username = graphene.String() 
        name = graphene.String()
        genderId = graphene.Int()

    def mutate(root, info, **kwargs):
        email = kwargs.get('email')
        password = kwargs.get('password')
        username = kwargs.get('username')
        name = kwargs.get('name')
        genderId = kwargs.get('genderId')

        # #upload the media into the S3 bucket
        # aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
        # folder_name = "user-profile-media/"
        # file_name = "user_profile_"+str(user_data.user_id)
        # media_link = aws_link+folder_name+file_name
        # success_upload = upload_to_aws(user_data.avatar, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
        # userid = int("20210001")+User.objects.count()
        # print(success_upload)
        # print(media_link)
        
        #add to the post model with all the details of the post.
        # if not success_upload:
        #     media_link = ""
        if email is not None:
            if email and email.strip():
                isValid = validate_email(email)
                isExists = validate_email(email, verify=True)
                if not isValid:
                    raise BadRequestException("invalid request; email provided is invalid", 400)
                elif not isExists:
                    raise BadRequestException("invalid request; email provided is does not exist", 400)
            else:
                raise BadRequestException("invalid request; email provided is empty", 400)
        else:
            raise BadRequestException("invalid request; email provided is invalid", 400)
        if password is not None:
            if password and password.strip():
                pass
            else:
                raise BadRequestException("invalid request; password provided is empty", 400)
        else:
            raise BadRequestException("invalid request; password provided is invalid", 400)
        if username is not None:
            if username and username.strip():
                if any(ele.isupper() for ele in username):
                    username = username.lower()
                else:
                    pass
            else:
                raise BadRequestException("invalid request; username provided is empty", 400)
        else:
            raise BadRequestException("invalid request; username provided is invalid", 400)
        if name is not None:
            if name and name.strip():
                pass
            else:
                raise BadRequestException("invalid request; name provided is empty", 400)
        else:
            raise BadRequestException("invalid request; name provided is invalid", 400)

        try:
            usermails = User.objects.using('default').values_list('email', flat=True)
            if email in usermails:
                raise BadRequestException("conflict in request; email provided is already in use", 409)
        except User.DoesNotExist:
            pass
        try:
            usernames = User.objects.using('default').values_list('username', flat=True)
            if username in usernames:
                raise BadRequestException("conflict in request; username provided is already in use", 409)
        except User.DoesNotExist:
            pass
        # last_user_id = PostLike.objects.using('default').all().aggregate(Max('user_id'))
        # lastUserId = last_user_id['user_id__max']+1 if last_user_id['user_id__max'] else 1
        user = models.User.objects.create(
            # user_id = lastUserId,
            email = email,
            password = encrypt_password(password),
            username = username,
            is_active = False,
            created_on = datetime.datetime.now(timezone.utc),
            modified_on = datetime.datetime.now(timezone.utc),
            user_status_id = 1,
            level = 1,
            access_failed_count = 0
            )
    
        user.save()
        # if avatar is not None:
        #     media = models.MediaUser.create(
        #         media_user_id=MediaUser.objects.count()+1,
        #         url="media_link"
        #     )
        #     media.save()
        #add to user profile table as well.
        if user.user_id is not None:
            # profile_number = "2021_"+str(UserProfile.objects.count()+1)
           
            profile = models.UserProfile.objects.create(
                user_id = user.user_id, 
                gender_id = genderId,
                created_by = user.user_id,
                created_on = datetime.datetime.now(timezone.utc),
                modified_on = datetime.datetime.now(timezone.utc),

            )
        # Send mail for verification
        response = sendMailToUser(name, username, email)
        # userPayload = jwt_payload(user)
        # userToken = jwt_encode(userPayload)
        # token = UserToken.objects.create(
        #     user_id = user.userId,
        #     token = userToken
        # )

        # token.save()
        
        profile.save()
        return CreateUserMutation(message=str(response['message']), token=response['token'])



'''
Reset Password
'''
class ResetPasswordMutation(graphene.Mutation):
    message = graphene.String()

    class Arguments():
        userId = graphene.Int()
        password = graphene.String()
        token = graphene.String()

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        password = kwargs.get('password')
        token = kwargs.get('token')
        sessionObj = ''
        sessionObj = info.context.session[token]
       
        
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not provided", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if password is not None:
            if password and password.strip():
                pass
            else:
                raise BadRequestException("invalid request; password provided is empty", 400)
        else:
            raise BadRequestException("invalid request; password provided is invalid", 400)
        if sessionObj:
            pass
        else:
            raise AuthorizationException("conflict in request; password code is not verified")
        
        # user = User.objects.using('default').get(user_id=userId)
        user.password = encrypt_password(password)
        user.save()
        del info.context.session[token]
        return ResetPasswordMutation(message='successfully updated reset the password')


"""
    On Application Startup
"""
# class StartUpMutation(graphene.Mutation):
    #class Arguments:
        #pass
    #def mutate:
        #pass
        # def connection(WebSocket):
        #     """
        #         This is the function which should be initaited when you pull a message.
        #     """
       

class Mutation(graphene.ObjectType):
    # on_opening = StartUpMutation.Field()
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    revoke_token = graphql_jwt.Revoke.Field()
    login = LoginUserMutation.Field()
    reset_password = ResetPasswordMutation.Field()
    register_user = CreateUserMutation.Field()      
