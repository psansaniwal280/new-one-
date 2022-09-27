import graphene
from .userTravelType import *
from app.utilities.errors import *
from ...utilities.pagination import pagination

class Query(graphene.ObjectType):
    travelers = graphene.List(TravelerType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    allTravelerRelationships = graphene.List(TravelerRelationshipType)
    allGenders = graphene.List(GenderType)

    def resolve_travelers(self, info, **kwargs):
        userId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if userId is not None:
            try:
                User.objects.using('default').get(user_id=userId)
                result =[]
                result += Traveler.objects.using('default').filter(user_id=userId, is_active=True)
                flag, result = pagination(result, page, limit)
                return result['result']
            except User.DoesNotExist:
                raise NotFoundException("Invalid request: userId provided does not exist", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        return None
    
    def resolve_allTravelerRelationships(self, info):
        travelerRelationships = []
        for rel in TravelerRelationship.objects.all():
            if travelerRelationships is not []:
                added = False
                for i in range(len(travelerRelationships)):
                    let = 0
                    while(travelerRelationships[i].traveler_relationship_name[let] is not None and rel.traveler_relationship_name[let] is not None and travelerRelationships[i].traveler_relationship_name[let]==rel.traveler_relationship_name[let]):
                        let+=1
                    if(rel.traveler_relationship_name[let] < travelerRelationships[i].traveler_relationship_name[let]):
                        travelerRelationships.insert(i, rel)
                        added = True
                        break
                if not added:
                    travelerRelationships.append(rel)
            else:
                travelerRelationships.append(rel)
        return travelerRelationships
    
    def resolve_allGenders(self, info):
        return Gender.objects.all()