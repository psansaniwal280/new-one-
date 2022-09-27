from .errors import NotFoundException, BadRequestException, NoContentException, ConflictException, AuthorizationException
from .standardizemethods import standardize_phonenumber
from ..models import User
import hashlib, binascii, os
from .standardizemethods import encrypt_password, decrypt_password
from django.db.models import Q

def authenticateLogin(email, password):
    if email is not None:
        pass
    else:
        raise BadRequestException("Invalid Request; email provided is invalid", 400)
    if password is not None:
        pass
    else:
        raise BadRequestException("Invalid Request; password provided is invalid", 400)

    try:
        user={}
        user = User.objects.using('default').get(Q(email=email) or Q(username = email))
        # for userobj in userAll:
        #     if userobj['email'] == email or userobj['username'] == email:
        #         user = User.objects.using('default').get(user_id = userobj['user_id'])
        if user and decrypt_password(user.password)==password:
            # if request.session['username']== user.username:
            #     raise AuthorizationException("already logged in")
            # else:
            #     request.session['username'] = user.username
            return user
    except User.DoesNotExist:
        raise NotFoundException("username provided does not exists", 404)