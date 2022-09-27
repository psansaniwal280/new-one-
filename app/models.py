import datetime
from django.db import models
from s3direct.fields import S3DirectField
from graphene_file_upload.scalars import Upload
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser, AbstractBaseUser
from .utilities.standardizemethods import *


class DemoRouter:

    def db_for_read(self, model, **hints):
        """
        Attempts to read user models go to users_db.
        """
        if model._meta.app_label == 'default_db':
            return 'default'
        elif model._meta.app_label == 'payments_db':
            return 'payments'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write user models go to users_db.
        """
        if model._meta.app_label == 'default_db':
            return 'default'
        elif model._meta.app_label == 'payments_db':
            return 'payments'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the user app is involved.
        """
        if obj1._meta.app_label == 'default_db' or \
                obj2._meta.app_label == 'default_db':
            return True
        if obj1._meta.app_label == 'payments_db' or \
                obj2._meta.app_label == 'payments_db':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth app only appears in the 'users_db'
        database.
        """
        if app_label == 'default_db':
            return db == 'default'
        if app_label == 'payments_db':
            return db == 'payments'
        return None

class EncryptEmailField(models.CharField):
    description = "Encrypted email"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 255
        kwargs['null'] = False
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        del kwargs["null"]
        return name, path, args, kwargs

    def get_prep_value(self, value):
        return encrypt_email(value)

    def from_db_value(self, value, expression, connection):
        key ="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        if key not in value:
            return value
        else:
            return decrypt_email(value)

    def to_python(self, value):
        if isinstance(value, User):
            return value
        if value is None:
            return value

        return decrypt_email(value)


class EncryptUsernameField(models.CharField):
    description = "Encrypted username"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 255
        kwargs['null'] = False
        kwargs['unique'] = True
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        del kwargs["unique"]
        del kwargs["null"]
        return name, path, args, kwargs

    def get_prep_value(self, value):
        print(value)
        return encrypt_username(value)

    def from_db_value(self, value, expression, connection):
        key ="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
        if key not in value:
            return value
        else:
            return decrypt_username(value)

    def to_python(self, value):
        if isinstance(value, User):
            return value
        if value is None:
            return value

        return decrypt_username(value)


class AddressType(models.Model):
    address_type_id = models.BigAutoField(primary_key=True)
    address_type_name = models.CharField(max_length=255, null=False)
    address_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'address_type'

    app_label = 'default'


class Country(models.Model):
    country_id = models.BigAutoField(primary_key=True)
    country_name = models.CharField(max_length=255, null=False)
    country_code_two_char = models.CharField(max_length=2, null=False)
    country_code_three_char = models.CharField(max_length=3, null=False)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'country'

    app_label = 'default'


class PostDisinterested(models.Model):
    post_disinterested_id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey("Post", models.DO_NOTHING, null=False)
    user = models.ForeignKey("User", models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_disinterested'

    app_label = 'default'


class States(models.Model):
    state_id = models.BigAutoField(primary_key=True)
    country = models.ForeignKey(Country, models.DO_NOTHING, null=False)
    state_name = models.CharField(max_length=255, null=False)
    state_code = models.CharField(max_length=5, null=False)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'states'

    app_label = 'default'


class City(models.Model):
    city_id = models.BigAutoField(primary_key=True)
    state = models.ForeignKey(States, models.DO_NOTHING, null=False)
    city_name = models.CharField(max_length=255, null=False)
    latitude = models.DecimalField(max_digits=65535, decimal_places=65535, null=True, blank=True)
    longitude = models.DecimalField(max_digits=65535, decimal_places=65535, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'city'

    app_label = 'default'


class Address(models.Model):
    address_id = models.BigAutoField(primary_key=True)
    address_type = models.ForeignKey(AddressType, models.DO_NOTHING, null=False)
    street_address_line1 = models.CharField(max_length=50, null=True)
    street_address_line2 = models.CharField(max_length=50, null=True)
    zip_code = models.ForeignKey('ZipCode', models.DO_NOTHING, null=False)
    street_number = models.CharField(max_length=50, null=True)
    home_phone = models.CharField(max_length=50, null=True)
    landmark = models.CharField(max_length=250, null=True)
    mobile_phone = models.CharField(max_length=50, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)
    longitude = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    latitude = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    city = models.ForeignKey(City, models.DO_NOTHING, null=False)
    zip_code_0 = models.CharField(db_column='zip_code', max_length=20, blank=True, null=True)  # Field renamed because of name conflict.

    class Meta:
        managed = False
        db_table = 'address'

    app_label = 'default'


class Amenity(models.Model):
    amenity_id = models.BigAutoField(primary_key=True)
    amenity_name = models.CharField(max_length=255, null=False)
    amenity_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'amenity'

    app_label = 'default'


class AttachmentType(models.Model):
    attachment_type_id = models.BigAutoField(primary_key=True)
    attachment_type_name = models.CharField(max_length=255, null=False)
    attachment_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'attachment_type'

    app_label = 'default'


class Attachment(models.Model):
    attachment_id = models.BigAutoField(primary_key=True)
    attachment_type = models.ForeignKey(AttachmentType, models.DO_NOTHING)
    attachment_url = models.CharField(max_length=255, null=True, blank=True)
    attachment_url_name = models.CharField(max_length=255, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'attachment'

    app_label = 'default'


class BadgeType(models.Model):
    badge_type_id = models.IntegerField(primary_key=True)
    badge_type_name = models.CharField(max_length=255, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)
    badge_type_description = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'badge_type'

    app_label = 'default'


class Badge(models.Model):
    badge_id = models.IntegerField(primary_key=True)
    badge_name = models.CharField(max_length=255, null=False)
    badge_description = models.CharField(max_length=500, null=True)
    value = models.IntegerField(null=False)
    badge_type = models.ForeignKey(BadgeType, models.DO_NOTHING)
    image = models.CharField(max_length=255, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'badge'

    app_label = 'default'


class BookingStatus(models.Model):
    booking_status_id = models.BigAutoField(primary_key=True)
    booking_status_name = models.CharField(max_length=255, null=False)
    booking_status_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'booking_status'

    app_label = 'default'


class CancellationPolicy(models.Model):
    cancellation_policy_id = models.BigAutoField(primary_key=True)
    cancellation_policy_name = models.CharField(max_length=255, null=False)
    cancellation_policy_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'cancellation_policy'

    app_label = 'default'

class AccessRestriction(models.Model):
    access_restriction_id = models.BigAutoField(primary_key=True)
    access_restriction_name = models.CharField(max_length=255, null=False)
    access_restriction_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'access_restriction'

    app_label = 'default'


class Venue(models.Model):
    venue_id = models.BigAutoField(primary_key=True)
    is_external = models.BooleanField(null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue'

    app_label = 'default'


class UserStatus(models.Model):
    user_status_id = models.BigAutoField(primary_key=True)
    user_status_name = models.CharField(max_length=255, null=False, unique=True)
    user_status_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_status'

    app_label = 'default'


class User(AbstractUser):
    user_id = models.BigAutoField(primary_key=True)
    email = EncryptEmailField()
    password = models.CharField(max_length=255, null=False)
    username = EncryptUsernameField()
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False, null=False)
    level = models.IntegerField(null=False, default=1)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    avatar = models.CharField(max_length=255, blank=True, null=True)
    DOB = models.DateField(db_column='DOB', blank=True, null=True)
    user_status = models.ForeignKey(UserStatus, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)
    two_factor_enabled = models.BooleanField(default=False)
    lockout_end = models.DateTimeField(blank=True, null=True)
    lockout_enabled = models.BooleanField(default=False)
    access_failed_count = models.IntegerField(default=0)

    REQUIRED_FIELDS=('user_id',)

    USERNAME_FIELD = 'username'

    class Meta:
        # managed= True
        db_table = 'user'

    app_label = 'default'


class ChatThread(models.Model):
    chat_thread_id = models.BigAutoField(primary_key=True)
    is_approved = models.BooleanField(null=False)
    avatar = models.CharField(max_length=255, null=True)
    chat_thread_name = models.CharField(max_length=255, null=True)
    is_group = models.BooleanField(default=False, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'chat_thread'

    app_label = 'default'


class ChatThreadAdmin(models.Model):
    chat_thread_admin_id = models.BigAutoField(primary_key=True)
    chat_thread = models.ForeignKey(ChatThread, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'chat_thread_admin'

    app_label = 'default'


class ChatThreadParticipant(models.Model):
    chat_thread_participant_id = models.BigAutoField(primary_key=True)
    chat_thread = models.ForeignKey(ChatThread, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'chat_thread_participant'

    app_label = 'default'


class ChatDeleteThread(models.Model):
    chat_delete_thread_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    chat_thread = models.ForeignKey(ChatThread, models.DO_NOTHING)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'chat_delete_thread'

    app_label = 'default'


class ShareType(models.Model):
    share_type_id = models.BigAutoField(primary_key=True)
    share_type_name = models.CharField(max_length=255, null=False)
    share_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'share_type'

    app_label = 'default'


class ChatMessage(models.Model):
    chat_message_id = models.BigAutoField(primary_key=True)
    is_removed = models.BooleanField(null=False)
    text = models.TextField(null=True)
    sender = models.ForeignKey(User, models.DO_NOTHING, related_name='auth_user_id')
    chat_thread = models.ForeignKey(ChatThread, models.DO_NOTHING, related_name='recipient_user_id', null=False)
    shared = models.ForeignKey('Shared', models.DO_NOTHING, null=True)
    share_type = models.ForeignKey(ShareType, models.DO_NOTHING, null=True)
    attachment = models.ForeignKey(Attachment, models.DO_NOTHING, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'chat_message'

    app_label = 'default'


class ChatMessageReactionType(models.Model):
    chat_message_reaction_type_id = models.BigAutoField(primary_key=True)
    chat_message_reaction_type_name = models.CharField(max_length=255, null=False)
    chat_message_reaction_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'chat_message_reaction_type'

    app_label = 'default'


class ChatMessageReaction(models.Model):
    chat_message_reaction_id = models.BigAutoField(primary_key=True)
    chat_message = models.ForeignKey(ChatMessage, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    chat_message_reaction_type = models.ForeignKey(ChatMessageReactionType, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'chat_message_reaction'

    app_label = 'default'


class ChatMessageRecipient(models.Model):
    chat_message_recipient_id = models.BigAutoField(primary_key=True)
    chat_message = models.ForeignKey(ChatMessage, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    is_read = models.BooleanField(default=False, null=False)
    read_on = models.DateTimeField(null=True, default=datetime.datetime.now())
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'chat_message_recipient'

    app_label = 'default'


class Device(models.Model):
    device_id = models.BigAutoField(primary_key=True)
    uuid = models.TextField(db_column='UUID', null=False)  # Field name made lowercase. This field type is a guess.
    os_name = models.CharField(max_length=255, null=False)
    os_version = models.CharField(max_length=255, null=False)
    max_memory = models.BigIntegerField(null=False)
    available_memory = models.BigIntegerField(null=False)
    is_camera = models.BooleanField(null=False)
    is_earphone_connected = models.BooleanField(null=False)
    is_airplane_mode = models.BooleanField(null=False)
    battery_status = models.BigIntegerField(blank=True, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)
    language_preference = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'device'

    app_label = 'default'


# class ExperienceCategory(models.Model):
#     experience_category_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=255, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)

#     class Meta:
#         managed = False
#         db_table = 'experience_category'

#     app_label = 'default'


# class ExperienceSubcategory(models.Model):
#     experience_subcategory_id = models.BigAutoField(primary_key=True)
#     experience_category = models.ForeignKey(ExperienceCategory, models.DO_NOTHING, null=False)
#     name = models.CharField(max_length=255, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)

#     class Meta:
#         managed = False
#         db_table = 'experience_subcategory'

#     app_label = 'default'


# class ExploreCategory(models.Model):
#     explore_category_id = models.BigAutoField(primary_key=True)
#     thumbnail = models.CharField(max_length=512, null=False)
#     explore_category_name = models.CharField(max_length=256, null=False)
#     explore_category_description =  models.CharField(max_length=500, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)

#     class Meta:
#         managed = False
#         db_table = 'explore_category'
#     app_label = 'default'


# class LocationType(models.Model):
#     location_type_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=255, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'location_type'
#
#     app_label = 'default'


# class Location(models.Model):
#     location_id = models.BigAutoField(primary_key=True)
#     city = models.CharField(max_length=255, null=False)
#     street = models.CharField(max_length=255, null=True)
#     street_two = models.CharField(max_length=255, null=True)
#     state = models.CharField(max_length=255, null=True)
#     country = models.CharField(max_length=255, null=False)
#     zipcode = models.BigIntegerField(null=True)
#     latitude = models.DecimalField(max_digits=65535, decimal_places=65535)
#     longitude = models.DecimalField(max_digits=65535, decimal_places=65535)
#     apt_no = models.CharField(max_length=255, null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'location'
#
#     app_label = 'default'


# class MediaItinerary(models.Model):
#     media_itinerary_id = models.BigAutoField(primary_key=True)
#     media_itinerary_url = models.CharField(max_length=255, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'media_itinerary'
#
#     app_label = 'default'


class MediaPost(models.Model):
    media_post_id = models.BigAutoField(primary_key=True)
    media_post_url = models.TextField(null=False)
    media_post_raw_url = models.TextField(null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'media_post'

    app_label = 'default'

#
# class MediaUser(models.Model):
#     media_user_id = models.BigAutoField(primary_key=True)
#     media_user_url = models.CharField(max_length=255, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'media_user'
#
#     app_label = 'default'


class MediaVenueType(models.Model):
    media_venue_type_id = models.BigAutoField(primary_key=True)
    media_venue_type_name = models.CharField(max_length=255, null=False)
    media_venue_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'media_venue_type'

    app_label = 'default'


# class MediaVenue(models.Model):
#     media_venue_id = models.BigAutoField(primary_key=True)
#     media_venue_url = models.CharField(max_length=255, null=False)
#     media_venue_type = models.ForeignKey(MediaVenueType, models.DO_NOTHING, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'media_venue'
#
#     app_label = 'default'


class Post(models.Model):
    post_id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False)
    user_rating = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    is_verified_booking = models.BooleanField(null=False, default=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    post_description = models.CharField(max_length=500, blank=True, null=True)
    venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)
    thumbnail = models.CharField(max_length=255, null=False)
    media_post = models.ForeignKey(MediaPost, models.DO_NOTHING, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post'

    app_label = 'default'


class PostComment(models.Model):
    post_comment_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    post = models.ForeignKey(Post, models.DO_NOTHING, null=False)
    comment = models.CharField(max_length=255, null=False)
    comment_reply = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_comment'

    app_label = 'default'


class PostCommentLike(models.Model):
    post_comment_like_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    post_comment = models.ForeignKey(PostComment, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_comment_like'

    app_label = 'default'


# class VenuePrice(models.Model):
#     venue_price_id = models.BigAutoField(primary_key=True)
#     venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)
#     venue_base_price = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
#     venue_discount_value = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
#     venue_discount_percent = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
#     valid_from = models.DateField(null=False)
#     valid_to = models.DateField(null=False)
#     start_time = models.TimeField(null=True)
#     end_time = models.TimeField(null=True)
#     is_active = models.BooleanField(default=True, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'venue_price'
#
#     app_label = 'default'


class PostCommentMention(models.Model):
    post_comment_mention_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    post_comment = models.ForeignKey(PostComment, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_comment_mention'

    app_label = 'default'


class Tag(models.Model):
    tag_id = models.BigAutoField(primary_key=True)
    tag_name = models.CharField(max_length=255, null=False)
    tag_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'tag'

    app_label = 'default'


class Shared(models.Model):
    shared_id = models.BigAutoField(primary_key=True)
    sender_user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    post = models.ForeignKey(Post, models.DO_NOTHING, null=True)
    venue = models.ForeignKey(Venue, models.DO_NOTHING, null=True)
    is_active = models.BooleanField(default=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'shared'

    app_label = 'default'


class PostTag(models.Model):
    post_tag_id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, models.DO_NOTHING, null=False)
    tag = models.ForeignKey(Tag, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_tag'

    app_label = 'default'


class PostCommentTag(models.Model):
    post_comment_tag_id = models.BigAutoField(primary_key=True)
    post_comment = models.ForeignKey(PostComment, models.DO_NOTHING, null=False)
    tag = models.ForeignKey(Tag, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_comment_tag'

    app_label = 'default'


class PostLike(models.Model):
    post_like_id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_like'

    app_label = 'default'


class PostMention(models.Model):
    post_mention_id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_mention'

    app_label = 'default'


class PostSaved(models.Model):
    post_saved_id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_saved'

    app_label = 'default'


# class PostVenue(models.Model):
#     post_venue_id = models.BigAutoField(primary_key=True)
#     venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)
#     post = models.ForeignKey(Post, models.DO_NOTHING, blank=True, null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'post_venue'
#
#     app_label = 'default'

class ViewSource(models.Model):
    view_source_id = models.BigAutoField(primary_key=True)
    view_source_name = models.CharField(max_length=255)
    view_source_description = models.CharField(max_length=500)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)
    class Meta:
        managed = False
        db_table = 'view_source'

class PostView(models.Model):
    post_view_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    post = models.ForeignKey(Post, models.DO_NOTHING, blank=True, null=True)
    video_start_time = models.DateTimeField(null=True)
    video_end_time = models.DateTimeField(null=True)
    video_duration = models.IntegerField(null=True, default=0)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)
    view_source = models.ForeignKey(ViewSource, models.DO_NOTHING, null=False)

    class Meta:
        managed = False
        db_table = 'post_view'


# class VenuePrice(models.Model):
#     venue_price_id = models.BigAutoField(primary_key=True)
#     venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)
#     venue_base_price = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
#     venue_discount_value = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
#     venue_discount_percent = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
#     valid_from = models.DateField(null=False)
#     valid_to = models.DateField(null=False)
#     start_time = models.TimeField(null=True)
#     end_time =  models.TimeField(null=True)
#     is_active = models.BooleanField(default=True, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)


#     class Meta:
#         managed = False
#         db_table = 'venue_price'
#     app_label = 'default'


# class ExperienceVenueAvailability(models.Model):
#     exp_venue_availability_id = models.BigAutoField(primary_key=True)
#     start_date = models.DateField(null=False)
#     end_date = models.DateField(null=False)
#     start_time = models.TimeField(null=True)
#     end_time = models.TimeField(null=True)
#     is_recurring = models.BooleanField()
#     associated_exp_venue_availability_id = models.BigIntegerField()
#     arrival_time = models.ForeignKey("ArrivalTime", models.DO_NOTHING, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#     venue_internal = models.ForeignKey("VenueInternal", models.DO_NOTHING, null=False)
#
#     class Meta:
#         managed = False
#         db_table = 'exp_venue_availability'
#
#     app_label = 'default'
#
#
# class ExperienceVenueOption(models.Model):
#     exp_venue_option_id = models.BigAutoField(primary_key=True)
#     venue_internal = models.ForeignKey("VenueInternal", models.DO_NOTHING, null=False)
#     exp_venue_option_name = models.CharField(max_length=255, null=False)
#     exp_venue_option_description = models.TextField()
#     per_group = models.BigIntegerField()
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'exp_venue_option'
#
#     app_label = 'default'
#
#
# class ExperienceVenueOptionPrice(models.Model):
#     exp_venue_option_price_id = models.BigAutoField(primary_key=True)
#     exp_venue_option = models.ForeignKey(ExperienceVenueOption, models.DO_NOTHING, null=False)
#     venue_base_price = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
#     venue_discount_value = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
#     venue_discount_percent = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
#     is_active = models.BooleanField(default=True, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'exp_venue_option_price'
#
#     app_label = 'default'
#

class ReportPostReason(models.Model):
    report_post_reason_id = models.BigAutoField(primary_key=True)
    report_post_reason_name = models.CharField(max_length=255, null=False)
    report_post_reason_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'report_post_reason'

    app_label = 'default'


class ReportPost(models.Model):
    report_post_id = models.BigAutoField(primary_key=True)
    report_post_reason = models.ForeignKey(ReportPostReason, models.DO_NOTHING, null=False)
    post = models.ForeignKey(Post, models.DO_NOTHING, null=False)
    reporter = models.ForeignKey(User, models.DO_NOTHING, null=False)
    count = models.IntegerField(null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'report_post'

    app_label = 'default'


class ReportUserReason(models.Model):
    report_user_reason_id = models.BigAutoField(primary_key=True)
    report_user_reason_name = models.CharField(max_length=255, null=False)
    report_user_reason_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'report_user_reason'

    app_label = 'default'


class ReportUser(models.Model):
    report_user_id = models.BigAutoField(primary_key=True)
    reporter = models.ForeignKey(User, models.DO_NOTHING, related_name='reporter_user', null=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    report_user_reason = models.ForeignKey(ReportUserReason, models.DO_NOTHING, null=False)
    count = models.IntegerField(null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'report_user'

    app_label = 'default'


# class StayType(models.Model):
#     stay_type_id = models.BigAutoField(primary_key=True)
#     stay_type_name = models.CharField(max_length=255, null=False)
#     stay_type_description = models.CharField(max_length=500, null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'stay_type'
#
#     app_label = 'default'


# class TransportationType(models.Model):
#     transportation_type_id = models.BigAutoField(primary_key=True)
#     name = models.CharField(max_length=255, null=False)
#     capacity = models.IntegerField(blank=True, null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'transportation_type'
#
#     app_label = 'default'


# class TripBooked(models.Model):
#     trip_booked_id = models.IntegerField(primary_key=True)
#     name = models.CharField(max_length=255)
#     booked_at = models.DateTimeField()
#     start_date = models.DateTimeField()
#     end_date = models.DateTimeField()
#     price = models.DecimalField(max_digits=65535, decimal_places=65535)
#     venue = models.ForeignKey('Venue', models.DO_NOTHING)
#
#     class Meta:
#         managed = False
#         db_table = 'trip_booked'
#
#     app_label = 'default'


class UserBadge(models.Model):
    user_badge_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    badge = models.ForeignKey(Badge, models.DO_NOTHING, null=False)
    date_earned = models.DateTimeField(blank=True, null=True)
    is_pinned = models.BooleanField(null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_badge'

    app_label = 'default'


class UserProfile(models.Model):
    profile_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    bio = models.CharField(max_length=255, blank=True, null=True)
    featured_video = models.CharField(max_length=255, blank=True, null=True)
    bio_link = models.CharField(max_length=255, blank=True, null=True)
    city = models.ForeignKey(City, models.DO_NOTHING, blank=True, null=True)
    user_profile_name = models.CharField(max_length=255, blank=True, null=True)
    gender = models.ForeignKey('Gender', models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_profile'

    app_label = 'default'


class UserBioMention(models.Model):
    user_bio_mention_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    user_profile = models.ForeignKey(UserProfile, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_bio_mention'

    app_label = 'default'


class UserBioTag(models.Model):
    user_bio_tag_id = models.BigAutoField(primary_key=True)
    tag = models.ForeignKey(Tag, models.DO_NOTHING, null=False)
    user_profile = models.ForeignKey(UserProfile, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_bio_tag'

    app_label = 'default'


class UserBlocked(models.Model):
    user_blocked_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, related_name='userId', null=False)
    block_user = models.ForeignKey(User, models.DO_NOTHING, related_name='blockUserId', null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_blocked'

    app_label = 'default'


class UserDevice(models.Model):
    user_device_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    device = models.ForeignKey(Device, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_device'

    app_label = 'default'


# class UserFollower(models.Model):
#     user_follower_id = models.BigAutoField(primary_key=True)
#     user = models.ForeignKey(User, models.DO_NOTHING, null=False)
#     follower_user = models.ForeignKey(User, models.DO_NOTHING, related_name='follower', null=True)
#     is_followed = models.BooleanField(default=True, null=False)
#     unfollowed_date = models.DateTimeField(null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)

#     class Meta:
#         managed = False
#         db_table = 'user_follower'

#     app_label = 'default'


class UserFollowing(models.Model):
    user_following_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    following_user = models.ForeignKey(User, models.DO_NOTHING, related_name='following', null=True)
    is_following = models.BooleanField(default=True, null=False)
    unfollowing_date = models.DateTimeField(null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_following'

    app_label = 'default'


class UserProfileTag(models.Model):
    user_profile_tag_id = models.AutoField(primary_key=True)
    user_profile_tag_name = models.CharField(max_length=255, null=False, unique=True)
    user_profile_tag_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_profile_tag'

    app_label = 'default'


# class UserProfileTagList(models.Model):
#     user_profile_tag_list_id = models.BigAutoField(primary_key=True)
#     user = models.ForeignKey(User, models.DO_NOTHING, null=False)
#     user_profile_tag_list = ArrayField(models.BigIntegerField(), blank=False, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)

#     class Meta:
#         managed = False
#         db_table = 'user_profile_tag_list'

#     app_label = 'default'


class UserSharedItinerary(models.Model):
    user_shared_itinerary_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    user_shared_itinerary_name = models.CharField(max_length=255, null=False)
    user_shared_itinerary_description = models.CharField(max_length=500, null=True)
    thumbnail = models.CharField(max_length=255, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_shared_itinerary'

    app_label = 'default'


class UserSharedItineraryMention(models.Model):
    user_shared_itinerary_mention_id = models.BigAutoField(primary_key=True)
    user_shared_itinerary = models.ForeignKey(UserSharedItinerary, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_shared_itinerary_mention'

    app_label = 'default'


class UserSharedItineraryPost(models.Model):
    user_shared_itinerary_post_id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, models.DO_NOTHING, null=False)
    user_shared_itinerary = models.ForeignKey(UserSharedItinerary, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_shared_itinerary_post'

    app_label = 'default'


class UserSharedItineraryTag(models.Model):
    user_shared_itinerary_tag_id = models.BigAutoField(primary_key=True)
    user_shared_itinerary = models.ForeignKey(UserSharedItinerary, models.DO_NOTHING, null=False)
    tag = models.ForeignKey(Tag, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_shared_itinerary_tag'

    app_label = 'default'


class UserTag(models.Model):
    user_tag_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    user_profile_tag = models.ForeignKey(UserProfileTag, models.DO_NOTHING, null=False)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_tag'

    app_label = 'default'


class UserToken(models.Model):
    user_token_id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField(null=False)
    token = models.CharField(max_length=255, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_token'

    app_label = 'default'


class VendorBusiness(models.Model):
    vendor_business_id = models.BigAutoField(primary_key=True)
    vendor_business_name = models.CharField(max_length=255, null=False)
    vendor_business_description = models.CharField(max_length=500, null=True)
    number = models.CharField(max_length=255, null=False, db_column='number')
    license_number = models.CharField(max_length=255, null=False)
    insurance_number = models.CharField(max_length=255, null=False)
    permit_title = models.CharField(max_length=255, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'vendor_business'

    app_label = 'default'


class VendorStatus(models.Model):
    vendor_status_id = models.BigAutoField(primary_key=True)
    vendor_status_name = models.CharField(max_length=255, null=False, unique=True)
    vendor_status_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'vendor_status'

    app_label = 'default'


class Vendor(models.Model):
    vendor_id = models.BigAutoField(primary_key=True)
    vendor_name = models.CharField(max_length=255, null=False)
    avatar = models.CharField(max_length=255, blank=True, null=True)
    vendor_url = models.CharField(max_length=255, blank=True, null=True)
    vendor_description = models.CharField(max_length=500, blank=True, null=True)
    vendor_business = models.ForeignKey(VendorBusiness, models.DO_NOTHING, blank=True, null=True)
    vendor_status = models.ForeignKey(VendorStatus, models.DO_NOTHING)
    address = models.ForeignKey(Address, models.DO_NOTHING)
    gender = models.ForeignKey('Gender', models.DO_NOTHING)
    dob = models.DateField(null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'vendor'

    app_label = 'default'


class VendorVenue(models.Model):
    vendor_venue_id = models.BigAutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, models.DO_NOTHING, null=False)
    venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'vendor_venue'

    app_label = 'default'


class VenueAmenity(models.Model):
    venue_amenity_id = models.BigAutoField(primary_key=True)
    amenity = models.ForeignKey(Amenity, models.DO_NOTHING, null=False)
    venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_amenity'

    app_label = 'default'

#
# class VenueExperienceOptionDetail(models.Model):
#     venue_experience_option_detail_id = models.BigAutoField(primary_key=True)
#     address_id = models.CharField(max_length=255, null=False)
#     minimum_age = models.BigIntegerField(null=False)
#     provided_with = ArrayField(models.CharField(max_length=255), null=False)
#     what_to_bring = ArrayField(models.CharField(max_length=255), null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'venue_experience_option_detail'
#
#     app_label = 'default'


# class VenueExperienceCategory(models.Model):
#     venue_experience_category_id = models.BigAutoField(primary_key=True)
#     experience_category = models.ForeignKey(ExperienceCategory, models.DO_NOTHING, null=False)
#     venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)

#     class Meta:
#         managed = False
#         db_table = 'venue_experience_category'

#     app_label = 'default'


class VenueType(models.Model):
    venue_type_id = models.BigAutoField(primary_key=True)
    venue_type_name = models.CharField(max_length=255, null=False)
    venue_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_type'

    app_label = 'default'


class Languages(models.Model):
    language_id = models.BigAutoField(primary_key=True)
    language_name = models.CharField(max_length=255, null=False)
    language_description = models.CharField(max_length=500, null=True, blank=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'languages'

    app_label = 'default'


class WhatToBring(models.Model):
    what_to_bring_id = models.BigAutoField(primary_key=True)
    what_to_bring_name = models.CharField(max_length=255, null=False, unique=True)
    what_to_bring_description = models.CharField(max_length=500, null=True, blank=True)
    venue_internal = models.ForeignKey('VenueInternal', models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'what_to_bring'

    app_label = 'default'


class WhatWeProvideCategory(models.Model):
    what_we_provide_category_id = models.BigAutoField(primary_key=True)
    what_we_provide_category_name = models.CharField(max_length=255, null=False)
    what_we_provide_category_description = models.CharField(max_length=500, null=True, blank=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'what_we_provide_category'

    app_label = 'default'


class WhatWeProvideOption(models.Model):
    what_we_provide_option_id = models.BigAutoField(primary_key=True)
    what_we_provide_category = models.ForeignKey(WhatWeProvideCategory, models.DO_NOTHING, null=False)
    what_we_provide_option_name = models.CharField(max_length=255, null=False, unique=True)
    what_we_provide_option_description = models.CharField(max_length=500, null=True, blank=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'what_we_provide_option'

    app_label = 'default'


class WhatWeProvide(models.Model):
    what_we_provide_id = models.BigAutoField(primary_key=True)
    what_we_provide_option = models.ForeignKey(WhatWeProvideOption, models.DO_NOTHING, null=False)
    venue_internal = models.ForeignKey('VenueInternal', models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'what_we_provide'

    app_label = 'default'


class VenueExternal(models.Model):
    venue_external_id = models.BigAutoField(primary_key=True)
    api_id = models.IntegerField(null=False)
    venue_external_name = models.CharField(max_length=255, null=False)
    venue_external_description = models.CharField(max_length=500, null=True)
    venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_external'

    app_label = 'default'


class VenueInternal(models.Model):
    venue_internal_id = models.BigAutoField(primary_key=True)
    venue_internal_name = models.CharField(max_length=255, null=False)
    venue_internal_description = models.TextField(null=False)
    venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)
    max_guests = models.IntegerField(null=True)
    address = models.ForeignKey(Address, models.DO_NOTHING, null=False)
    venue_type = models.ForeignKey(VenueType, models.DO_NOTHING, null=False)
    cancellation_policy = models.ForeignKey(CancellationPolicy, models.DO_NOTHING, null=True, blank=True)
    featured_video = models.CharField(max_length=255, null=True, blank=True)
    access_restriction = models.ForeignKey(AccessRestriction, models.DO_NOTHING, null=True, blank=True)
    age_restriction = models.ForeignKey('AgeRestriction', models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)
    venue_level = models.ForeignKey('VenueLevel', models.DO_NOTHING, blank=True, null=True)
    venue_category = models.ForeignKey('VenueCategory', models.DO_NOTHING)



    class Meta:
        managed = False
        db_table = 'venue_internal'

    app_label = 'default'


class VenueInternalImage(models.Model):
    venue_internal_image_id = models.BigAutoField(primary_key=True)
    venue_internal_image_url = models.CharField(max_length=255, null=False)
    venue_internal_image_name = models.CharField(max_length=255, null=True)
    venue_internal_image_description = models.CharField(max_length=516, null=True)
    venue_internal = models.ForeignKey(VenueInternal, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_internal_image'

    app_label = 'default'


# class Booking(models.Model):
#     booking_id = models.BigAutoField(primary_key=True)
#     start_date = models.DateField(null=False)
#     end_date = models.DateField(null=False)
#     start_time = models.TimeField(null=False)
#     end_time = models.TimeField(null=False)
#     is_recurring = models.BooleanField()
#     venue_internal = models.ForeignKey(VenueInternal, models.DO_NOTHING)
#     associated_booking_id = models.BigIntegerField(null=True)
#     is_multy_traveler = models.BooleanField(default=False)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'booking'
#
#     app_label = 'default'


class UserTrip(models.Model):
    user_trip_id = models.BigAutoField(primary_key=True)
    booking_purchase = models.ForeignKey('BookingPurchase', models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING)
    referred_post = models.ForeignKey(Post, models.DO_NOTHING, blank=True, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_trip'

    app_label = 'default'


class BlackoutDate(models.Model):
    blackout_date_id = models.BigAutoField(primary_key=True)
    exp_venue_availability = models.ForeignKey('ExpVenueAvailability', models.DO_NOTHING, blank=True, null=True)
    blackout_date_name = models.CharField(max_length=255, null=True)
    blackout_date_description = models.CharField(max_length=500, null=True)
    blackout_date_start_date = models.DateField(null=False)
    blackout_date_end_date = models.DateField(null=False)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'blackout_date'

    app_label = 'default'


# class BookingException(models.Model):
#     booking_exception_id = models.BigAutoField(primary_key=True)
#     is_rescheduled = models.BooleanField(null=True)
#     is_cancelled = models.BooleanField(null=True)
#     start_date = models.DateField(null=False)
#     end_date = models.DateField(null=False)
#     start_time = models.TimeField(null=False)
#     end_time = models.TimeField(null=False)
#     booking = models.ForeignKey(Booking, models.DO_NOTHING, null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'booking_exception'
#
#     app_label = 'default'


# class ExperienceVenuePatternType(models.Model):
#     exp_venue_pattern_type_id = models.BigAutoField(primary_key=True)
#     exp_venue_pattern_type_name = models.CharField(max_length=255, null=False)
#     exp_venue_pattern_type_description = models.CharField(max_length=500, null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'exp_venue_pattern_type'
#
#     app_label = 'default'
#
#
# class ExperienceVenuePattern(models.Model):
#     exp_venue_pattern_id = models.BigAutoField(primary_key=True)
#     exp_venue_pattern_type = models.ForeignKey(ExperienceVenuePatternType, models.DO_NOTHING, null=False)
#     exp_venue_availability = models.ForeignKey(ExperienceVenueAvailability, models.DO_NOTHING, null=False)
#     sepration_count = models.IntegerField(null=True)
#     max_num_of_occurence = models.IntegerField(null=True)
#     day_of_week = models.IntegerField(null=True)
#     week_of_month = models.IntegerField(null=True)
#     day_of_month = models.IntegerField(null=True)
#     month_of_year = models.IntegerField(null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'exp_venue_pattern'
#
#     app_label = 'default'


class BookingPurchase(models.Model):
    booking_purchase_id = models.BigAutoField(primary_key=True)
    exp_venue_availability_timeslot = models.ForeignKey('ExpVenueAvailabilityTimeslot', models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    num_of_people = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    base_price = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    price_pay = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    base_deal_amt = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
    deal_amt_pay = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
    base_tax_amt = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
    tax_amt_pay = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
    base_service_amt = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
    service_amt_pay = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
    base_total_amt = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    total_amt_pay = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    venue = models.ForeignKey(Venue, models.DO_NOTHING, null=False)

    class Meta:
        managed = False
        db_table = 'booking_purchase'

    app_label = 'default'


class TravelerRelationship(models.Model):
    traveler_relationship_id = models.BigAutoField(primary_key=True)
    traveler_relationship_name = models.CharField(max_length=255, null=False)
    traveler_relationship_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'traveler_relationship'

    app_label = 'default'


class Gender(models.Model):
    gender_id = models.BigAutoField(primary_key=True)
    gender_name = models.CharField(max_length=255, null=False)
    gender_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'gender'

    app_label = 'default'


class Traveler(models.Model):
    traveler_id = models.BigAutoField(primary_key=True)
    gender = models.ForeignKey(Gender, models.DO_NOTHING, null=False)
    first_name = models.CharField(max_length=100, null=True)
    middle_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    date_of_birth = models.DateField(null=False)
    traveler_relationship = models.ForeignKey(TravelerRelationship, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'traveler'

    app_label = 'default'

class BookingPurchaseTraveler(models.Model):
    booking_purchase_traveler_id = models.BigAutoField(primary_key=True)
    booking_purchase = models.ForeignKey(BookingPurchase, models.DO_NOTHING, null=False)
    traveler = models.ForeignKey(Traveler, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'booking_purchase_traveler'

    app_label = 'default'


class VenueMedia(models.Model):
    venue_media_id = models.BigAutoField(primary_key=True)
    venue_internal = models.ForeignKey(VenueInternal, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)
    media_venue_url = models.CharField(max_length=255)
    media_venue_type = models.ForeignKey(MediaVenueType, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'venue_media'

    app_label = 'default'


class VenueLanguages(models.Model):
    venue_language_id = models.BigAutoField(primary_key=True)
    venue_internal = models.ForeignKey(VenueInternal, models.DO_NOTHING, null=False)
    language = models.ForeignKey(Languages, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_languages'

    app_label = 'default'


class HolidayType(models.Model):
    holiday_type_id = models.BigAutoField(primary_key=True)
    holiday_type_name = models.CharField(max_length=255, null=False)
    holiday_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'holiday_type'

    app_label = 'default'


class Holiday(models.Model):
    holiday_id = models.BigAutoField(primary_key=True)
    holiday_type = models.ForeignKey(HolidayType, models.DO_NOTHING, null=False)
    holiday_name = models.CharField(max_length=255, null=False)
    holiday_description = models.CharField(max_length=500, null=True)
    holiday_start_date = models.DateField(null=False)
    holiday_end_date = models.DateField(null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'holiday'

    app_label = 'default'


class MembershipType(models.Model):
    membership_type_id = models.BigAutoField(primary_key=True)
    membership_type_name = models.CharField(max_length=255, null=False, unique=True)
    membership_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'membership_type'

    app_label = 'default'


class Member(models.Model):
    member_id = models.BigAutoField(primary_key=True)
    membership_type = models.ForeignKey(MembershipType, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    first_name = models.CharField(max_length=100, null=True)
    middle_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    date_of_birth = models.DateField(null=False)
    gender = models.ForeignKey(Gender, models.DO_NOTHING)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'member'

    app_label = 'default'


class MemberTransaction(models.Model):
    member_transaction_id = models.BigAutoField(primary_key=True)
    member = models.ForeignKey(Member, models.DO_NOTHING, null=False)
    point_before_transaction = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    point_after_transaction = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    point_added = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'member_transaction'

    app_label = 'default'


class Promo(models.Model):
    promo_id = models.BigAutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, models.DO_NOTHING, null=False)
    promo_name = models.CharField(max_length=255, null=False)
    promo_description = models.CharField(max_length=500, null=True)
    promo_code = models.CharField(max_length=20, null=False)
    promo_valid_from = models.DateTimeField(null=False)
    promo_valid_untill = models.DateTimeField(null=False)
    is_redeem_allowed = models.BooleanField(null=True)
    quantity = models.DecimalField(max_digits=65535, decimal_places=65535)
    remaining = models.DecimalField(max_digits=65535, decimal_places=65535)
    discount_value = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    discount_unit = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    minimum_order_value = models.DecimalField(max_digits=65535, decimal_places=65535)
    maximum_discount_amount = models.DecimalField(max_digits=65535, decimal_places=65535)
    maximum_discount_percent = models.DecimalField(max_digits=65535, decimal_places=65535)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'promo'

    app_label = 'default'


# class SearchTempleType(models.Model):
#     search_template_type_id = models.BigAutoField(primary_key=True)
#     search_template_type_name = models.CharField(max_length=255, null=False)
#     search_template_type_description = models.CharField(max_length=500, null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'search_template_type'
#
#     app_label = 'default'


class SharedRecipient(models.Model):
    shared_recipient_id = models.BigAutoField(primary_key=True)
    shared = models.ForeignKey(Shared, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'shared_recipient'

    app_label = 'default'


class VenueCategory(models.Model):
    venue_category_id = models.BigAutoField(primary_key=True)
    venue_type = models.ForeignKey(VenueType, models.DO_NOTHING, null=False)
    venue_category_name = models.CharField(max_length=255, null=False)
    venue_category_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_category'

    app_label = 'default'


class VenueSubCategory(models.Model):
    venue_subcategory_id = models.BigAutoField(primary_key=True)
    venue_category = models.ForeignKey(VenueCategory, models.DO_NOTHING, null=False)
    venue_subcategory_name = models.CharField(max_length=255, null=False, unique=True)
    venue_subcategory_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_subcategory'

    app_label = 'default'


class ZipCode(models.Model):
    zip_code_id = models.BigAutoField(primary_key=True)
    city = models.ForeignKey(City, models.DO_NOTHING, null=False)
    zip_code = models.CharField(max_length=20, null=False, unique=True)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'zip_code'

    app_label = 'default'


class AgeRestriction(models.Model):
    age_restriction_id = models.BigAutoField(primary_key=True)
    age_in_number = models.IntegerField(null=False)
    age_restriction_name = models.CharField(max_length=255, null=False)
    age_restriction_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'age_restriction'

    app_label = 'default'


class ArrivalTime(models.Model):
    arrival_time_id = models.BigAutoField(primary_key=True)
    arrival_time_name = models.CharField(max_length=255, null=False)
    arrival_time_description = models.CharField(max_length=500, null=True)
    time_in_minutes = models.BigIntegerField()
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'arrival_time'

    app_label = 'default'


class BookingCurrentStatus(models.Model):
    booking_current_status_id = models.BigAutoField(primary_key=True)
    booking_purchase = models.ForeignKey(BookingPurchase, models.DO_NOTHING, null=False)
    booking_status = models.ForeignKey(BookingStatus, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'booking_current_status'

    app_label = 'default'


class Role(models.Model):
    role_id = models.BigAutoField(primary_key=True)
    role_name = models.CharField(max_length=255, null=False)
    role_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'role'

    app_label = 'default'


class UserPromo(models.Model):
    user_promo_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    promo = models.ForeignKey(Promo, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_promo'

    app_label = 'default'


class UserPromoActivate(models.Model):
    user_promo_activate_id = models.BigAutoField(primary_key=True)
    user_promo = models.ForeignKey(UserPromo, models.DO_NOTHING, null=False)
    activated_promo_code = models.CharField(max_length=20, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_promo_activate'

    app_label = 'default'


class UserRole(models.Model):
    user_role_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    role = models.ForeignKey(Role, models.DO_NOTHING, null=False)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_role'

    app_label = 'default'


class VendorBusinessAttachment(models.Model):
    vendor_business_attachment_id = models.BigAutoField(primary_key=True)
    vendor_business = models.ForeignKey(VendorBusiness, models.DO_NOTHING, null=False)
    attachment = models.ForeignKey(Attachment, models.DO_NOTHING, null=False)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'vendor_business_attachment'

    app_label = 'default'


class VendorIdentity(models.Model):
    vendor_identity_id = models.BigAutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, models.DO_NOTHING, null=False)
    vendor_identity_url = models.CharField(max_length=255, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'vendor_identity'

    app_label = 'default'


class VenueStatus(models.Model):
    venue_status_id = models.BigAutoField(primary_key=True)
    venue_status_name = models.CharField(max_length=255, null=False, unique=True)
    venue_status_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_status'

    app_label = 'default'


class VenueCurrentStatus(models.Model):
    venue_current_status_id = models.BigAutoField(primary_key=True)
    venue_internal = models.ForeignKey(VenueInternal, models.DO_NOTHING, null=False)
    venue_status = models.ForeignKey(VenueStatus, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_current_status'

    app_label = 'default'


class VenuePromo(models.Model):
    venue_promo_id = models.BigAutoField(primary_key=True)
    venue_internal = models.ForeignKey(VenueInternal, models.DO_NOTHING)
    promo = models.ForeignKey(Promo, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_promo'

    app_label = 'default'


# class VenuePromoActivate(models.Model):
#     venue_promo_activate_id = models.BigAutoField(primary_key=True)
#     venue_promo = models.ForeignKey(VenuePromo, models.DO_NOTHING, null=False)
#     booking_purchase = models.ForeignKey(BookingPurchase, models.DO_NOTHING, null=False)
#     activated_promo_code = models.CharField(max_length=20, null=True)
#     created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
#     modified_on = models.DateTimeField(null=True)
#     created_by = models.BigIntegerField(null=False, default=16395)
#     modified_by = models.BigIntegerField(null=True)
#
#     class Meta:
#         managed = False
#         db_table = 'venue_promo_activate'
#
#     app_label = 'default'


class CommissionType(models.Model):
    commission_type_id = models.BigAutoField(primary_key=True)
    commission_type_name = models.CharField(max_length=255, unique=True, null=False)
    commission_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'commission_type'

    app_label = 'default'


class CommissionRate(models.Model):
    commission_rate_id = models.BigAutoField(primary_key=True)
    commission_rate_name = models.CharField(max_length=255, unique=True, null=False)
    commission_rate_description = models.CharField(max_length=500, null=True)
    commission_rate_percentage = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'commission_rate'

    app_label = 'default'


class CommissionEarned(models.Model):
    commissions_earned_id = models.BigAutoField(primary_key=True)
    booking_purchase = models.ForeignKey(BookingPurchase, models.DO_NOTHING, null=False)
    commission_type = models.ForeignKey(CommissionType, models.DO_NOTHING, null=False)
    commission_rate = models.ForeignKey(CommissionRate, models.DO_NOTHING, null=False)
    revenue_amount = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'commission_earned'

    app_label = 'default'


class PostVenueClick(models.Model):
    post_venue_click_id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, models.DO_NOTHING, null=False)
    user = models.ForeignKey(User, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'post_venue_click'

    app_label = 'default'


class ExpVenueAvailability(models.Model):
    exp_venue_availability_id = models.BigAutoField(primary_key=True)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=True)
    is_recurring = models.BooleanField(null=True)
    associated_exp_venue_availability_id = models.BigIntegerField(null=True)
    arrival_time = models.ForeignKey(ArrivalTime, models.DO_NOTHING, null=False)
    venue_internal = models.ForeignKey(VenueInternal, models.DO_NOTHING, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'exp_venue_availability'

    app_label = 'default'


class ExpVenueAvailabilityException(models.Model):
    exp_venue_availability_exception_id = models.BigAutoField(primary_key=True)
    exp_venue_availability_timeslot = models.ForeignKey('ExpVenueAvailabilityTimeslot', models.DO_NOTHING)
    is_rescheduled = models.BooleanField()
    is_cancelled = models.BooleanField()
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'exp_venue_availability_exception'

    app_label = 'default'


class ExpVenueOption(models.Model):
    exp_venue_option_id = models.BigAutoField(primary_key=True)
    venue_internal = models.ForeignKey(VenueInternal, models.DO_NOTHING, null=False)
    exp_venue_option_name = models.CharField(max_length=255, unique=True, null=False)
    exp_venue_option_description = models.CharField(max_length=500, null=True)
    per_group = models.BigIntegerField(null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'exp_venue_option'

    app_label = 'default'


class ExpVenueOptionPrice(models.Model):
    exp_venue_option_price_id = models.BigAutoField(primary_key=True)
    exp_venue_option = models.ForeignKey(ExpVenueOption, models.DO_NOTHING, null=False)
    venue_base_price = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    venue_discount_value = models.DecimalField(max_digits=65535, decimal_places=65535, null=False)
    venue_discount_percent = models.DecimalField(max_digits=65535, decimal_places=65535, null=True)
    is_active = models.BooleanField(default=True, null=False)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'exp_venue_option_price'

    app_label = 'default'


class ExpVenuePatternType(models.Model):
    exp_venue_pattern_type_id = models.BigAutoField(primary_key=True)
    exp_venue_pattern_type_name = models.CharField(max_length=255, null=False, unique=True)
    exp_venue_pattern_type_description = models.CharField(max_length=500, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'exp_venue_pattern_type'

    app_label = 'default'


class ExpVenuePattern(models.Model):
    exp_venue_pattern_id = models.BigAutoField(primary_key=True)
    exp_venue_pattern_type = models.ForeignKey(ExpVenuePatternType, models.DO_NOTHING, null=False)
    exp_venue_availability = models.ForeignKey(ExpVenueAvailability, models.DO_NOTHING, null=True)
    separation_count = models.IntegerField(null=True)
    max_num_of_occurence = models.IntegerField(null=True)
    day_of_week = models.IntegerField(null=True)
    week_of_month = models.IntegerField(null=True)
    day_of_month = models.IntegerField(null=True)
    month_of_year = models.IntegerField(null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'exp_venue_pattern'

    app_label = 'default'


class Tax(models.Model):
    tax_id = models.BigAutoField(primary_key=True)
    tax_name = models.CharField(unique=True, max_length=255)
    tax_description = models.CharField(max_length=500, blank=True, null=True)
    tax_percentage = models.DecimalField(max_digits=65535, decimal_places=65535)
    is_active = models.BooleanField()
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'tax'

    app_label = 'default'


class TaxCustom(models.Model):
    tax_custom_id = models.BigAutoField(primary_key=True)
    vendor_id = models.BigIntegerField()
    tax_custom_name = models.CharField(unique=True, max_length=255)
    tax_custom_description = models.CharField(max_length=500, blank=True, null=True)
    tax_custom_percentage = models.DecimalField(max_digits=65535, decimal_places=65535)
    is_active = models.BooleanField()
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'tax_custom'

    app_label = 'default'


class UserLoginHistory(models.Model):
    user_login_history_id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    ip_number = models.CharField(max_length=50)
    browser_type = models.CharField(max_length=50)
    is_success = models.BooleanField()
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'user_login_history'

    app_label = 'default'


class VendorBusinessAssociation(models.Model):
    vendor_business_association_id = models.BigAutoField(primary_key=True)
    vendor = models.ForeignKey('Vendor', models.DO_NOTHING)
    vendor_business = models.ForeignKey(VendorBusiness, models.DO_NOTHING)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'vendor_business_association'

    app_label = 'default'


class BookingChatMessage(models.Model):
    booking_chat_message_id = models.BigAutoField(primary_key=True)
    booking_purchase = models.ForeignKey('BookingPurchase', models.DO_NOTHING, blank=True, null=True)
    vendor = models.ForeignKey('Vendor', models.DO_NOTHING)
    user = models.ForeignKey('User', models.DO_NOTHING)
    attachment = models.ForeignKey(Attachment, models.DO_NOTHING, blank=True, null=True)
    chat_message = models.TextField(blank=True, null=True)
    is_read = models.BooleanField()
    is_removed = models.BooleanField()
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'booking_chat_message'

    app_label = 'default'


class VenueLevel(models.Model):
    venue_level_id = models.BigAutoField(primary_key=True)
    venue_level_name = models.CharField(unique=True, max_length=255)
    venue_level_description = models.CharField(max_length=500, blank=True, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_level'

    app_label = 'default'


class ExpVenueAvailabilityTimeslot(models.Model):
    exp_venue_availability_timeslot_id = models.BigAutoField(primary_key=True)
    exp_venue_availability = models.ForeignKey(ExpVenueAvailability, models.DO_NOTHING)
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField(blank=True, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'exp_venue_availability_timeslot'
    app_label = 'default'


class VenueTax(models.Model):
    venue_tax_id = models.BigAutoField(primary_key=True)
    venue_internal = models.ForeignKey(VenueInternal, models.DO_NOTHING)
    tax = models.ForeignKey(Tax, models.DO_NOTHING, blank=True, null=True)
    tax_custom_id = models.BigIntegerField(blank=True, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'venue_tax'

    app_label = 'default'


class BookingPurchasePromo(models.Model):
    booking_purchase_promo_id = models.BigAutoField(primary_key=True)
    venue_promo = models.ForeignKey('VenuePromo', models.DO_NOTHING)
    booking_purchase = models.ForeignKey(BookingPurchase, models.DO_NOTHING)
    activated_promo_code = models.CharField(max_length=20, blank=True, null=True)
    created_on = models.DateTimeField(null=False, default=datetime.datetime.now())
    modified_on = models.DateTimeField(null=True)
    created_by = models.BigIntegerField(null=False, default=16395)
    modified_by = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'booking_purchase_promo'

    app_label = 'default'


############################################################################################################################################################################################

"""
-------------------------------------------------------------------------PAYMENTS MODEL-------------------------------------------------------------------------------------------------------------------------

