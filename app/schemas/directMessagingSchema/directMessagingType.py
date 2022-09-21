from app.models import *
import graphene
from app.schemas.commonObjects.objectTypes import PageInfoObject, aggregateObjectType

class UserIdFieldType(graphene.ObjectType):
    user_id = graphene.Int()

class ChatUserType(graphene.ObjectType):
    username = graphene.String()
    userId = graphene.Int()
    avatar = graphene.String()

class AttachmentTypeObject(graphene.ObjectType):
    attachment_type_id = graphene.Int()
    attachment_type_name = graphene.String()

class ChatMessageAttachmentType(graphene.ObjectType):
    attachment_id= graphene.Int()
    attachment_url= graphene.String()
    type = graphene.Field(AttachmentTypeObject)

class ChatThreadAttachmentType(graphene.ObjectType):
    type = graphene.Field(AttachmentTypeObject)
    id = graphene.String()
    url= graphene.String()

class ChatMessageReactionType(graphene.ObjectType):
    type_id = graphene.String()
    user_id = graphene.String()

class ChatSharesTemplateMessageType(graphene.ObjectType):
    type = graphene.String()
    media = graphene.String()
    id = graphene.String()
    title = graphene.String()

class ChatSharesMessageType(graphene.ObjectType):
    link = graphene.String()
    template = graphene.Field(ChatSharesTemplateMessageType)
    

class ChatStroyMessageType(graphene.ObjectType):
    link = graphene.String()
    id = graphene.Int()
    is_reply = graphene.Boolean()

class RecipientFieldType(graphene.ObjectType):
    user_id = graphene.Int()
    read = graphene.Boolean()




class ChatMessageType(graphene.ObjectType):
    class Meta:
        model = ChatMessage

    isSender = graphene.Boolean()
    messageId = graphene.Int()
    modified_on = graphene.DateTime()
    # sender = graphene.Field(ChatUserType)
    sender_user_id = graphene.Int()
    recipient_user_id = graphene.List(UserIdFieldType)
    recipient_user_read = graphene.List(RecipientFieldType)
    message = graphene.String()
    attachment = graphene.Field(ChatMessageAttachmentType)
    reaction = graphene.List(ChatMessageReactionType)
    shares = graphene.Field(ChatSharesMessageType)
    story = graphene.Field(ChatStroyMessageType)
    read = graphene.Boolean()

class ChatMessagesType(graphene.ObjectType):
    messageId = graphene.Int()
    created_on = graphene.DateTime()
    # message = graphene.String()

class ChatMessagesPageListType(graphene.ObjectType):
    page_info = graphene.Field(PageInfoObject)
    messages = graphene.List(ChatMessagesType)


class ChatThreadType(graphene.ObjectType):
    thread_id = graphene.Int()
    name = graphene.String()
    # messages = graphene.List(ChatMessagesType)
    participants = graphene.List(UserIdFieldType)
    unreadCount = graphene.Field(aggregateObjectType)
    mostRecentMessage = graphene.String()
    avatar = graphene.String()
    hasUnreadMessage = graphene.Boolean()
    admin = graphene.List(UserIdFieldType)
    is_group = graphene.Boolean()

class ChatThreadListType(graphene.ObjectType):
    threadId = graphene.Int()
    participants = graphene.List(ChatUserType)
    modified_on = graphene.DateTime()
    recent_message = graphene.Field(ChatMessagesType)
    has_unread = graphene.Boolean()

class ChatThreadsPageListType(graphene.ObjectType):
    page_info = graphene.Field(PageInfoObject)
    threads = graphene.List(ChatThreadListType)


# class ChatMessageListType(graphene.ObjectType):
#     messages = graphene.List(ChatMessagesType)    
