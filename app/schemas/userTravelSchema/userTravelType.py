# imports
import graphene
from graphene_django import DjangoObjectType
from app.models import *
from app.utilities.toBigInt import BigInt
from app.schemas.commonObjects.objectTypes import *
from app.utilities.errors import *

class GenderType(DjangoObjectType):
    class Meta:
        model = Gender
        exclude = ('created_on','created_by','modified_on','modified_by')
    gender_id = graphene.Field(BigInt)
    gender_name = graphene.String()
    gender_description = graphene.String()

class TravelerRelationshipType(DjangoObjectType):
    class Meta:
        model = TravelerRelationship
        exclude = ('created_on','created_by','modified_on','modified_by')
    traveler_relationship_id = graphene.Field(BigInt)
    traveler_relationship_name = graphene.String()
    traveler_relationship_description = graphene.String()

class TravelerListType(graphene.ObjectType):
    traveler_id = graphene.Field(BigInt)

class TravelerType(DjangoObjectType):
    class Meta:
        model = Traveler
        exclude = ('created_on','created_by','modified_on','modified_by','is_active')
    traveler_id = graphene.Field(BigInt)
    first_name = graphene.String()
    middle_name = graphene.String()
    last_name = graphene.String()
    date_of_birth = graphene.Date()
    gender_id = graphene.Field(BigInt)
    traveler_relationship_id = graphene.Field(BigInt)
    gender = graphene.Field(GenderType)
    traveler_relationship = graphene.Field(TravelerRelationshipType)

    age = graphene.Int()
    def resolve_age(self, info):
        currentDay = datetime.date.today()
        age = currentDay.year - self.date_of_birth.year
        if currentDay.month < self.date_of_birth.month or (currentDay.month == self.date_of_birth.month and currentDay.day < self.date_of_birth.day):
            age -= 1
        return age

        

    def resolve_gender(self, info):
        try:
            gender = Gender.objects.using('default').get(gender_id=self.gender_id)
            return gender
        except Gender.DoesNotExist:
            return None

    def resolve_traveler_relationship(self, info):
        try:
            traveler_relationship = TravelerRelationship.objects.using('default').get(traveler_relationship_id=self.traveler_relationship_id)
            return traveler_relationship
        except TravelerRelationship.DoesNotExist:
            return None
