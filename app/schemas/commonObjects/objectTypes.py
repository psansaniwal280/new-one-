import graphene

class PageInfoObject(graphene.ObjectType):
    nextPage = graphene.Int()
    limit = graphene.Int()


class aggregate(graphene.ObjectType):
    count = graphene.Int()

class aggregateObjectType(graphene.ObjectType):
    aggregate = graphene.Field(aggregate)   


class aggregateOutput(graphene.ObjectType):
    count = graphene.Int()

class aggregateOutputObjectType(graphene.ObjectType):
    aggregate = graphene.Field(aggregate)


class mentionSection(graphene.ObjectType):
    username = graphene.String()        
    userId = graphene.Int()

class hashtagSection(graphene.ObjectType):
    hashtag = graphene.String()        
    tagid = graphene.Int()

class bioSection(graphene.ObjectType):
    content = graphene.String()
    hashtags = graphene.List(hashtagSection)
    mentions = graphene.List(mentionSection)


class MediaTypeObject(graphene.ObjectType):
    type_id = graphene.Int()
    type_name = graphene.String()

class MediaObjectType(graphene.ObjectType):
    id = graphene.Int()
    url = graphene.String()
    type = graphene.Field(MediaTypeObject)

"""
Error Message and Code Type
"""
class ExceptionFieldObjectType(graphene.ObjectType):
    message = graphene.String()
    code = graphene.Int()
    
class ExceptionErrorObjectType(graphene.ObjectType):
    error = graphene.Field(ExceptionFieldObjectType)


class APIPlacesListType(graphene.ObjectType):
    name = graphene.String()    



