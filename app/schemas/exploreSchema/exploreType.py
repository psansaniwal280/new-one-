import graphene

'''
Explore Graphene Object Type
'''
class ExploreTheLoopObjectType(graphene.ObjectType):
    name = graphene.String()
    thumbnail = graphene.String()

class ExploreAllUserObjectType(graphene.ObjectType):
    user_id = graphene.String()
    username = graphene.String()
    avatar = graphene.String()
    rating = graphene.String()

class ExploreAllPostObjectType(graphene.ObjectType):
    post_id  = graphene.String()
    name = graphene.String()
    #price = graphene.String()
    user = graphene.Field(ExploreAllUserObjectType)

class ExploreAllFieldType(graphene.ObjectType):
    near_you = graphene.List(ExploreAllPostObjectType)
    explore_the_loop = graphene.List(ExploreTheLoopObjectType)
    trending_videos = graphene.List(ExploreAllPostObjectType)
    recommended_users = graphene.List(ExploreAllUserObjectType)
    recommended_videos = graphene.List(ExploreAllPostObjectType)