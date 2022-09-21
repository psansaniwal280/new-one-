import graphene
import math
from .itineraryType import *
from app.models import *
from app.schemas.commonObjects.objectTypes import *
from app.utilities.errors import *
from app.schemas.postSchema.postType import PostListType


class Query(graphene.ObjectType):

    userItineraries = graphene.Field(ItineraryPageListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    userItinerariesConcat = graphene.List(ItineraryListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    #Get Itinerary by Itinerary Ids
    itinerary = graphene.Field(ItineraryObjectType, userId = graphene.Int(), itineraryId=graphene.Int())


     #Get Itineraries by User Id
    def resolve_userItineraries(parent, info, **kwagrs):
        id = kwagrs.get('userId') 
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')  
        result= []
        if id is not None:
            try:
                if User.objects.using('default').get(user_id = id):
                    for i in UserSharedItinerary.objects.using('default').filter(user_id=id):
                        result.append(ItineraryListType(i.user_shared_itinerary_id, i.created_on))
                    if result :
                        result.sort(key=lambda x:x.created_on, reverse=True)
                        # return result
                        if len(result)>0:
                            if page and limit:
                                totalPages = math.ceil(len(result)/limit)
                                if page <= totalPages:
                                    start = limit*(page-1)
                                    result = result[start:start+limit]

                                    return ItineraryPageListType(itineraries=result, page_info=PageInfoObject(nextPage=page+1 if page+1 <= totalPages else None, limit=limit))
                                else:
                                    raise BadRequestException("invalid request; page provided exceeded total")
                            elif page == limit == None:
                                return ItineraryPageListType(itineraries=result, page_info=PageInfoObject(nextPage= None, limit=None))
                            elif page is None:
                                raise BadRequestException("invalid request; limit cannot be provided without page")
                            elif limit is None:
                                raise BadRequestException("invalid request; page cannot be provided without limit")
                        
                        else:
                            return ItineraryPageListType(itineraries=[], page_info=PageInfoObject(nextPage= None, limit=None))
                    else:
                        return ItineraryPageListType(itineraries=[], page_info=PageInfoObject(nextPage= None, limit=None))
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)   
        return None

    def resolve_userItinerariesConcat(parent, info, **kwagrs):
        id = kwagrs.get('userId') 
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')  
        result= []
        if id is not None:
            try:
                if User.objects.using('default').get(user_id = id):
                    for i in UserSharedItinerary.objects.using('default').filter(user_id=id):
                        result.append(ItineraryListType(i.user_shared_itinerary_id, i.created_on))
                    if result :
                        result.sort(key=lambda x:x.created_on, reverse=True)
                        # return result
                        if len(result)>0:
                            if page and limit:
                                totalPages = math.ceil(len(result)/limit)
                                if page <= totalPages:
                                    start = limit*(page-1)
                                    result = result[start:start+limit]

                                    return result
                                else:
                                    raise BadRequestException("invalid request; page provided exceeded total")
                            elif page == limit == None:
                                return result
                            elif page is None:
                                raise BadRequestException("invalid request; limit cannot be provided without page")
                            elif limit is None:
                                raise BadRequestException("invalid request; page cannot be provided without limit")
                        
                        else:
                            return []
                    else:
                        return []
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)   
        return None



        
 #Get Itinerary of posts by Itinerary Id
    def resolve_itinerary(self, info, **kwargs):
        userId = kwargs.get('userId')
        itineraryId = kwargs.get('itineraryId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if itineraryId is not None:
            try:
                itinerary = UserSharedItinerary.objects.using('default').get(user_shared_itinerary_id = itineraryId)
            except:
                raise NotFoundException("itineraryId provided not found")
        else:
            raise BadRequestException("invalid request; itineraryId provided is invalid") 
        
        tagIds = UserSharedItineraryTag.objects.using('default').filter(user_shared_itinerary_id=itinerary.user_shared_itinerary_id).values_list('tag_id', flat=True)
        tags = []
        res_tags = []
        res_tags = Tag.objects.using('default').filter(tag_id__in=tagIds)
        for each in res_tags:
            tags.append(hashtagSection(each.tag_name, each.tag_id))

        
        
        postIds = UserSharedItineraryPost.objects.using('default').filter(user_shared_itinerary_id=itinerary.user_shared_itinerary_id).values_list('post_id', flat=True)
        posts = []
        posts = Post.objects.using('default').filter(post_id__in=postIds).order_by('-created_on').values_list('post_id')
        
        posts = [PostListType(post_id=x[0]) for x in posts]
        # print(posts)
        result = {
            "itinerary_id": itinerary.user_shared_itinerary_id,
            "userId": itinerary.user_id,
            "title": itinerary.user_shared_itinerary_name,
            "description": itinerary.user_shared_itinerary_description,
            "tags": tags,
            "posts": posts,
            "thumbnail": itinerary.thumbnail
            }    
        return result  

