import graphene
from app.models import *
from .badgesType import BadgesListType, BadgesYearListType, BadgesPageListType, BadgeType
from app.utilities.errors import *
import math
from app.schemas.commonObjects.objectTypes import PageInfoObject
from app.utilities.pagination import pagination

class Query(graphene.ObjectType):
    userBadges = graphene.Field(BadgesPageListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    userBadgesConcat = graphene.List(BadgesListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    userBadge = graphene.Field(BadgeType, userBadgeId = graphene.Int())
  
  #Get Badges by User Id    
    def resolve_userBadges(parent, info , **kwagrs):
        
        id = kwagrs.get('userId')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if id is not None :
            try:
                result_badge_ids = []
                if User.objects.using('default').get(user_id=id):
                    result_badge_ids = UserBadge.objects.using('default').filter(user_id=id)
                    resultDict = {"Pinned": []}
                    k =0
                    if result_badge_ids:
                        # start w/ pinned
                        resultDict["Pinned"] = UserBadge.objects.using('default').filter(user_id=id, is_pinned=True)

                        # failsafe for too many pinned
                        if len(resultDict["Pinned"]) > 3:
                            sortedPinned = []
                            index = 0
                            for item in resultDict["Pinned"]:
                                if sortedPinned == []:
                                    sortedPinned.append(item)
                                    continue
                                while (index < len(sortedPinned) and ((item.modified_on if item.modified_on is not None else item.created_on) < (sortedPinned[index].modified_on if sortedPinned[index].modified_on is not None else sortedPinned[index].created_on))):
                                    index += 1
                                while (index > 0 and ((item.modified_on if item.modified_on is not None else item.created_on) > (sortedPinned[index].modified_on if sortedPinned[index].modified_on is not None else sortedPinned[index].created_on))):
                                    index -= 1
                                if index == len(sortedPinned):
                                    sortedPinned.append(item)
                                else:
                                    sortedPinned.insert(index, item)
                            resultDict["Pinned"] = sortedPinned[0:3]
                        

                        for badge in result_badge_ids:
                            if badge in resultDict["Pinned"]:
                                continue
                            year = badge.date_earned.year
                            if resultDict.get(str(year)) == None:
                                resultDict[str(year)] = []
                            resultDict[str(year)].append(badge)
                        
                        sortedBadges = []
                        for badge in resultDict["Pinned"]:
                            sortedBadges.append(badge)
                        for year in reversed(range(2021, datetime.date.today().year+1)):
                            if(resultDict.get(str(year))!=None):
                                for badge in resultDict[str(year)]:
                                    sortedBadges.append(badge)                   

                        # pagination
                        flag, page_data = pagination(sortedBadges, page, limit)
                        if flag:
                            result = []
                            resultPerYear = []
                            pinnedResult = []
                            previousYear = UserBadge.objects.using("default").get(user_badge_id=(page_data["result"])[0].user_badge_id).date_earned.year
                            for badgeThing in page_data["result"]:
                                badge = UserBadge.objects.using("default").get(user_badge_id=badgeThing.user_badge_id)
                                if badge in resultDict["Pinned"]:
                                    pinnedResult.append(badge)
                                else:
                                    if badge.date_earned.year != previousYear:
                                        if resultPerYear != []:
                                            result.append(BadgesYearListType(label=str(previousYear),badges=resultPerYear))
                                            resultPerYear=[]
                                        previousYear = badge.date_earned.year
                                    resultPerYear.append(badge)
                            if resultPerYear != []:
                                result.append(BadgesYearListType(label=str(previousYear),badges=resultPerYear))
                            if pinnedResult != []:
                                result.insert(0, BadgesYearListType(label="Pinned",badges=pinnedResult))
                            return BadgesPageListType(badges=result, page_info=PageInfoObject(
                                nextPage=page_data["page"], limit=page_data["limit"]))
                        else:
                            raise BadRequestException(page_data)
                    #'''    for j in result_badge_ids:
                    #        for i in Badge.objects.using('default').filter(badge_id = j.badge_id):
                    #            if j.is_pinned:
                    #                result.insert(0, j)#BadgesListType(j.user_badge_id)) #, i.badge_id, i.image, i.name, i.value, i.badge_type_id, j.date_earned))
                    #            else:
                    #                result.append(j)
                    #    
                    #flag, page_data = pagination(result, page, limit)
                    #if flag:
                    #    return BadgesPageListType(badges=page_data["result"], page_info=PageInfoObject(
                    #        nextPage=page_data["page"], limit=page_data["limit"]))
                    #else:
                    #    raise BadRequestException(page_data) '''

                    # else:
                    #     raise NotFoundException("no badges associated with this user", 204)
            except (User.DoesNotExist, Badge.DoesNotExist):
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        return None

    def resolve_userBadgesConcat(parent, info , **kwagrs):
        
        id = kwagrs.get('userId')
        page = kwagrs.get('page')
        limit = kwagrs.get('limit')
        if id is not None :
            try:
                result_badge_ids = []
                if User.objects.using('default').get(user_id=id):
                    result_badge_ids = UserBadge.objects.using('default').filter(user_id=id)
                    resultDict = {"Pinned": []}
                    k =0
                    if result_badge_ids:
                        # start w/ pinned
                        resultDict["Pinned"] = UserBadge.objects.using('default').filter(user_id=id, is_pinned=True)

                        # failsafe for too many pinned
                        if len(resultDict["Pinned"]) > 3:
                            sortedPinned = []
                            index = 0
                            for item in resultDict["Pinned"]:
                                if sortedPinned == []:
                                    sortedPinned.append(item)
                                    continue
                                while (index < len(sortedPinned) and ((item.modified_on if item.modified_on is not None else item.created_on) < (sortedPinned[index].modified_on if sortedPinned[index].modified_on is not None else sortedPinned[index].created_on))):
                                    index += 1
                                while (index > 0 and ((item.modified_on if item.modified_on is not None else item.created_on) > (sortedPinned[index].modified_on if sortedPinned[index].modified_on is not None else sortedPinned[index].created_on))):
                                    index -= 1
                                if index == len(sortedPinned):
                                    sortedPinned.append(item)
                                else:
                                    sortedPinned.insert(index, item)
                            resultDict["Pinned"] = sortedPinned[0:3]
                        

                        for badge in result_badge_ids:
                            if badge in resultDict["Pinned"]:
                                continue
                            year = badge.date_earned.year
                            if resultDict.get(str(year)) == None:
                                resultDict[str(year)] = []
                            resultDict[str(year)].append(badge)
                        
                        sortedBadges = []
                        for badge in resultDict["Pinned"]:
                            sortedBadges.append(badge)
                        for year in reversed(range(2021, datetime.date.today().year+1)):
                            if(resultDict.get(str(year))!=None):
                                for badge in resultDict[str(year)]:
                                    sortedBadges.append(badge)                   

                        # pagination
                        flag, page_data = pagination(sortedBadges, page, limit)
                        if flag:
                            return page_data['result']
                        else:
                            raise BadRequestException(page_data)
                    #'''    for j in result_badge_ids:
                    #        for i in Badge.objects.using('default').filter(badge_id = j.badge_id):
                    #            if j.is_pinned:
                    #                result.insert(0, j)#BadgesListType(j.user_badge_id)) #, i.badge_id, i.image, i.name, i.value, i.badge_type_id, j.date_earned))
                    #            else:
                    #                result.append(j)
                    #    
                    #flag, page_data = pagination(result, page, limit)
                    #if flag:
                    #    return BadgesPageListType(badges=page_data["result"], page_info=PageInfoObject(
                    #        nextPage=page_data["page"], limit=page_data["limit"]))
                    #else:
                    #    raise BadRequestException(page_data) '''

                    # else:
                    #     raise NotFoundException("no badges associated with this user", 204)
            except (User.DoesNotExist, Badge.DoesNotExist):
                raise NotFoundException("userId provided not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
        return None

 #Get Badge by User Badge Id
    def resolve_userBadge(parent, info, **kwargs):
        userBadgeId = kwargs.get('userBadgeId')
        if userBadgeId is not None :
            userBadge = UserBadge.objects.using('default').get(user_badge_id=userBadgeId)
            try:
                i = Badge.objects.using('default').get(badge_id = userBadge.badge_id)
                return BadgeType(userBadgeId, i.badge_id, i.image, i.badge_name, i.value, i.badge_type_id, userBadge.date_earned, userBadge.is_pinned)
            except (UserBadge.DoesNotExist, Badge.DoesNotExist):
                raise NotFoundException("userBadgeId provided not found", 404)
            except UserProfile.DoesNotExist:
                raise NotFoundException("profile for provided userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)


        # return result