import graphene
from app.models import *
from app.utilities.errors import *

"""
    Pin Badges -- Array of 3
"""
class PinBadgesMutation(graphene.Mutation):
    message = graphene.String()
    badgesPinned = graphene.List(graphene.String)
    userId = graphene.Int()

    class Arguments:
        userId = graphene.Int()
        userBadges = graphene.List(graphene.Int)
    
    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        badges = kwargs.get('userBadges')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if badges is not None:
            if len(badges)<=3:
                pass
            else:
                raise BadRequestException("invalid request; userBadges provided exceeds limit (only 3 pinned badges allowed)")
            # try:
                # badgeObjs = Badge.objects.using('default').filter(badge_id=badges)
            for each in badges:
                try:
                    # print(each)
                    
                    userBadge = UserBadge.objects.using('default').get(user_id = userId, user_badge_id = each)
                    badge= Badge.objects.using('default').get(badge_id=userBadge.badge_id)
                    # except UserBadge.
                    if userBadge.is_pinned is None or userBadge.is_pinned == False:
                        userBadge.is_pinned = True
                        userBadge.save()
                        
                    # elif userBadge.is_pinned ==True:
                    #     return PinBadgesMutation(message="successfully pinned badges provided", badgesPinned=badges, userId = userId)
                except UserBadge.DoesNotExist:
                    raise NotFoundException("provided userBadgeId "+str(each)+" is not associated with provided userId")
                except Badge.DoesNotExist:
                    raise NotFoundException("badgeId: "+str(badge.badge_id)+" provided is not found")
            userBadges = UserBadge.objects.using('default').filter(user_id=userId)
            for each in userBadges:
                if each.badge_id not in badges:
                    each.is_pinned = False
                    each.save()
            return PinBadgesMutation(message="successfully pinned userBadges provided", badgesPinned = badges, userId = userId)
        else:
            raise BadRequestException("invalid request; userBadges provided is invalid")
        
class Mutation(graphene.ObjectType):
    pin_user_badges = PinBadgesMutation.Field()
