import graphene
from app.models import *
from graphene_django import DjangoObjectType
from app.schemas.commonObjects.objectTypes import *
from app.schemas.userSchema.userType import UserType
from app.utilities.extractWord import extract_tags_mentions
from app.utilities.toBigInt import BigInt


class OutputHashTagType(DjangoObjectType):
    class Meta:
        model = Tag
    tag_id = graphene.Int()
    name = graphene.String()

class OutputPostHashTagType(DjangoObjectType):
    class Meta:
        model = PostTag
    post_tag_id = graphene.Int()
    post_id = graphene.Int()
    tag_id = graphene.Field(OutputHashTagType)
    def resolve_post_id(self, info):
        return Post.objects.all()
    def resolve_tag_id(self, info):
        return Tag.objects.all()

class OutputMentionType(DjangoObjectType):
    class Meta:
        model = PostMention
    post_mention_id = graphene.Int()
    post_id = graphene.Int()
    user_id = graphene.Field(UserType)
    def resolve_post_id(self, info):
        return Post.objects.all()
    def resolve_user_id(self, info):
        return User.objects.all()

class PostListType(graphene.ObjectType):
    post_id = graphene.Int()
    rel_score = graphene.Float()

class PostPageListType(graphene.ObjectType):
    posts = graphene.List(PostListType)
    page_info = graphene.Field(PageInfoObject)

class PostCommentListType(graphene.ObjectType):
    post_comment_id = graphene.Int()

class PostType(graphene.ObjectType):
    # class Meta:
    #     model = Post
    post_id = graphene.Int()
    media = graphene.String()
    thumbnail = graphene.String()
    venue_id = graphene.String()
    title = graphene.String()
    user_rating = graphene.Float()
    user_id = graphene.Int()
    is_verified_booking = graphene.Boolean()
    created_on = graphene.DateTime()
    postLikesAggregate = graphene.Field(aggregateObjectType)
    postCommentsAggregate = graphene.Field(aggregateObjectType)
    postSharesAggregate = graphene.Field(aggregateObjectType)
    postSavesAggregate = graphene.Field(aggregateObjectType)
    post_description = graphene.String()
    hashtags = graphene.List(hashtagSection)
    mentions = graphene.List(mentionSection)
    isLiked = graphene.Boolean()
    isSaved = graphene.Boolean()
    viewCount = graphene.Int()


    def resolve_media(self, info):
        if self['media_post_id']:
            return MediaPost.objects.using('default').get(media_post_id=int(self['media_post_id'])).media_post_url
        else:
            return None

    def resolve_postLikesAggregate(self, info):
        postlike_aggregate_output_obj = []
        postlike_objs =[]
        postlike_objs += PostLike.objects.using('default').filter(post_id=self['post_id']).values_list('post_like_id', flat=True)
        if postlike_objs !=[]:
            for each in postlike_objs:
                postlike_aggregate_output_obj.append(each)
        else:
            postlike_aggregate_output_obj = []
        return aggregateObjectType(aggregate(count=len(postlike_aggregate_output_obj)))

    def resolve_postCommentsAggregate(self, info):
        postcomment_aggregate_output_obj = []
        postcomment_objs =[]
        postcomment_objs += PostComment.objects.using('default').filter(post_id=self['post_id']).values_list('post_comment_id', flat=True)
        if postcomment_objs !=[]:
            for each in postcomment_objs:
                postcomment_aggregate_output_obj.append(each)
        else:
            postcomment_aggregate_output_obj = []
        return aggregateObjectType(aggregate(count=len(postcomment_aggregate_output_obj)))

    def resolve_postSavesAggregate(self, info):
        postsaved_aggregate_output_obj = []
        postsaved_objs =[]
        postsaved_objs += PostSaved.objects.using('default').filter(post_id=self['post_id']).values_list('post_saved_id', flat=True)
        if postsaved_objs !=[]:
            for each in postsaved_objs:
                postsaved_aggregate_output_obj.append(each)
        else:
                postsaved_aggregate_output_obj = []
        return aggregateObjectType(aggregate(count=len(postsaved_aggregate_output_obj)))

    def resolve_postSharesAggregate(self, info):
        postshared_aggregate_output_obj = []
        postshared_objs =[]
        postshared_objs += Shared.objects.using('default').filter(post_id=self['post_id']).values_list('shared_id', flat=True)
        if postshared_objs !=[]:
            for each in postshared_objs:
                postshared_aggregate_output_obj.append(each)
        else:
                postshared_aggregate_output_obj = []
        return aggregateObjectType(aggregate(count=len(postshared_aggregate_output_obj)))

    def resolve_hashtags(self, info):
        hashtags_word, hashtags = [], []
        hashtags_word, _ = extract_tags_mentions(self['post_description'])
        if hashtags_word == []:
            return []
        for one_hashtag in hashtags_word:
            try:
                tag_obj = Tag.objects.using('default').get(tag_name=one_hashtag)
                try:
                    PostTag.objects.using('default').get(post_id=self['post_id'], tag_id=tag_obj.tag_id)
                except PostTag.DoesNotExist:
                    PostTag.objects.create(post_id=self['post_id'], tag_id=tag_obj.tag_id)
                hashtags.append(hashtagSection(tag_obj.tag_name, tag_obj.tag_id))
            except Tag.DoesNotExist:
                tag_obj = Tag.objects.create(tag_name=one_hashtag)
                try:
                    PostTag.objects.using('default').get(post_id=self['post_id'], tag_id=tag_obj.tag_id)
                except PostTag.DoesNotExist:
                    PostTag.objects.create(post_id=self['post_id'], tag_id=tag_obj.tag_id)
                hashtags.append(hashtagSection(tag_obj.tag_name, tag_obj.tag_id))
        return hashtags

    def resolve_mentions(self, info):
        mentions_word, mentions = [], []
        _ , mentions_word = extract_tags_mentions(self['post_description'])
        if mentions_word == []:
            return []
        for one_mention in mentions_word:
            try:
                userObjList = User.objects.using('default').values('user_id', 'username')
                for user_obj in userObjList:
                    if user_obj['username'] == one_mention: 
                        mentions.append(mentionSection(user_obj['username'], user_obj['user_id']))
            except User.DoesNotExist:
                mentions.append(mentionSection(one_mention, None))
        return mentions

    def resolve_viewCount(self, info):
        viewCnt = 0
        WATCH_MIN = 500
        try:
            selfView = False
            for impression in PostView.objects.using('default').filter(post_id=self['post_id']):
                # if there is no video duration, continue (note that this should be non-nullable)
                if impression.video_duration is None:
                    continue
                
                # calculates total watch time
                watchTimeDT = impression.video_end_time - impression.video_start_time
                watchTime = watchTimeDT.days * 86400000 + watchTimeDT.seconds * 1000 + watchTimeDT.microseconds/1000

                # gives the uploader their one view if they've watched their own video
                if impression.user_id == self['user_id']:
                    if watchTime >= WATCH_MIN and not selfView:
                        viewCnt += 1
                        selfView = True
                        continue

                if watchTime >= WATCH_MIN:
                    viewCnt += 1 + math.floor(((watchTime-WATCH_MIN)/impression.video_duration) if watchTime-WATCH_MIN > impression.video_duration else 0)
            return viewCnt
        except PostView.DoesNotExist:
            return 0



