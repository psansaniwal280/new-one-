from app.models import *
from .directMessagingType import *
from app.utilities.errors import *
import graphene
from app.schemas.commonObjects.objectTypes import PageInfoObject, aggregate, aggregateObjectType
import math
from django.db.models import Q
from app.utilities.matchGroup import getParticipantMatch, getParticipantContains
from app.utilities.pagination import pagination


class Query(graphene.ObjectType):
    #Recieve Message
    messages = graphene.List(ChatMessageType, userId = graphene.Int(), recipientUserId= graphene.Int(), threadId = graphene.Int())
    
    #Threads
    threadList = graphene.Field(ChatThreadsPageListType, userId = graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    #Threads -- Chat Request
    requestThreadList = graphene.Field(ChatThreadsPageListType, userId = graphene.Int(), page=graphene.Int(), limit = graphene.Int())

    #Message Thread
    threadInfo = graphene.Field(ChatThreadType, userId = graphene.Int(), threadId = graphene.Int())

    #Message List 
    messageList = graphene.Field(ChatMessagesPageListType, userId = graphene.Int(), threadId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    #Message
    message = graphene.Field(ChatMessageType, userId = graphene.Int(), messageId = graphene.Int())

 #Receive Chat Message
    def resolve_messages(self, info, **kwargs):
        sender_user_id = kwargs.get('authUserId')
        receiver_user_id = kwargs.get('recipientUserId')
        dialog_id = kwargs.get('threadId')

        try: 
            User.objects.using('default').get(user_id=sender_user_id)
        except User.DoesNotExist:
            raise NotFoundException("sender userId provided not found", 404)
        try: 
            User.objects.using('default').get(user_id=receiver_user_id)
        except User.DoesNotExist:
            raise NotFoundException("receiver userId provided not found", 404)
        try:
            dialog = ChatThread.objects.using('default').get(id = dialog_id)
            try:
                dialog = ChatThread.objects.using('default').get((Q(user1_id= sender_user_id) , Q(user2_id= receiver_user_id)) | (Q(user2_id= sender_user_id) & Q(user1_id= receiver_user_id)))
            except ChatThread.DoesNotExist:
                raise NotFoundException("thread between the users not found", 404)
        except ChatThread.DoesNotExist:
            raise NoContentException("threadId provided not found", 404)
        
        chat_messages = []
        chat_messages += ChatMessage.objects.using('default').filter(dialog_id = dialog_id)
        result = []
        print(len(chat_messages))
        for each in chat_messages:
            s_user = User.objects.using('default').get(user_id=each.sender_id)
            r_user = User.objects.using('default').get(user_id=each.recipient_id)
            

            sender_user = {
                "username": s_user.username,
                "id": s_user.user_id ,
                "avatar": s_user.avatar
            }
            recipient_user = {
                "username": r_user.username,
                "id": r_user.user_id ,
                "avatar": r_user.avatar
            }
            if each.attachment_type is not None:
                if each.attachment_type.attachment_type_name == 'post':
                    attachment_id = Shared.objects.using('default').get(chat_message_id=each.id).post_id
                elif each.attachment_type.attachment_type_name == 'venue':
                    attachment_id = Shared.objects.using('default').get(chat_message_id=each.id).venue_id
                attachment = {
                    "type": {
                        "name":each.attachment_type.attachment_type_name,
                        "attachment_type_id":each.attachment_type_id
                        },
                    "id": attachment_id
                }
            else:
                attachment = {}
            if each.reaction:
                reaction = {
                    "reaction": None,
                    "user": None
                }
            else:
                reaction = {}
            shares = {
                "is_post": False,
                "media": None,
                "id": None,
                "title": None
            }
            story = {
                "id": None,
                "link": None,
                "is_reply": None
            }
            each_result =  {
                "messageId": each.id,
                "modified_on": each.modified_on,
                "sender": sender_user,
                "recipient": recipient_user,
                "message":each.text,
                "attachment": attachment,
                "reaction": reaction,
                "shares": shares,
                "story": story
            }
            result.append(each_result)
        
        #Sort with latest date on top
        result.sort(key = lambda x:x['modified_on'], reverse=True)

        return result
        
 #Thread List
    def resolve_threadList(self, info, **kwargs):
        user_id = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id=user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        dialogs = []
        messages = []
        list_messages=[]
        partUsers=getParticipantContains(user_id)
        for each in partUsers:
            if each['chat_thread_id'] is not None:
                # dialogs += ChatThread.objects.using('default').filter(chat_thread_id=each['chat_thread_id']).values_list('chat_thread_id', 'created_on', 'is_approved')#, 'created', 'user1_id', 'user2_id')
                dialogs += ChatMessage.objects.using('default').filter(chat_thread_id=each['chat_thread_id']).values('chat_thread_id', 'created_on', 'chat_message_id').order_by('chat_message_id')
  
        dialogs.sort(key=lambda x:x['created_on'], reverse = True)
        result = []
        dialogs= list({v['chat_thread_id']:v for v in dialogs}.values())
        flag, page_data = pagination(dialogs, page, limit)
     
        if flag:
            for each in page_data['result']:
                if each['chat_message_id']:
                    try:
                        ChatDeleteThread.objects.using('default').get(chat_thread_id=each['chat_thread_id'], user_id = user_id)
                    except ChatDeleteThread.DoesNotExist:
                        result.append({
                            "threadId": each['chat_thread_id'],
                        })

    
            return ChatThreadsPageListType(threads=result, page_info=PageInfoObject(nextPage=page_data['page'], limit=page_data['limit'] ))
        else:
            raise BadRequestException(page_data)
        
        
 
 #Get Thread by Thread Id
    def resolve_threadInfo(self, info, **kwargs):
        dialog_id = kwargs.get('threadId')
        user_id = kwargs.get('userId')
        if user_id is not None:
            try:
                user= User.objects.using('default').get(user_id=user_id)

            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if dialog_id is not None:
            try:
                dialog = ChatThread.objects.using('default').get(chat_thread_id = dialog_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=dialog_id).values_list('user_id', flat=True)
                if user.user_id in participants:
                    pass
                else:
                    raise AuthorizationException("userId provided is not authorized to view this thread")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found", 404)
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")

        result = {}
        messages = []
        participants = []
        unreadCount = 0
        list_messages = ChatMessage.objects.using('default').filter(chat_thread_id=dialog_id)

        for each in list_messages:
            chat_message_read = ChatMessageRecipient.objects.using('default').filter(chat_message_id = each.chat_message_id, user_id=user_id).values_list('is_read', flat=True)
         
            if len(chat_message_read)>0 and chat_message_read[0]:
                pass
            else:
                unreadCount +=1
           
            messages.append({"id": each.chat_thread_id, "created_on": each.created_on, "message":each.text})

        recentMessage = messages[-1]['message'] if messages!=[] else ""
        participants += ChatThreadParticipant.objects.using('default').filter(chat_thread_id=dialog_id).values_list('user_id',flat=True)
     
        name=''
        if dialog.chat_thread_name:
            user = User.objects.using('default').get(user_id=user_id)
            if not len(participants)>2 and not dialog.is_group:
                for one in participants:
                    # one = User.objects.using('default').get(user_id=one)
                    if one==user_id:
                        continue
                    one = User.objects.using('default').get(user_id=one)
                    
                    name += one.username
                    if len(participants)>2:
                        name += ',' 
            else:
                name = dialog.chat_thread_name
        else:
            for one in participants:
                # one = User.objects.using('default').get(user_id=one)
                if one==user_id:
                    continue
                one = User.objects.using('default').get(user_id=one)
                
                name += one.username
                if len(participants)>2:
                    name += ','
        admin =[]
        adminList=ChatThreadAdmin.objects.using('default').filter(chat_thread_id=dialog_id).values_list('user_id',flat=True)
        if len(adminList)>0:
            for user_id in adminList:
                admin.append(user_id)
        
        avatar=''
        if dialog.avatar:
            avatar=dialog.avatar

        result = {
            "thread_id": dialog.chat_thread_id,
            # "messages": messages,
            "is_group" : dialog.is_group,
            "participants": [{"user_id": each} for each in participants],
            "name": name,
            "hasUnreadMessage": False if unreadCount==0 else True,
            "unreadCount":aggregateObjectType(aggregate= aggregate(count = unreadCount)),
            "mostRecentMessage": recentMessage,
            "admin":[{"user_id":eachAdmin} for eachAdmin in admin],
            "avatar": avatar
        }
        return result

 #Get Message List
    def resolve_messageList(self, info, **kwargs):
        user_id = kwargs.get('userId')
        dialog_id = kwargs.get('threadId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')

        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id=user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if dialog_id is not None:
            try:
                dialog = ChatThread.objects.using('default').get(chat_thread_id = dialog_id)
                participants=ChatThreadParticipant.objects.using('default').filter(chat_thread_id=dialog_id).values_list('user_id',flat=True)
                if user_id in participants:
                    pass
                else:
                    raise AuthorizationException("userId provided is not authorized to view this list")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found", 404)
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")
        
        list_messages = []
        messages = []
        participants = []

        list_messages+= ChatMessage.objects.using('default').filter(chat_thread_id=dialog.chat_thread_id).values_list('chat_message_id', 'created_on', 'sender_id')
        list_messages.sort(key = lambda x:x[1], reverse=True)
        
        for each in list_messages:
            messages.append({"messageId": each[0], "created_on": each[1]})
            recipientList= ChatMessageRecipient.objects.using('default').filter(chat_message_id=each[0]).values_list('user_id', flat=True)
            if user_id in recipientList:
                message = ChatMessageRecipient.objects.using('default').get(chat_message_id=each[0], user_id=user_id)               
                message.is_read = True
                message.read_on = datetime.datetime.now()
                message.save(update_fields=['is_read','read_on'])
        result = messages
        flag, page_data = pagination(result, page, limit)
        if flag:
            return ChatMessagesPageListType(messages=page_data["result"], page_info=PageInfoObject(
                nextPage=page_data["page"], limit=page_data["limit"]))
        else:
            raise BadRequestException(page_data)
             
     
        
        # return messages

    # Get Message by Message Id
    def resolve_message(self, info, **kwargs):
        sender_user_id = kwargs.get('userId')
        # receiver_user_id = kwargs.get('recipientUserId')
        messageId = kwargs.get('messageId')
        # dialog_id = kwargs.get('threadId')

        if sender_user_id is not None:
            try:
                User.objects.using('default').get(user_id=sender_user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found", 404)
        else:
            BadRequestException("invalid request; userId provided is invalid")

        if messageId is not None:
            try:
                message = ChatMessage.objects.using('default').get(chat_message_id=messageId)
            except ChatMessage.DoesNotExist:
                raise NotFoundException("messageId provided not found")
        else:
            raise BadRequestException("invalid request; messageId provided is invalid")

        # chat_messages = []
        # chat_messages += ChatMessage.objects.using('default').filter(dialog_id = dialog_id)
        result = []
        # print(len(chat_messages))
        # for each in chat_messages:
        each = message
        # s_user = User.objects.using('default').get(user_id=each.sender_id)
        # r_user = User.objects.using('default').get(user_id=each.recipient_id)

        # -----------getting the message recipients ---------------
        try:
            dialog = ChatThread.objects.using('default').get(chat_thread_id=each.chat_thread_id)
            participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=each.chat_thread_id).values_list('user_id', flat=True)
            if sender_user_id not in participants:
                raise AuthorizationException("authUserId provided is not authorized to view this messageId")
            receiver_user_id = [e.user_id for e in User.objects.using('default').filter(user_id__in=participants) if e.user_id != each.sender_id]
        except ChatThread.DoesNotExist:
            raise NotFoundException("thread between the users not found", 404)

        # -----------------message attachment -------------------
        attachment = {}
        if each.attachment_id is not None:
            try:
                attachmentObj = Attachment.objects.using('default').get(attachment_id=each.attachment_id)
                attachmentTypeObj = AttachmentType.objects.using('default').get(attachment_type_id=attachmentObj.attachment_type_id)
            except ChatThread.DoesNotExist:
                raise NotFoundException("thread between the users not found", 404)

            attachment = {
                "attachment_id": each.attachment_id,
                "attachment_url": attachmentObj.attachment_url,
                "type": {
                    "attachment_type_id": attachmentObj.attachment_type_id,
                    "attachment_type_name": attachmentTypeObj.attachment_type_name
                }

            }

        # -----------------message reaction -------------------
        try:
            reactions = []
            reaction = []
            reactions = ChatMessageReaction.objects.using('default').filter(chat_message_id=each.chat_message_id)
            for eachReaction in reactions:
                reaction.append({
                    "type_id": eachReaction.chat_message_reaction_type_id,
                    "user_id": eachReaction.user_id
                })
        except ChatMessageReaction.DoesNotExist:
            reaction = []
        
        read=False
        try:
            recipient = ChatMessageRecipient.objects.using('default').get(chat_message_id=each.chat_message_id, user_id=sender_user_id)
            if recipient.is_read:
                read = True
            else:
                read = False    
        except ChatMessageRecipient.DoesNotExist:
            read = False
    
        if each.shared_id is not None:
            shared = Shared.objects.using('default').get(shared_id=each.shared_id)
            if shared.post_id is not None:
                postObj = Post.objects.using('default').get(post_id=int(shared.post_id))
                shares = {
                    "type": "Post",
                    "id": postObj.post_id,
                    "media": postObj.thumbnail,
                    "title": postObj.title
                }

            elif shared.venue_id is not None:
                venueObj = Venue.objects.using('default').get(venue_id=shared.venue_id)
                if venueObj.is_external:
                    venueExternalObj = VenueExternal.objects.using('default').get(venue_id=venueObj.venue_id)
                    mediaString = None #venueExternalObj.thumbnail
                    name = venueExternalObj.venue_external_name
                else:
                    venueInternalObj = VenueInternal.objects.using('default').get(venue_id=venueObj.venue_id)
                    mediaString = None #venueInternalObj.thumbnail
                    name = venueInternalObj.venue_internal_name
                shares = {
                    "type": "Venue",
                    "id": venueObj.venue_id,
                    "media": mediaString,
                    "title": name
                }

        else:
            shares = {
                "type": None,
                "id": None,
                "media": None,
                "title": None
            }

        story = {
            "id": None,
            "link": None,
            "is_reply": None
        }

        each_result = {
            # "isSender": True if message.sender_id == sender_user_id else False,
            "messageId": each.chat_message_id,
            "modified_on": each.modified_on,
            "sender_user_id": each.sender_id,
            "recipient_user_id":[{"user_id": each} for each in receiver_user_id],
            "message": each.text,
            "attachment": attachment,
            "reaction": reaction,
            "shares": {"link": None, "template": shares},
            "story": None,
            "read" : read
        }
        result.append(each_result)

        # Sort with latest date on top
        # result.sort(key = lambda x:x['modified_datetime'], reverse=True)

        return each_result


    # Get Thread List of Chat Request       
    def resolve_requestThreadList(self, info, **kwargs):
            user_id = kwargs.get('userId')
            page = kwargs.get('page')
            limit = kwargs.get('limit')
            if user_id is not None:
                try:
                    user = User.objects.using('default').get(user_id=user_id)
                except User.DoesNotExist:
                    raise NotFoundException("userId provided not found")
            else:
                raise BadRequestException("invalid request; userId provided is invalid")
            dialogs = []
            partUsers=getParticipantContains(user_id)
            for each in partUsers:
                if each['chat_thread_id'] is not None:
                    dialogs += ChatThread.objects.using('default').filter(chat_thread_id=each['chat_thread_id']).values_list('chat_thread_id', 'created_on', 'is_approved')#, 'created', 'user1_id', 'user2_id')


            dialogs.sort(key=lambda x:x[1], reverse = True)
            result = []
            for each in dialogs:
                # messages = []
                # recent_message = []
                # has_unread = False
                # if user_id == each[3]:
                #     flag = 0
                # else:
                #     flag = 1
                # participant = User.objects.using('default').get(user_id=each[3]) if flag == 1 else User.objects.using('default').get(user_id=each[4])
                
                # recent_message += ChatMessage.objects.using('default').filter(dialog_id=each[0]).values_list('id', 'modified', 'text', 'read', 'sender_id')

                # recent_message.sort(key = lambda x:x[1], reverse=True)

                # for each_message in recent_message:
                #     messages.append({"id": each_message[0], "date_created": each_message[1], "message": each_message[2]})
                #     if not each_message[3] and not each_message[4]==user_id :
                #         has_unread = True
                if not each[2]:
                    result.append({
                        "threadId": each[0],
                        # "date_modified": each[1],
                        # "participants": [{
                        #     "username":participant.username,
                        #     "id": participant.user_id,
                        #     "avatar": participant.avatar
                        #     }],
                        # "recent_message":messages[0],
                        # "has_unread":has_unread
                    })
            
            flag, page_data = pagination(result, page, limit)
            if flag:
                return ChatThreadsPageListType(threads=page_data["result"], page_info=PageInfoObject(
                    nextPage=page_data["page"], limit=page_data["limit"]))
            else:
                raise BadRequestException(page_data)
                     
            return result
