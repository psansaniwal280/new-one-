import graphene
import re
from .userTravelType import *
from app.utilities.errors import *
from app.models import *
from app.utilities.toBigInt import BigInt

class AddTravelerMutation(graphene.Mutation):
    message = graphene.String()
    travelerId = graphene.Int()

    class Arguments:
        userId = graphene.Argument(BigInt)
        bookingPurchaseId = graphene.Argument(BigInt)
        firstName = graphene.String()
        middleName = graphene.String()
        lastName = graphene.String()
        dateOfBirth = graphene.Date()
        genderId = graphene.Argument(BigInt)
        travelerRelationshipId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        firstName = kwargs.get('firstName')
        middleName = kwargs.get('middleName')
        lastName = kwargs.get('lastName')
        dateOfBirth = kwargs.get('dateOfBirth')
        genderId = kwargs.get('genderId')
        travelerRelationshipId = kwargs.get('travelerRelationshipId')
        
        # cheating to add a traveler relationship
        '''travelerRelationship = TravelerRelationship.objects.create(
            traveler_relationship_name = "Spouse",
            traveler_relationship_description = "Spouse",
            created_on = datetime.datetime.now(),
            created_by = userId,
            modified_on = datetime.datetime.now()
        )
        travelerRelationship.save()'''

        # Checks if the inputs actually exist
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        if firstName is not None:
            name = firstName.replace(' ', '')
            if name == "":
                raise ValueError("invalid request: firstName can not be blank")
        else:
            raise BadRequestException("invalid request: firstName provided is invalid", 400)
        if lastName is not None:
            name = lastName.replace(' ', '')
            if name == "":
                raise ValueError("invalid request: lastName can not be blank")
        else:
            raise BadRequestException("invalid request: lastName provided is invalid", 400)
        if dateOfBirth is not None:
            if dateOfBirth > datetime.date.today():
                raise ValueError("invalid request: dateOfBirth provided is in the future")
        else:
            raise BadRequestException("invalid request: dateOfBirth provided is invalid", 400)
        if genderId is not None:
            try:
                gender = Gender.objects.using('default').get(gender_id=genderId)
            except Gender.DoesNotExist:
                raise NotFoundException("genderId provided not found", 404)
        else:
            raise BadRequestException("invalid request: genderId provided is invalid", 400)
        if travelerRelationshipId is not None:
            try:
                travelerRelationship = TravelerRelationship.objects.using('default').get(traveler_relationship_id=travelerRelationshipId)
            except TravelerRelationship.DoesNotExist:
                raise NotFoundException("travelerRelationshipId provided not found", 404)
        else:
            raise BadRequestException("invalid request: travelerRelationshipId provided is invalid", 400)

        # creates the traveler
        traveler = Traveler.objects.create(
            gender_id = genderId,
            first_name = firstName,
            middle_name = middleName,
            last_name = lastName,
            date_of_birth = dateOfBirth,
            traveler_relationship_id = travelerRelationshipId,
            user_id = userId,
            created_by = userId,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now()
        )
        traveler.save()

        return AddTravelerMutation(message="Successfully added traveler", travelerId = traveler.traveler_id)

class DeleteTravelerMutation(graphene.Mutation):
    message = graphene.String()
    travelerId = graphene.Int()

    class Arguments:
        userId = graphene.Argument(BigInt)
        travelerId = graphene.Argument(BigInt)
    
    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        travelerId = kwargs.get('travelerId')

        # Checks if the inputs actually exist
        if userId is not None:
            try:
               user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        
        if travelerId is not None:
            try:
               traveler = Traveler.objects.using('default').get(traveler_id=travelerId)
            except Traveler.DoesNotExist:
                raise NotFoundException("travelerId provided not found", 404)
        else:
            raise BadRequestException("invalid request; travelerId provided is invalid", 400)

        # deletes the traveler
        try:
            traveler = Traveler.objects.using('default').get(user_id=userId, traveler_id=travelerId)
            traveler.delete()
        except Traveler.DoesNotExist:
            raise ConflictException("conflict in request; userId provided is not authorized to delete provided travelerId", 409)
        
        return DeleteTravelerMutation(message = "Successfully deleted provided travelerId", travelerId = travelerId)

