import math
from django.db.models import Q
from math import radians, cos, sin, asin, sqrt
import cryptocode

#This Functions is used to hash password when creating a new user.
'''
    This function hash a password string from the user. This function actually does multiple things; it doesn’t just hash the password.The first thing it does is generate some random 
    salt that should be added to the password. That’s just the sha256 hash of some random bytes read from os.urandom . It then extracts a string representation of the hashed salt as a 
    set of hexadecimal numbers ( hexdigest).The salt is then provided to pbkdf2_hmac together with the password itself to hash the password in a randomized way. As pbkdf2_hmac  requires bytes as its 
    input, the two strings (password and salt) are previously encoded in pure bytes. The salt is encoded as plain ASCII, as the hexadecimal representation of a hash will only contain the 0-9 and A-F 
    characters. While the password is encoded as utf-8 , it could contain any character. (Is there anyone with emojis in their passwords?). The resulting pbkdf2 is a bunch of bytes, as you want to 
    store it into a database; you use binascii.hexlify  to convert the bunch of bytes into their hexadecimal representation in a string format.  Hexlify is a convenient way to convert bytes to 
    strings without losing data. It just prints all the bytes as two hexadecimal digits, so the resulting data will be twice as big as the original data, but apart from this, it’s exactly the same
    as the converted data. In the end, the function joins together the hash with its salt. As you know that the hexdigest of a sha256  hash (the salt) is always 64 characters long, by joining them
    together, you can grab back the salt by reading the first 64 characters of the resulting string.
'''
def encrypt_password(password):
    """encrypting password for storing."""
    return cryptocode.encrypt(password, "mypassword")

def decrypt_password(password):
    """decrypting password for storing."""
    return cryptocode.decrypt(password, "mypassword")

def standardize_phonenumber(phoneNumber):
    replaceChar = "()- "
    for char in replaceChar:
        phoneNumber = phoneNumber.replace(char, "")
    return int(phoneNumber,16)

def standardize_roundOf(value):
    if math.modf(value)[0] > 0.5:
        roundvalue=math.ceil(value)
    else:
        roundvalue=math.floor(value)
    return roundvalue   

def encrypt_email(email):
    """encrypting password for storing."""
    return cryptocode.encrypt(str(email), "myemail")

def decrypt_email(email):
    """decrypting password for storing."""
    return cryptocode.decrypt(str(email), "myemail")

def encrypt_username(username):
    """encrypting password for storing."""
    return cryptocode.encrypt(str(username), "myusername")

def decrypt_username(username):
    """decrypting password for storing."""
    return cryptocode.decrypt(str(username), "myusername")   