class PostLikeType(DjangoObjectType):
    class Meta:
        model = PostLike
    post_like_id = graphene.Field(BigInt)
    post_id = graphene.Field(BigInt)
    user_id = graphene.Field(BigInt)

class PostSavedType(DjangoObjectType):
    class Meta:
        model = PostSaved
    post_saved_id = graphene.Field(BigInt)
    post_id = graphene.Field(BigInt)
    user_id = graphene.Field(BigInt)

class OutputUserType(graphene.ObjectType):
    user_id = graphene.Int()
    username = graphene.String()
    avatar = graphene.String()
    level = graphene.Int()

class PostCommentReplyType(graphene.ObjectType):
    post_comment_id = graphene.Int()
    # user = graphene.Field(UserType)
    # post_id = graphene.Field(PostType)
    # comment = graphene.String()
    # number_of_likes = graphene.Int()
    # hashtags = graphene.List(hashtagSection)
    # mentions = graphene.List(mentionSection)

class PostCommentType(graphene.ObjectType):
    # class Meta:
    #     model  = PostComment
    post_comment_id = graphene.Field(BigInt)
    user = graphene.Field(OutputUserType)
    comment = graphene.String()
    commentLikesAggregate = graphene.Field(aggregateObjectType)
    created_on= graphene.DateTime()
    commentRepliesAggregate = graphene.Field(aggregateObjectType)
    comment_replies = graphene.List(PostCommentReplyType)
    hashtags = graphene.List(hashtagSection)
    mentions = graphene.List(mentionSection)
    isLiked = graphene.Boolean()
    isReply = graphene.Boolean()
    # def resolve_no_of_replies(self, info):
    #     return 0

class MediaPostType(graphene.ObjectType):
    media_post_id = graphene.Field(BigInt)
    media_post_url = graphene.String()
    media_post_raw_url = graphene.String()


class CommentReply(graphene.ObjectType):
    postCommentId= graphene.Int()


class CommentRepliesListType(graphene.ObjectType):
    postCommentReplies = graphene.List(CommentReply)
    postCommentId = graphene.Int()

class VideoAnalyticsTimeType(graphene.ObjectType):
    days = graphene.Int()
    hours = graphene.Int()
    minutes = graphene.Int()
    seconds = graphene.Float()

class VideoAnalyticsType(graphene.ObjectType):
    views = graphene.Int()
    reached_audience = graphene.Int()
    click_throughs = graphene.Int()
    total_watch_time = graphene.Field(VideoAnalyticsTimeType)
    average_watch_time = graphene.Field(VideoAnalyticsTimeType)
    percent_watch_full = graphene.Float()
class ViewSourceType(graphene.ObjectType):
    class Meta:
        model = ViewSource
        exclude = ('created_on','created_by','modified_on','modified_by')
    view_source_id = graphene.Int()
    view_source_name = graphene.String()
    view_source_description = graphene.String()
class ViewRetentionType(graphene.ObjectType):
    retention_percentages = graphene.List(graphene.Int)
    retention_intervals = graphene.List(graphene.Int)