class UpdateTravelerMutation(graphene.Mutation):
    message = graphene.String()
    traveler_id = graphene.Int()
    first_name = graphene.String()
    middle_name = graphene.String()
    last_name = graphene.String()
    date_of_birth = graphene.Date()
    gender_id = graphene.Int()
    traveler_relationship_id = graphene.Int()

    class Arguments:
        userId = graphene.Argument(BigInt)
        travelerId = graphene.Argument(BigInt)
        firstName = graphene.String()
        middleName = graphene.String()
        lastName = graphene.String()
        dateOfBirth = graphene.Date()
        genderId = graphene.Argument(BigInt)
        travelerRelationshipId = graphene.Argument(BigInt)

    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        travelerId = kwargs.get('travelerId')
        firstName = kwargs.get('firstName')
        middleName = kwargs.get('middleName')
        lastName = kwargs.get('lastName')
        dateOfBirth = kwargs.get('dateOfBirth')
        genderId = kwargs.get('genderId')
        travelerRelationshipId = kwargs.get('travelerRelationshipId')

        # checks if the user and traveler actually exist
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if travelerId is not None:
            try:
                traveler = Traveler.objects.using('default').get(traveler_id=travelerId)
            except Traveler.DoesNotExist:
                raise NotFoundException("travelerId provided is not found")
        else:
            raise BadRequestException("invalid request; travelerId proivded is invalid")

        # ensures that no blank inputs are provided for names/genders and travelers provided actually exists
        name = firstName.replace(' ', '')
        if name == "":
            raise ValueError("invalid request: firstName can not be blank")
        name = lastName.replace(' ', '')
        if name == "":
            raise ValueError("invalid request: lastName can not be blank")
        try:
            gender = Gender.objects.using('default').get(gender_id=genderId)
        except Gender.DoesNotExist:
            raise NotFoundException("genderId provided not found", 404)
        try:
            travelerRelationship = TravelerRelationship.objects.using('default').get(traveler_relationship_id=travelerRelationshipId)
        except TravelerRelationship.DoesNotExist:
            raise NotFoundException("travelerRelationshipId provided not found", 404)
        if dateOfBirth is not None:
            if dateOfBirth > datetime.date.today():
                raise ValueError("invalid request: dateOfBirth provided is in the future")

        # checks if the traveler can be received underneath the userId, then updates if so
        try:
            traveler = Traveler.objects.using('default').get(user_id=userId, traveler_id=travelerId)
            # updates traveler info
            if firstName is not None or traveler.first_name is None:
                traveler.first_name = firstName
            if middleName is not None or traveler.middle_name is None:
                traveler.middle_name = middleName
            if lastName is not None or traveler.last_name is None:
                traveler.last_name = lastName
            if dateOfBirth is not None or traveler.date_of_birth is None:
                traveler.date_of_birth = dateOfBirth
            if genderId is not None or traveler.gender_id is None:
                traveler.gender_id = genderId
            if travelerRelationshipId is not None or traveler.traveler_relationship_id is None:
                traveler.traveler_relationship_id = travelerRelationshipId
            traveler.modified_on = datetime.datetime.now()
            traveler.modified_by = userId
            traveler.save()
        except Traveler.DoesNotExist:
            raise ConflictException("conflict in request; userId provided is not authorized to delete provided travelerId", 409)
        
        return UpdateTravelerMutation(message="Successfully updated traveler info to provided travelerId", traveler_id=travelerId, first_name=firstName, middle_name=middleName, last_name=lastName, date_of_birth=dateOfBirth, gender_id=genderId, traveler_relationship_id=travelerRelationshipId)
    


class Mutation(graphene.ObjectType):
    add_traveler = AddTravelerMutation.Field()
    delete_traveler = DeleteTravelerMutation.Field()
    update_traveler = UpdateTravelerMutation.Field()



    