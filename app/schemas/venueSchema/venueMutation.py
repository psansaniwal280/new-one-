import graphene
from app.models import *
from .venueType import *
from app import models



"""
This is a Mutation Function to insert Venue(venue_id, is_external)
"""

class InputVenueType(graphene.InputObjectType):
    class Meta:
        model = Venue
    venue_id = graphene.String()
    is_external = graphene.Boolean()
    venue_price = graphene.String()
    venue_location = graphene.String()

    def resolve_venue_price(self, info):
        if self.is_external:
            return None
        else:
            result_venue = VenueInternal.objects.using('default').get(pk=self.venue_id)
            return str(result_venue.price) 
    def resolve_venue_location(self, info):
        if self.is_external:
            obj = VenueExternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.location)
        else:
            obj = VenueInternal.objects.using('default').get(pk=self.venue_id)
            return str(obj.location)

# class CreateVenueMutation(graphene.Mutation):
#     class Arguments:
#         vendorId= graphene.Int()
#         title= graphene.Int()


"""
This is a Mutation Function to insert Internal Venue
""" 
class InputVenueInternalType(graphene.InputObjectType):
    class Meta:
        model = VenueInternal
    name = graphene.String(), 
    price = graphene.Boolean(), 
    description = graphene.String(), 
    location = graphene.String(), 
    latitude = graphene.Boolean(), 
    longitude = graphene.Boolean(), 
    venue_id = graphene.String(), 
    type = graphene.String()

class CreateVenueInternalMutation(graphene.Mutation):
    class Arguments:
        venue_data = InputVenueInternalType()
    venue_internal = graphene.Field(VenueInternalType)
    def mutate(self, info, venue_data):
        venue_internal = models.VenueInternal.objects.create(
            venue_internal_name = venue_data.name, 
            # price = venue_data.name, 
            venue_internal_description = venue_data.description, 
            location = venue_data.location, 
            latitude = venue_data.latitude, 
            longitude = venue_data.longitude, 
            venue_id = venue_data.venue_id, 
            venue_type = venue_data.type,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
        )
        venue_internal.save()

"""
This is a Mutation Function to insert External Venue
"""
class InputVenueExternalType(graphene.InputObjectType):
    class Meta:
        model = VenueExternal
    api_id = graphene.String(),
    name = graphene.String(),  
    description = graphene.String(), 
    location = graphene.String(), 
    latitude = graphene.Boolean(), 
    longitude = graphene.Boolean(), 
    venue_id = graphene.String()

class CreateVenueExternalMutation(graphene.Mutation):
    class Arguments:
        venue_data = InputVenueExternalType()
    venue_external = graphene.Field(VenueExternalType)
    def mutate(self, info, venue_data):
        venue_external = models.VenueExternal.objects.create(
            venue_external_name = venue_data.name, 
            # price = venue_data.name, 
            venue_external_description = venue_data.description, 
            location = venue_data.location, 
            latitude = venue_data.latitude, 
            longitude = venue_data.longitude, 
            venue_id = venue_data.venue_id, 
            venue_type = venue_data.type,
            created_on = datetime.datetime.now(),
            modified_on = datetime.datetime.now(),
        )
        venue_external.save()



class Mutation(graphene.ObjectType):
   # create_venue = CreateVenueMutation.Field()
    create_venue_internal = CreateVenueInternalMutation.Field()
    create_venue_external = CreateVenueExternalMutation.Field()