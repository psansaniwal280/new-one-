from app.models import *
import graphene
from app.schemas.commonObjects.objectTypes import PageInfoObject


class BadgeType(graphene.ObjectType):
    # class Meta:
    #     model = Badge
    user_badge_id = graphene.Int()
    badge_id = graphene.Int()
    image = graphene.String()
    name = graphene.String()
    value = graphene.Int()
    badge_type = graphene.String()
    date_earned = graphene.DateTime()
    is_pinned = graphene.Boolean()


class BadgesListType(graphene.ObjectType):
    user_badge_id = graphene.Int()

class BadgesYearListType(graphene.ObjectType):
    label = graphene.String()
    badges = graphene.List(BadgesListType)

class BadgesPageListType(graphene.ObjectType):
    badges = graphene.List(BadgesYearListType)
    page_info = graphene.Field(PageInfoObject)