from app.models import *
from app.schemas.postSchema.postType import *
from app.utilities.errors import *

# milliseconds to video analytics time type function
def msToVideoWatchTime(watchTime):
    remainingWatchTime = int(watchTime)
    days = math.floor(remainingWatchTime/86400000)
    remainingWatchTime = remainingWatchTime % 86400000
    hours = math.floor(remainingWatchTime/3600000)
    remainingWatchTime = remainingWatchTime % 3600000
    minutes = math.floor(remainingWatchTime/60000)
    remainingWatchTime = remainingWatchTime % 60000
    seconds = round(float(remainingWatchTime)/1000, 1)
    return VideoAnalyticsTimeType(days=days, hours=hours, minutes=minutes, seconds=seconds)



def videoAnalytics(postId = None):
        # checks if the post actually exist
        if postId is not None:
            try:
                post = Post.objects.using('default').get(post_id=postId)
            except Post.DoesNotExist:
                raise NotFoundException("postId provided is not found", 404)
        else:
            raise BadRequestException("invalid request; postId provided is invalid", 400)

        # views, total watch time, average watch time, and full watch percent
        viewCnt = 0
        totalWatchTime = 0
        averageWatchTime = 0.0
        fullVideoWatchCnt = 0
        percentWatchFull = 0
        reachedAudience = 0
        sittings = 0
        WATCH_MIN = 500
        selfView = False
        try:
            # gets a list of impressions and goes through each one
            impressions = PostView.objects.using('default').filter(post_id=postId)
            # keeps track of each user that watched
            reachedAudienceList = []
            for impression in impressions:
                # skips for null video_duration - note that this should be non-nullable
                if impression.video_duration is None:
                    continue

                watchTimeDT = impression.video_end_time - impression.video_start_time
                watchTime = (watchTimeDT.days * 1000*3600*24) + (watchTimeDT.seconds * 1000) + (watchTimeDT.microseconds/1000)

                # gives uploaders their one lifetime self-view and excludes them from the rest of the data
                if impression.user_id == post.user_id and watchTime > WATCH_MIN:
                    if not selfView:
                        viewCnt += 1
                        selfView = True
                    continue
                # print("after self: view count: ", viewCnt)
                totalWatchTime += watchTime
                sittings += 1

                if watchTime >= WATCH_MIN:
                    viewCnt += 1 + math.floor(((watchTime-WATCH_MIN)/(impression.video_duration) if (watchTime-WATCH_MIN > impression.video_duration) else 0))
                if watchTime >= impression.video_duration:
                    fullVideoWatchCnt += int((watchTimeDT.total_seconds() * 1000)/ impression.video_duration)

                # tracks retained audience
                try:
                    viewer = User.objects.using('default').get(user_id=impression.user_id)
                    if viewer.is_active:
                        try:
                            reachedAudienceList.index(viewer.user_id)
                        except:
                            reachedAudienceList.append(viewer.user_id)
                except User.DoesNotExist:
                    pass
            averageWatchTime = float(totalWatchTime)/sittings if sittings > 0 else 0
            percentWatchFull = round(((float(fullVideoWatchCnt)/sittings)*100), 2) if sittings > 0 else 0
            reachedAudience = len(reachedAudienceList)
            totalWatchTimeObj = msToVideoWatchTime(totalWatchTime)
            averageWatchTimeObj = msToVideoWatchTime(averageWatchTime)
        except PostView.DoesNotExist:
            # returns 0 views/watch time if no impressions exist
            averageWatchTimeObj = VideoAnalyticsTimeType(days=0,hours=0,minutes=0,seconds=0)
            totalWatchTimeObj = VideoAnalyticsTimeType(days=0,hours=0,minutes=0,seconds=0)
            
       

        # gets clickthroughs
        clickThroughs = 0
        try:
            clicks = PostVenueClick.objects.using('default').filter(post_id=postId)
            for click in clicks:
                if click.user_id != post.user_id:
                    clickThroughs += 1
        except PostVenueClick.DoesNotExist:
            clickThroughs = 0
        return VideoAnalyticsType(views=viewCnt, click_throughs=clickThroughs, total_watch_time=totalWatchTimeObj, average_watch_time=averageWatchTimeObj, percent_watch_full=percentWatchFull, reached_audience=reachedAudience)