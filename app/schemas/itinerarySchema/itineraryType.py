import graphene
from app.schemas.userSchema.userType import UserType
from app.schemas.commonObjects.objectTypes import *
from app.models import *
from app.schemas.postSchema.postType import PostListType
from app.schemas.venueSchema.venueType import DescriptionObjectType
from app.utilities.extractWord import extract_tags_mentions

class ItineraryType(graphene.ObjectType):
    # class Meta:
    #     model = UserSharedItinerary
    itinerary_id = graphene.Int()
    user_id = graphene.Field(UserType)
    name = graphene.String()
    thumbnail = graphene.String()
    created_on = graphene.DateTime()
    modified_on = graphene.DateTime()

class ItineraryListType(graphene.ObjectType):
    itinerary_id = graphene.Int()
    created_on = graphene.DateTime()

class ItineraryPageListType(graphene.ObjectType):
    itineraries = graphene.List(ItineraryListType)
    page_info = graphene.Field(PageInfoObject)


class ItineraryObjectType(graphene.ObjectType):
    itinerary_id = graphene.Int()
    userId = graphene.Int()
    title = graphene.String()
    description = graphene.Field(DescriptionObjectType)
    tags = graphene.List(hashtagSection)
    posts = graphene.List(PostListType)
    thumbnail = graphene.String()

    def resolve_description(self, info):
        description_content = UserSharedItinerary.objects.using('default').get(user_shared_itinerary_id=self['itinerary_id']).user_shared_itinerary_description
        hashtag_words, hashtags = [], []
        mention_words, mentions = [], []
        hashtag_words, mention_words = extract_tags_mentions(description_content)
        if hashtag_words == []:
            hashtags = []
        for one_hashtag in hashtag_words:
            try:
                tag_obj = Tag.objects.using('default').get(tag_name=one_hashtag)
                hashtags.append(hashtagSection(tag_obj.tag_name, tag_obj.tag_id))
            except Tag.DoesNotExist:
                tag_obj = Tag.objects.create(
                    tag_name=one_hashtag,
                    created_on = datetime.datetime.now(),
                    modeified_on = datetime.datetime.now(),
                    created_by=self['user_id'])   
                hashtags.append(hashtagSection(tag_obj.tag_name, tag_obj.tag_id))  
        
        if mention_words == []:
            mentions = []
        for one_mention in mention_words:
            try:
                user = User.objects.using('default').get(username=one_mention)
                mentions.append(mentionSection(user.username, user.user_id))
            except User.DoesNotExist:
                mentions.append(mentionSection(one_mention, None))
        
        return DescriptionObjectType(description_content, hashtags, mentions)