"""


############################################################################################################################################################################################

class BillingAddress(models.Model):
    billing_address_id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField(null=False)
    billing_name = models.CharField(max_length=255, null=False)
    email = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, null=False)
    city = models.CharField(max_length=255, null=False)
    state = models.CharField(max_length=255, null=False)
    state_code = models.CharField(max_length=255, null=False)
    zip = models.CharField(max_length=255, null=False)
    country_name = models.CharField(max_length=255, null=False)
    country_code_two_char = models.CharField(max_length=3, null=False)
    default_source = models.BooleanField()
    mobile_phone = models.CharField(max_length= 50, null=False)


    class Meta:
        managed = False
        db_table = 'billing_address'

    app_label = 'payments'


class PaymentOptionType(models.Model):
    payment_option_type_id = models.BigAutoField(primary_key=True)
    payment_option_type = models.CharField(max_length=512, null=False)

    class Meta:
        managed = False
        db_table = 'payment_option_type'

    app_label = 'payments'


class PaymentOption(models.Model):
    payment_option_id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField(null=False)
    payment_option_type = models.ForeignKey(PaymentOptionType, models.DO_NOTHING, null=False)

    class Meta:
        managed = False
        db_table = 'payment_option'

    app_label = 'payments'


class CardPaymentDetail(models.Model):
    card_payment_detail_id = models.BigAutoField(primary_key=True)
    expiry_month = models.BigIntegerField(null=False)
    expiry_year = models.BigIntegerField(null=False)
    card_number = models.BinaryField(null=False)
    security_code = models.BinaryField(null=False)
    billing_address = models.ForeignKey(BillingAddress, models.DO_NOTHING)
    payment_option = models.ForeignKey(PaymentOption, models.DO_NOTHING, blank=True, null=True)
    card_name = models.CharField(max_length=255, null=False)

    class Meta:
        managed = False
        db_table = 'card_payment_detail'

    app_label = 'payments'


class Transaction(models.Model):
    transaction_id = models.BigAutoField(primary_key=True)
    user_payment_type = models.ForeignKey(PaymentOption, models.DO_NOTHING, null=False)
    date_created = models.DateTimeField(null=False)
    booking_purchase_id = models.BigIntegerField(null=False)

    class Meta:
        managed = False
        db_table = 'transaction'

    app_label = 'payments'