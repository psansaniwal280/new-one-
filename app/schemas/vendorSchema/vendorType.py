import graphene

class VendorObjectType(graphene.ObjectType):
    # class Meta:
    #     model = Vendor
    vendor_id = graphene.Int()
    name = graphene.String()
    avatar = graphene.String()
    bio_url = graphene.String()
    short_description = graphene.String()
    rating = graphene.Float()
    no_of_ratings = graphene.Int()

# class VendorListObjectType(graphene.ObjectType):
#     venue_vendor_id = graphene.Int()

