

import graphene
from .vendorType import *
from app.models import *
from app.utilities.errors import *
from django.db.models import Max, Avg


class Query(graphene.ObjectType):

      #Get Vendor Object By Venue Vendor Id
    vendor = graphene.Field(VendorObjectType, vendorVenueId = graphene.Int())


     #Get Vendor Object by Venue Vendor Id
    def resolve_vendor(self, info, **kwargs):
        venueVendorId = kwargs.get('vendorVenueId')
        if venueVendorId is not None:
            try:
                vendorVenue = VendorVenue.objects.using('default').get(vendor_venue_id=venueVendorId)
                vendorVenueIds = []
                vendorVenueIds = VendorVenue.objects.using('default').filter(vendor_id=vendorVenue.vendor_id).values_list('venue_id', flat=True)

                vendorRating = Post.objects.using('default').filter(venue_id__in=vendorVenueIds).aggregate(Avg('user_rating'))['user_rating__avg']
                vendorRatingCount = Post.objects.using('default').filter(venue_id__in=vendorVenueIds).count()
                # result = VendorObjectType(vendorVenue.vendor_venue_id, vendorVenue.vendor.name, vendorVenue.vendor.avatar, vendorVenue.vendor.bio_url, vendorVenue.vendor.short_description, vendorRating, vendorRatingCount)
                
                return VendorObjectType(vendorVenue.vendor_venue_id, vendorVenue.vendor.vendor_name, vendorVenue.vendor.avatar, vendorVenue.vendor.vendor_url, vendorVenue.vendor.vendor_description, vendorRating, vendorRatingCount)
            except VendorVenue.DoesNotExist:
                raise NotFoundException("vendorVenueId provided not found")
        else:
            raise BadRequestException("invalid request; vendorVenueId is invalid")

    