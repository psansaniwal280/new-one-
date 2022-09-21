
import graphene
from .exploreType import *
from app.schemas.searchSchema.searchType import locationObject
from math import radians, cos, sin, asin, sqrt
from app.models import *
from app.utilities.errors import *

class Query(graphene.ObjectType):

    #Explore Queries
    exploreAll = graphene.Field(ExploreAllFieldType, userId = graphene.Int(), location=locationObject())


    #Explore ALL   
    def resolve_exploreAll(parent, info, **kwagrs):

        def dist(lat1, long1, lat2, long2):
            """
            Calculate the great circle distance between two points 
            on the earth (specified in decimal degrees)
            """
            # convert decimal degrees to radians 
            print([lat1, long1, lat2, long2])
            lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])
            # haversine formula 
            dlon = long2 - long1 
            dlat = lat2 - lat1 
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a)) 
            # Radius of earth in kilometers is 6371
            km = 6371* c

            # conversion factor
            conv_fac = 0.621371

            # calculate miles
            miles = km * conv_fac
            # print(miles)
            return miles
        
        def findNearestLocationObjects(location):
            city = location.city
            country = location.country
            lat = location.latitude
            lon = location.longitude
            #validate city, country, lat, lon
            if city is not None:
                pass
            else:
                raise BadRequestException("invalid request; city is incorrect", 400)
            if country is not None:
                pass
            else:
                raise BadRequestException("invalid request; country is incorrect", 400)
            if lat is not None:
                pass
            else:
                raise BadRequestException("invalid request; latitude is incorrect", 400)
            if lon is not None:
                pass
            else:
                raise BadRequestException("invalid request; longitude is incorrect", 400)

            dist_obj = []
            all_location_objs = Address.objects.all()
            venue_id_objs={}
            for one_obj  in all_location_objs:
                #get respective venue objects for the location
                # try:
                if VenueInternal.objects.using('default').filter(address_id=one_obj.address_id).values_list('venue_id'):
                    venue_id_objs = VenueInternal.objects.using('default').filter(address_id=one_obj.address_id).values_list('venue_id')

                # if VenueExternal.objects.using('default').filter(address_id=one_obj.address_id).values_list('venue_id'):
                #     venue_id_objs = VenueExternal.objects.using('default').filter(address_id=one_obj.address_id).values_list('venue_id')
                
                for venue_id in venue_id_objs:
                    one_post_venue_objs = Post.objects.using('default').filter(venue_id=venue_id)
                    for post_id_obj in one_post_venue_objs:
                        # print(post_id_obj)
                        zip = ZipCode.objects.using('default').get(zip_code_id=one_obj.zip_code_id)
                        city = City.objects.using('default').get(city_id=zip.city_id)
                        if (city.latitude is not None) and  (city.longitude is not None):
                            dist_obj.append((dist(lat, lon, city.latitude, city.longitude), (post_id_obj.post_id, venue_id[0])))
            #Sort the distance by nearest first
            dist_obj.sort(key=lambda y: y[0])
            return dist_obj


        uid = kwagrs.get('userId')
        location = kwagrs.get('location')

    #Get the user details with the user id
        if uid is not None:
            try:
                user_obj = User.objects.using('default').get(user_id=uid)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

        json_result = []
        nearYouObjs = []
        exploreTheLoopObjs = []
        trendingVideosObjs = []
        stuffYouLike = []
        usersYouLike = []

        if location:
            dist_post_objs = findNearestLocationObjects(location)
            for i in range(len(dist_post_objs)):
                (dist, (pid, vid)) = dist_post_objs[i]
                obj = Post.objects.using('default').get(post_id=pid)
                uobj = User.objects.using('default').get(user_id=obj.user_id)
                # priceobj = VenueExperiencePrice.objects.using('default').get()
                json_obj = ExploreAllPostObjectType(obj.post_id, obj.title, ExploreAllUserObjectType(obj.user_id, uobj.username, uobj.avatar, obj.user_rating)) 
                # {
                #     'id':obj.post_id,
                #     'name':obj.title,
                #     #'price':obj.price,
                #     'user': ExploreAllUserObjectType(obj.user_id, uobj.username, uobj.avatar, obj.user_rating)
                #     # {
                #     #     'id':obj.user_id,
                #     #     'username':uobj.username,
                #     #     'avatar':uobj.avatar,
                #     #     'rating':obj.user_rating
                #     # }
                #}
                json_result.append(json_obj)
            nearYouObjs = json_result


        #For Explore the loop
        # json_result =  []
        # for obj in ExploreCategory.objects.all():
        #     json_result.append(ExploreTheLoopObjectType(obj.explore_category_name, obj.thumbnail))
        # exploreTheLoopObjs = json_result

        #For trending videos, the post can be curated from the most liked and shared videos.
        
        json_result = []
        post_objs = Post.objects.all().order_by('-total_likes', '-total_shares', '-total_comments','-total_saves')
        for pobj in post_objs:
            
            uobj = User.objects.using('default').get(user_id=pobj.user_id)

            json_obj = ExploreAllPostObjectType(pobj.post_id, pobj.title, ExploreAllUserObjectType(pobj.user_id, uobj.username, uobj.avatar, pobj.user_rating))
            json_result.append(json_obj)
        trendingVideosObjs = json_result

        '''-----------------------------------------------------------------------TO DO---------------------------------------------------------------------------'''
        #Looper you like
        #Stuff you like
        

        
        return ExploreAllFieldType(nearYouObjs, exploreTheLoopObjs, trendingVideosObjs, stuffYouLike, usersYouLike)
