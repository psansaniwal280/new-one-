from email import message
import os
from app.models import *
from .directMessagingType import *
from app.utilities.errors import *
from app.utilities.toBigInt import BigInt
import datetime
import graphene
from django.db.models import Q
from django.db.models import Max, Avg
from app.utilities.uploadFileToAws import upload_to_aws
from django.conf import settings
from app import models
import mimelib
from app.utilities.matchGroup import getParticipantMatch, getParticipantContains
"""
    Chat - Send Message 
"""
class ChatSendMessageMutation(graphene.Mutation):
    message_id = graphene.List(graphene.Int)
    thread_id = graphene.Int()
    auth_user_id = graphene.Int()
    recipient_user_id = graphene.List(UserIdFieldType)
    attachments = graphene.List(ChatMessageAttachmentType)

    class Arguments:
        authUserId = graphene.Int()
        recipientUserId = graphene.List(BigInt)
        threadId = graphene.Int()
        message = graphene.String()
        attachmentList = Upload()

    def mutate(self, info, **kwargs):
        sender_user_id = kwargs.get('authUserId')
        receiver_user_id = kwargs.get('recipientUserId')
        text = kwargs.get('message')
        attachment_list= kwargs.get('attachmentList')
        temp_threads =[]
        attachmentOutputObj=[]
        messageIdList=[]
   
        if sender_user_id is not None:
            try: 
                User.objects.using('default').get(user_id=sender_user_id)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found", 404)
        else:
            BadRequestException("invalid request; authUserId provided is invalid")
        if receiver_user_id:
            for each in receiver_user_id:
                try: 
                    User.objects.using('default').get(user_id=each)
                except User.DoesNotExist:
                    raise NotFoundException("recipientUserId provided is not found ---"+str(each)+"-- userId", 404)
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid")

        participants = []
        participants += receiver_user_id
        participants.append(sender_user_id)
        participants = list(set(sorted(participants)))    
        # print(participants)
        following = []
        # for each in participants: 
        temp_threads =[]
        participants_temp_thread=[]
        result=getParticipantMatch(participants)

        thread_id = result['match_thread_id']
        if thread_id is not None:     
            try:
                dialog = ChatThread.objects.using('default').get(chat_thread_id=thread_id) 
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")

            dialog.modified = datetime.datetime.now()
            for each in participants:
                following += UserFollowing.objects.using('default').filter(following_user_id=sender_user_id, user_id=each).values_list('user_id', flat=True)
            
            temp_threads += ChatThread.objects.using('default').filter(created_by__in=receiver_user_id).values_list('chat_thread_id', flat=True)  
            participants_temp_thread += ChatThreadParticipant.objects.using('default').filter(chat_thread_id__in=temp_threads, user_id=sender_user_id).values_list('chat_thread_id', flat=True)
            participants_temp_thread = list(set(sorted(participants_temp_thread)))  

            if following !=[]:
                is_approved = True
            else:
                if not participants_temp_thread ==[]:
                    print("here")
                    is_approved = True                        
                else:
                    print("else")
                    is_approved = False

                         
            if is_approved:
                dialog.is_approved = True

            if len(participants)>2:
                dialog.is_group = True    

            dialog.save() 
            try:
                deleteThread = ChatDeleteThread.objects.using('default').filter(chat_thread_id=dialog.chat_thread_id)
                # print("fsd")
                # print(deleteThread)
                for each in deleteThread:
                    each.delete()
            except ChatDeleteThread.DoesNotExist:
                pass
            
            dialog.save()

        else :
        
            for each in participants:
                following += UserFollowing.objects.using('default').filter(following_user_id=sender_user_id, user_id=each).values_list('user_id', flat=True)

            temp_threads += ChatThread.objects.using('default').filter(created_by__in=receiver_user_id).values_list('chat_thread_id', flat=True)    
            participants_temp_thread += ChatThreadParticipant.objects.using('default').filter(chat_thread_id__in=temp_threads, user_id=sender_user_id).values_list('chat_thread_id', flat=True)
            participants_temp_thread = list(set(sorted(participants_temp_thread)))    
            if following !=[]:
                is_approved = True
            else:
                if not participants_temp_thread ==[]:
                    # print("here")
                    is_approved = True
                    
                else:
                    # print("else")
                    is_approved = False
            
            name =''
            for one in participants:
                one = User.objects.using('default').get(user_id=one)             
                name += one.username
                if len(participants)>2:
                    name += ','

            admin = None
            is_group = False
            if len(participants)>2:
                name = None
                is_group = True
                admin = sender_user_id
            else:
                is_group = False
                admin = None

            dialog = ChatThread.objects.create(
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now(),
                chat_thread_name = name,
                is_approved = is_approved,
                created_by = sender_user_id,
                is_group = is_group
            )
            dialog.save()

            for user_id in list(set(sorted(participants))):
                chat_thread_participants= ChatThreadParticipant.objects.create(
                    chat_thread_id = dialog.chat_thread_id,
                    user_id = user_id,
                    created_by = sender_user_id,
                    created_on = datetime.datetime.now(),
                    modified_on = datetime.datetime.now(),
                )
                chat_thread_participants.save()

            if admin:
               chat_thread_admin=ChatThreadAdmin.objects.create(
                chat_thread_id = dialog.chat_thread_id,
                user_id = admin,
                created_by = sender_user_id,
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now(),
               )   
               chat_thread_admin.save()  
               
        if attachment_list is not None:
            if len(info.context.FILES.getlist('0'))!=0 and len(info.context.FILES.getlist('0'))<=6 :
                counter = 1
                for file in info.context.FILES.getlist('0'):
                    aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
                    folder_name = "chat-attachment/"
                    filename, file_extension = os.path.splitext(str(file))
                    file_name = "chat_attachment_"+filename+str(dialog.chat_thread_id)+file_extension
                    media_link = aws_link+folder_name+file_name
                    success_upload = upload_to_aws(file, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
                    print(success_upload)
                    print(media_link)

                    file_type_name = mimelib.url(str(file)).file_type
                    if file_type_name=="image":
                        attachmentType=AttachmentType.objects.using('default').get(attachment_type_name='Image')
                
                    elif file_type_name=="media":
                        attachmentType=AttachmentType.objects.using('default').get(attachment_type_name='Video')
                
                    else:    
                        pass
                    
                    attachment = Attachment.objects.create(          
                        attachment_type_id = attachmentType.attachment_type_id,
                        attachment_url = media_link,
                        created_by = sender_user_id,
                        created_on = datetime.datetime.now(),
                        modified_on = datetime.datetime.now(),
                    )
                    attachment.save()
                    last_attachment = Attachment.objects.all().aggregate(Max('attachment_id'))
                    attachmentId = last_attachment['attachment_id__max']

                    attachmentObj = Attachment.objects.using('default').get(attachment_id=attachmentId)
                    attachmentsObj= {
                        'attachment_id': attachmentObj.attachment_id,
                        'attachment_url': attachmentObj.attachment_url,
                        'type': attachmentType,
                    }
                
                    attachmentOutputObj.append(attachmentsObj)

                    if counter == len(info.context.FILES.getlist('0')):
                        message = text
                        
                    else:
                        message= None

                    counter +=1
                    chat_message = ChatMessage.objects.create(
                        created_on = datetime.datetime.now(),
                        modified_on = datetime.datetime.now(),
                        is_removed = False,
                        text = message,
                        sender_id = sender_user_id,
                        chat_thread_id = dialog.chat_thread_id,
                        attachment_id = attachmentId,
                        created_by = sender_user_id
                    )
                    chat_message.save()

                    for user_id in list(set(sorted(receiver_user_id))):
                        chat_message_recipients=ChatMessageRecipient.objects.create(
                            chat_message_id = chat_message.chat_message_id,
                            user_id= user_id,
                            is_read = False,
                            created_by = sender_user_id,
                            created_on = datetime.datetime.now(),
                            modified_on = datetime.datetime.now(),

                        )
                        chat_message_recipients.save()
                    messageIdList.append(chat_message.chat_message_id)
               
                
            else:
                raise ConflictException("conflict in request; unable to upload more than 6 media files")   

        else:
                chat_message = ChatMessage.objects.create(
                            created_on = datetime.datetime.now(),
                            modified_on = datetime.datetime.now(),
                            is_removed = False,
                            text = text,
                            sender_id = sender_user_id,
                            chat_thread_id = dialog.chat_thread_id,
                            created_by = sender_user_id
                        )
                chat_message.save()
                
                for user_id in list(set(sorted(receiver_user_id))):
                    chat_message_recipients=ChatMessageRecipient.objects.create(
                        chat_message_id = chat_message.chat_message_id,
                        user_id = user_id,
                        is_read = False,
                        created_by = sender_user_id,
                        created_on = datetime.datetime.now(),
                        modified_on = datetime.datetime.now(),

                    )
                    chat_message_recipients.save()
                messageIdList.append(chat_message.chat_message_id)

        return ChatSendMessageMutation(recipient_user_id=[{"user_id": each} for each in receiver_user_id], message_id=messageIdList, thread_id = chat_message.chat_thread_id, auth_user_id=sender_user_id, attachments=attachmentOutputObj)


"""
    Post/Venue - Share Message
"""
class TemplateObjectType(graphene.InputObjectType):
    type = graphene.String()
    id = graphene.String()

class ShareObjectType(graphene.InputObjectType) :
    template = graphene.Field(TemplateObjectType)
    link = graphene.String()

class AttachmentOutputObjectType(graphene.ObjectType) :
    type = graphene.String()
    id = graphene.String()

class ChatSendMessageSharesMutation(graphene.Mutation):
    message_id = graphene.Int()
    recipient_user_id = graphene.List(UserIdFieldType)
    auth_user_id = graphene.Int()
    threadId = graphene.Int()
    message = graphene.String()
    sharedId = graphene.Int()
    # attachment = graphene.Field(AttachmentOutputObjectType)

    class Arguments:
        authUserId = graphene.Int()
        recipientUserId = graphene.List(BigInt)
        message = graphene.String()
        threadId = graphene.Int()
        # isPost = graphene.Boolean()
        shareObj = graphene.Argument(ShareObjectType)

    def mutate(self, info, **kwargs):
        auth_user_id = kwargs.get('authUserId')
        receiver_user_id = kwargs.get('recipientUserId')
        thread_id = kwargs.get('threadId')
        text = kwargs.get('message')
        # is_post = kwargs.get('isPost')
        shareObj = kwargs.get('shareObj')

        if auth_user_id is not None:
            try: 
                User.objects.using('default').get(user_id=auth_user_id)
                try:
                    deleteThread = ChatDeleteThread.objects.using('default').filter(chat_thread_id=thread_id)
      
                    for each in deleteThread:
                        each.delete()
                except ChatDeleteThread.DoesNotExist:
                    pass
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid")
        
        if receiver_user_id is not None:
            for each in receiver_user_id:
                try: 
                    User.objects.using('default').get(user_id=each)
                except User.DoesNotExist:
                    raise NotFoundException("recipientUserId provided is not found ---"+str(each)+"-- userId", 404)
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid")
        # if text is None or text=="":
        #     raise NoContentException("text is empty")
        if shareObj:
            try:
                print(shareObj.template.type)
                shareTypeObj = ShareType.objects.using('default').get(share_type_name = shareObj.template.type)
            except ShareType.DoesNotExist:
                raise NotFoundException("shareType provided is not found")
            if shareObj.template.type =='post':
                try:
                    postObj = Post.objects.using('default').get(post_id=str(shareObj.template.id))
                except ValueError:
                    raise BadRequestException("postId provided not found")
                except Post.DoesNotExist:
                    raise NotFoundException("postId provided not found")
            elif shareObj.template.type == 'venue':
                try:
                    venueObj = Venue.objects.using('default').get(venue_id=shareObj.template.id)
                except Venue.DoesNotExist:
                    raise NotFoundException("venueId provided not found")
        else:
            raise BadRequestException("invalid request; shareObj provided is invalid")
        

        participants = []
        participants += receiver_user_id
        participants.append(auth_user_id)
        participants = list(set(sorted(participants)))
        temp_threads=[]
        following=[]

        participants_temp_thread=[]
        result=getParticipantMatch(participants)

        thread_id = result['match_thread_id']
        if thread_id is not None:

            try:
                dialog = ChatThread.objects.using('default').get(chat_thread_id=thread_id)
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")
       
            for each in participants:
                following += UserFollowing.objects.using('default').filter(following_user_id=auth_user_id, user_id=each).values_list('user_id', flat=True)

            temp_threads += ChatThread.objects.using('default').filter(created_by__in=receiver_user_id).values_list('chat_thread_id', flat=True)    
            participants_temp_thread += ChatThreadParticipant.objects.using('default').filter(chat_thread_id__in=temp_threads, user_id=auth_user_id).values_list('chat_thread_id', flat=True)
            participants_temp_thread = list(set(sorted(participants_temp_thread)))    

            if following !=[]:
                is_approved = True
            else:
                print(participants_temp_thread)
                if not participants_temp_thread ==[]:
                    print("here")
                    is_approved = True
                    
                else:
                    print("else")
                    is_approved = False

            dialog.modified = datetime.datetime.now()
            
            chat_message = ChatMessage.objects.create(
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now(),
                is_removed = False,
                # message_id = message_id,
                text = text,
                # recipient_id = list(set(sorted(receiver_user_id))),
                sender_id = auth_user_id,
                created_by = auth_user_id,
                chat_thread_id = dialog.chat_thread_id,
                share_type_id = shareTypeObj.share_type_id
            )

            for user_id in list(set(sorted(receiver_user_id))):
                chat_message_recipients=ChatMessageRecipient.objects.create(
                    chat_message_id = chat_message.chat_message_id,
                    user_id= user_id,
                    is_read = False,
                    created_by = auth_user_id,
                    created_on = datetime.datetime.now(),
                    modified_on = datetime.datetime.now(),

                )
                chat_message_recipients.save()

            try:
                deleteThread = ChatDeleteThread.objects.using('default').filter(chat_thread_id=dialog.chat_thread_id)
                print("fsd")
                print(deleteThread)
                for each in deleteThread:
                    each.delete()
            except ChatDeleteThread.DoesNotExist:
                pass
            chat_message.save()
            dialog.save()

        else :
            for each in participants:
                following += UserFollowing.objects.using('default').filter(following_user_id=auth_user_id, user_id=each).values_list('user_id', flat=True)
               
            temp_threads += ChatThread.objects.using('default').filter(created_by__in=receiver_user_id).values_list('chat_thread_id', flat=True)
            participants_temp_thread += ChatThreadParticipant.objects.using('default').filter(chat_thread_id__in=temp_threads, user_id=auth_user_id).values_list('chat_thread_id', flat=True)
            participants_temp_thread = list(set(sorted(participants_temp_thread))) 
            if following !=[]:
                is_approved = True
            else:
                print(participants_temp_thread)
                if not participants_temp_thread ==[]:
                    print("here")
                    is_approved = True
                    
                else:
                    print("else")
                    is_approved = False

            name =''
            for one in participants:
                one = User.objects.using('default').get(user_id=one)
                
                name += one.username
                if len(participants)>2:
                    name += ','
    
            admin = None
            is_group = False
            if len(participants)>2:
                name = None
                is_group = True
                admin = auth_user_id
            else:
                is_group = False
                admin = None    

            dialog = ChatThread.objects.create(
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now(),
                chat_thread_name= name,
                is_approved = is_approved,
                created_by = auth_user_id,
                is_group = is_group
            )
            dialog.save()
             
            for user_id in list(set(sorted(participants))):
                chat_thread_participants= ChatThreadParticipant.objects.create(
                    chat_thread_id = dialog.chat_thread_id,
                    user_id = user_id,
                    created_by = auth_user_id,
                    created_on = datetime.datetime.now(),
                    modified_on = datetime.datetime.now(),
                )
                chat_thread_participants.save()

            if admin:
               chat_thread_admin=ChatThreadAdmin.objects.create(
                chat_thread_id = dialog.chat_thread_id,
                user_id = admin,
                created_by = auth_user_id,
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now(),
               )   
               chat_thread_admin.save()  
               

            chat_message = ChatMessage.objects.create(
                created_on = datetime.datetime.now(),
                modified_on = datetime.datetime.now(),
                is_removed = False,
                text = text,
                sender_id = auth_user_id,
                created_by = auth_user_id,
                chat_thread_id = dialog.chat_thread_id,
                share_type_id = shareTypeObj.share_type_id
            )
            chat_message.save()

            for user_id in list(set(sorted(receiver_user_id))):
                chat_message_recipients=ChatMessageRecipient.objects.create(
                    chat_message_id = chat_message.chat_message_id,
                    user_id= user_id,
                    is_read = False,
                    created_by = auth_user_id,
                    created_on = datetime.datetime.now(),
                    modified_on = datetime.datetime.now(),

                )
                chat_message_recipients.save()

        outputMessage= ''
        sharedId = None
        if shareObj.template:
            if shareObj.template.type=='Post':
                try:
                    shareObj.template.id= int(shareObj.template.id)
                    postObj = Post.objects.using('default').get(post_id=shareObj.template.id)
                    postSharedObj = Shared.objects.using('default').create(
                        post_id = postObj.post_id,
                        sender_user_id = auth_user_id,
                        created_on = datetime.datetime.now(),
                        modified_on = datetime.datetime.now(),
                        created_by = auth_user_id
                    )
                    sharedId= postSharedObj.shared_id
                    postSharedObj.save()
                    outputMessage = "Successfully shared post attachment"
                except Post.DoesNotExist:
                    raise NotFoundException("postId provided not found")
                
            elif shareObj.template.type=='Venue':
                try:
                    venueObj = Venue.objects.using('default').get(venue_id=shareObj.template.id)
                    venueSharedObj = Shared.objects.using('default').create(
                        venue_id = venueObj.venue_id,
                        sender_user_id = auth_user_id,
                        created_on = datetime.datetime.now(),
                        modified_on = datetime.datetime.now(),
                        created_by = auth_user_id
                    )
                    sharedId= venueSharedObj.shared_id
                    venueSharedObj.save()
                    outputMessage = "Successfully shared venue attachment"
                except Venue.DoesNotExist:
                    raise NotFoundException("venueId provided not found")
            
            for user_id in list(set(sorted(receiver_user_id))):
                shared_recipients=SharedRecipient.objects.create(
                    shared_id = sharedId,
                    user_id= user_id,
                    created_by = auth_user_id,
                    created_on = datetime.datetime.now(),
                    modified_on = datetime.datetime.now(),

                )
                shared_recipients.save()
            chat_message=ChatMessage.objects.using('default').get(chat_message_id = chat_message.chat_message_id)    
            chat_message.shared_id = sharedId
            chat_message.save()        

        else:
            raise BadRequestException("invalid request; shareObj provided is invalid")

        return ChatSendMessageSharesMutation(message = outputMessage, recipient_user_id=[{"user_id": each} for each in receiver_user_id], auth_user_id=auth_user_id, message_id=chat_message.chat_message_id, sharedId=sharedId, threadId=dialog.chat_thread_id)#, attachment=AttachmentOutputObjectType(attachment.type,attachment.id))

"""
    Add Reaction to Message
"""
class AddReactionMessageMutation(graphene.Mutation):
    message = graphene.String()
    user_id = graphene.Int()
    message_id = graphene.Int()
    reaction_type_id = graphene.Int()

    class Arguments:
        messageId = graphene.Int()
        userId = graphene.Int()
        reactionTypeId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        messageId = kwargs.get('messageId')
        reactionTypeId = kwargs.get('reactionTypeId')
        if userId:
            try:
                user= User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if messageId:
            try:
                message = ChatMessage.objects.using('default').get(chat_message_id=messageId)
            except ChatMessage.DoesNotExist:
                raise NotFoundException("messageId provided not found")
        else:
            raise BadRequestException("invalid request; messageId provided is invalid")
        if reactionTypeId:
            try:
                reaction = models.ChatMessageReactionType.objects.using('default').get(chat_message_reaction_type_id=reactionTypeId)
            except models.ChatMessageReactionType.DoesNotExist:
                raise NotFoundException("reactionTypeId provided not found")
        else:
            raise BadRequestException("invalid request; reactionTypeId provided is invalid")
       
        try:
            chatMessageRecipients = ChatMessageRecipient.objects.using('default').filter(chat_message_id=messageId, user_id=userId).values_list('user_id',flat=True)
            chatMessage=ChatMessage.objects.using('default').filter(Q(chat_message_id=messageId),  Q(sender_id=userId))
            if len(chatMessageRecipients)>0 or len(chatMessage)>0:
                
                try:
                    ChatMessageReaction.objects.using('default').get(chat_message_id=messageId, user_id=userId, chat_message_reaction_type_id=reactionTypeId)
                except ChatMessageReaction.DoesNotExist:
                    chat_message_reaction_obj = ChatMessageReaction.objects.using('default').create(
                        chat_message_id = message.chat_message_id,
                        user_id = userId,
                        chat_message_reaction_type_id = reaction.chat_message_reaction_type_id,
                        created_on = datetime.datetime.now(),
                        modified_on = datetime.datetime.now(),
                        created_by = userId
                    )
                    chat_message_reaction_obj.save()

                return AddReactionMessageMutation(message="successfully added reaction to this message", message_id=messageId, user_id=userId, reaction_type_id=reactionTypeId)
            else:
                 raise AuthorizationException("userId provided is not authorized to react to this message")    
        except ChatMessage.DoesNotExist:
            raise AuthorizationException("userId provided is not authorized to react to this message")
        
"""
    Delete Reaction to message
"""      
class DeleteReactionMessageMutation(graphene.Mutation):
    message = graphene.String()
    user_id = graphene.Int()
    message_id = graphene.Int()
    reaction_type_id = graphene.Int()
    class Arguments:
        messageId = graphene.Int()
        userId = graphene.Int()
        reactionTypeId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        userId = kwargs.get('userId')
        messageId = kwargs.get('messageId')
        reactionTypeId = kwargs.get('reactionTypeId')
        if userId:
            try:
                user= User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if messageId:
            try:
                message = ChatMessage.objects.using('default').get(chat_message_id=messageId)
            except ChatMessage.DoesNotExist:
                raise NotFoundException("messageId provided not found")
        else:
            raise BadRequestException("invalid request; messageId provided is invalid")
        if reactionTypeId:
            try:
                reaction = models.ChatMessageReactionType.objects.using('default').get(chat_message_reaction_type_id=reactionTypeId)
            except models.ChatMessageReactionType.DoesNotExist:
                raise NotFoundException("reactionTypeId provided not found")
        else:
            raise BadRequestException("invalid request; reactionTypeId provided is invalid")
        
        try:
            chatMessageRecipients = ChatMessageRecipient.objects.using('default').filter(chat_message_id=messageId, user_id=userId).values_list('user_id',flat=True)
            chatMessage=ChatMessage.objects.using('default').filter(Q(chat_message_id=messageId), Q(sender_id=userId))
            if len(chatMessageRecipients)>0 or len(chatMessage)>0:
                try:
                    reaction = ChatMessageReaction.objects.using('default').get(user_id=userId, chat_message_id=messageId, chat_message_reaction_type_id=reactionTypeId)
                    reaction.delete()
                    return DeleteReactionMessageMutation(message="successfully delete the reaction ", user_id=userId, message_id=messageId, reaction_type_id=reactionTypeId)
                except ChatMessageReaction.DoesNotExist:
                    raise ConflictException("conflict in request; unable to remove reaction that is not liked")   
            else:
                 raise AuthorizationException("userId provided is not authorized to remove reaction to this message")
        except ChatMessage.DoesNotExist:
            raise AuthorizationException("userId provided is not authorized to remove reaction to this message")
            

"""
    Delete Message
"""
class DeleteMessageMutation(graphene.Mutation):
    message = graphene.String()
    userId = graphene.Int()
    message_id = graphene.Int()

    class Arguments:
        userId = graphene.Int()
        messageId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        authUserId = kwargs.get('userId')
        message_id = kwargs.get('messageId')
        if authUserId is not None:
            try:
                User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if message_id is not None:
            try:
                message = ChatMessage.objects.using('default').get(chat_message_id=message_id)
                if message.sender_id == authUserId:
                    message.delete()
                    return DeleteMessageMutation(message="successfully deleted the message", message_id=message_id, userId=authUserId)
                else:
                    raise AuthorizationException("userId provided is not authorized to delete this message")
                
            except ChatMessage.DoesNotExist:
                raise NotFoundException("messageId provided is not found")
        else:
            raise BadRequestException("invalid request; messageId provided is invalid")

"""
    Delete Chat Thread 
"""
class DeleteThreadMutation(graphene.Mutation):
    threadId = graphene.Int()
    userId = graphene.Int()
    message = graphene.String()

    class Arguments:
        userId = graphene.Int()
        threadId = graphene.Int()
    
    def mutate(self, info, **kwagrs):
        userId = kwagrs.get('userId')
        threadId = kwagrs.get('threadId')
        if userId is not None:
            try:
                user = User.objects.using('default').get(user_id=userId)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if threadId is not None:
            try:
                thread = ChatThread.objects.using('default').get(chat_thread_id=threadId)
                participants=ChatThreadParticipant.objects.using('default').filter(chat_thread_id=threadId).values_list('user_id',flat=True)
                if userId in participants: 
                    try:
                        ChatDeleteThread.objects.using('default').get(chat_thread_id=threadId, user_id=userId)
                        raise ConflictException("conflict in request; unable to delete provided thread that has already deleted")
                    except ChatDeleteThread.DoesNotExist:
                        deleted_thread = ChatDeleteThread.objects.using('default').create(
                            chat_thread_id = threadId,
                            user_id = userId,
                            created_on = datetime.datetime.now(),
                            modified_on = datetime.datetime.now(),
                            created_by = userId
                        )
                        deleted_thread.save()
                        return DeleteThreadMutation(message="successful delete thread", userId = userId, threadId = threadId)
                else:
                    raise AuthorizationException("userId provided is not authorized to delete this thread")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")
        
"""
    Add Member To Group Chat Thread
"""     
class AddMemberGroupThreadMutation(graphene.Mutation):
    authUserId = graphene.Int()
    newParticipants = graphene.List(UserIdFieldType)
    threadId = graphene.Int()
    message = graphene.String()
    alreadyParticipants = graphene.List(UserIdFieldType)

    class Arguments:
        authUserId = graphene.Int()
        threadId = graphene.Int()
        recipientUserId = graphene.List(BigInt)
    
    def mutate(self, info, **kwargs):
        auth_user_id = kwargs.get('authUserId')
        recipient_user_id = kwargs.get('recipientUserId')
        thread_id = kwargs.get('threadId')

        if auth_user_id is not None:
            try:
                User.objects.using('default').get(user_id=auth_user_id)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found")
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid")
        if recipient_user_id:
            for each in recipient_user_id:
                try: 
                    User.objects.using('default').get(user_id=each)
                except User.DoesNotExist:
                    raise NotFoundException("recipientUserId provided is not found ---"+str(each)+"-- userId", 404)
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using("default").get(chat_thread_id = thread_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                participants = list(set(sorted(participants)))
                if len(participants)<=2 and not thread.is_group:
                    raise ConflictException("conflict in request; unable to add member into a direct chat thread")
                try:
                    if auth_user_id in participants:
                        ChatThread.objects.using('default').get(chat_thread_id=thread_id)
                    else:
                        raise AuthorizationException("authUserId provided is not authorized to add member")    
                except ChatThread.DoesNotExist:
                    raise AuthorizationException("authUserId provided is not authorized to add member")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")
        
        participant_list=[]
        already_participants=[]
        for each in recipient_user_id:
            if each not in participants:
                participant_list.append(each)   
            else:
                already_participants.append(each)
        
        if len(participant_list)>0:      
            for each in participant_list:
                thread_participants=ChatThreadParticipant.objects.using('default').create(
                    chat_thread_id = thread.chat_thread_id,
                    user_id = each,
                    created_by = auth_user_id,
                    created_on = datetime.datetime.now(),
                    modified_on = datetime.datetime.now(),
                )
                thread_participants.save()
            return AddMemberGroupThreadMutation(message="Successfully added new member to chat", threadId = thread_id, authUserId=auth_user_id, newParticipants=[{"user_id": each} for each in participant_list], alreadyParticipants=[{"user_id": each} for each in already_participants])    
        else:
             raise ConflictException("conflict in request; unable to add recipientUserId is already member")

"""
    Remove Member from Group Chat Thread
"""            
class RemoveMemberGroupThreadMutation(graphene.Mutation):
    threadId = graphene.Int()
    authUserId = graphene.Int()
    recipientUserId = graphene.Int()
    message = graphene.String()

    class Arguments:
        threadId = graphene.Int()
        authUserId = graphene.Int()
        recipientUserId = graphene.Int()

    def mutate(self, info, **kwargs):
        auth_user_id = kwargs.get('authUserId')
        recipient_user_id = kwargs.get('recipientUserId')
        thread_id = kwargs.get('threadId')
        if auth_user_id is not None:
            try:
                User.objects.using('default').get(user_id=auth_user_id)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided is not found")
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid")
        if recipient_user_id is not None:
            try:
                User.objects.using('default').get(user_id=recipient_user_id)
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided is not found")
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using("default").get(chat_thread_id = thread_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                threadAdmin = ChatThreadAdmin.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                participants = list(set(sorted(participants)))
                threadAdmin = list(set(sorted(threadAdmin)))
                if len(participants)<=2 and not thread.is_group:
                    raise ConflictException("conflict in request; unable to remove user from chat")
                if auth_user_id not in threadAdmin and auth_user_id in participants:
                    raise AuthorizationException("authUserId provided is not the group admin to remove member")
                try:
                    if auth_user_id in participants:
                        ChatThread.objects.using('default').get(chat_thread_id=thread_id)
                    else:    
                        raise AuthorizationException("authUserId provided is not authorized to remove member")
                except ChatThread.DoesNotExist:
                    raise AuthorizationException("authUserId provided is not authorized to remove member")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")   
        if recipient_user_id in participants:
            thread_participant = ChatThreadParticipant.objects.using('default').get(chat_thread_id=thread_id, user_id = recipient_user_id)
            thread_participant.delete()
            return RemoveMemberGroupThreadMutation(message="Successfully removed member from chat", threadId=thread_id, authUserId=auth_user_id, recipientUserId = recipient_user_id)
        else:
            raise ConflictException("conflict in request; unable to remove member that is not present")

"""
    Change Group Photo
"""
class ChangeGroupPhotoMutation(graphene.Mutation):
    message = graphene.String()
    threadId = graphene.Int()
    userId = graphene.Int()
    avatar = graphene.String()

    class Arguments:
        threadId = graphene.Int()
        userId = graphene.Int()
        avatar = Upload()
    
    def mutate(self, info, **kwargs):
        user_id = kwargs.get('userId')
        thread_id = kwargs.get('threadId')
        avatar = kwargs.get('avatar')
        if user_id is not None:
            try:
                User.objects.using('default').get(user_id=user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using("default").get(chat_thread_id = thread_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                participants = list(set(sorted(participants)))
                if len(participants)<=2 and not thread.is_group:
                    raise ConflictException("conflict in request; unable to change photo to a direct chat thread")
                # if user_id not in thread.admin:
                #     raise AuthorizationException("userId provided is not authorized to change photo of the group")
                try:
                    if user_id in participants:
                        ChatThread.objects.using('default').get(chat_thread_id=thread.chat_thread_id)
                    else:    
                        raise AuthorizationException("userId provided is not authorized to view this thread")
                except ChatThread.DoesNotExist:
                    raise AuthorizationException("userId provided is not authorized to view this thread")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")  
        if avatar is not None:
            # last_post = Post.objects.all().aggregate(Max('post_id'))
            # print(last_post['post_id__max']+1)
            aws_link = "https://loop-cloud-bucket.s3.us-west-1.amazonaws.com/"
            folder_name = "chat-avatar/"
            file_name = "chat_avatar"+str(thread.chat_thread_id)+".jpg"
            media_link = aws_link+folder_name+file_name
            success_upload = upload_to_aws(avatar, settings.AWS_STORAGE_BUCKET_NAME, folder_name, file_name)
            print(success_upload)
            print(media_link)
            if success_upload:
                thread.avatar = media_link
                thread.save()
                return ChangeGroupPhotoMutation(message="Successfully modified the group image", userId=user_id, threadId=thread_id, avatar=media_link)
            else:
                return ChangeGroupPhotoMutation(message="upload unsuccessful",userId=user_id, threadId=thread_id, avatar=None)

"""
    Change Group Name
"""
class ChangeGroupNameMutation(graphene.Mutation):
    threadId = graphene.Int()
    userId = graphene.Int()
    name = graphene.String()
    message = graphene.String()

    class Arguments:
        userId = graphene.Int()
        threadId = graphene.Int()
        name = graphene.String()
    
    def mutate(self, info, **kwargs):
        user_id= kwargs.get('userId')
        thread_id = kwargs.get('threadId')
        name = kwargs.get('name')
        if user_id is not None:
            try:
                User.objects.using('default').get(user_id=user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided is not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using("default").get(chat_thread_id = thread_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                participants = list(set(sorted(participants)))
                if len(participants)<=2 and not thread.is_group:
                    raise ConflictException("conflict in request; unable to change name to a direct chat thread")
                try:
                    if user_id in participants:
                        ChatThread.objects.using('default').get(chat_thread_id=thread_id)
                    else:
                       raise AuthorizationException("userId provided is not authorized to view this thread")     
                except ChatThread.DoesNotExist:
                    raise AuthorizationException("userId provided is not authorized to view this thread")
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided is not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")  
        if name is not None and name.strip():
            if len(name)>24:
                raise BadRequestException("invalid request; name provided exceeded the maximum length")
            thread.chat_thread_name = name
            thread.save()
            return ChangeGroupNameMutation(message="successfullly changed the name of the group", userId = user_id, threadId = thread_id, name = name)
        else:
            raise BadRequestException("invalid request; name provided is invalid")



"""
    Accept Request Chat
"""
class AcceptRequestChatThreadMutation(graphene.Mutation):
    user_id = graphene.Int()
    thread_id = graphene.Int()
    message = graphene.String()
    class Arguments:
        userId = graphene.Int()
        threadId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        user_id = kwargs.get('userId')
        thread_id = kwargs.get('threadId')
        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id = user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using('default').get(chat_thread_id=thread_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                participants = list(set(sorted(participants)))
                if thread.is_approved:
                    raise ConflictException("conflict in request; unable to approve since thread is already approved")
                else:
                    if user_id  not in participants:
                        raise AuthorizationException("userId provided is not authorized to access this thread")
                    else:
                        thread.is_approved = True
                        thread.save()
                return AcceptRequestChatThreadMutation(message="successfully accepted the chat request", user_id=user_id, thread_id=thread_id)
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")

"""
    Decline Request Chat Thread
"""
class DeclineRequestChatThreadMutation(graphene.Mutation):
    user_id = graphene.Int()
    thread_id = graphene.Int()
    message = graphene.String()
    class Arguments:
        userId = graphene.Int()
        threadId = graphene.Int()
    
    def mutate(self, info, **kwargs):
        user_id = kwargs.get('userId')
        thread_id = kwargs.get('threadId')
        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id = user_id)
            except User.DoesNotExist:
                raise NotFoundException("userId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using('default').get(chat_thread_id=thread_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                participants = list(set(sorted(participants)))
                if user_id  not in participants:
                    raise AuthorizationException("userId provided is not authorized to view this thread")
                else:
                    if thread.is_approved:
                        raise ConflictException("conflict in request; unable to decline threadId provided that is already approved")
                    else:
                        thread.delete()
                        return DeclineRequestChatThreadMutation(message="successfully declined the chat request", user_id=user_id, thread_id=thread_id)
            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")


"""
    Assign Chat Thread Admin
"""
class AssignChatThreadAdminMutation(graphene.Mutation):
    recipient_User_Id = graphene.Int()
    thread_id = graphene.Int()
    auth_User_Id= graphene.Int()
    message = graphene.String()
    class Arguments:
        recipientUserId = graphene.Int()
        threadId = graphene.Int() 
        authUserId= graphene.Int()

    def mutate(self, info, **kwargs):
        user_id = kwargs.get('recipientUserId')
        thread_id = kwargs.get('threadId')
        admin_id = kwargs.get('authUserId')
        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id = user_id)
            except User.DoesNotExist:
                raise NotFoundException("recipientUserId provided not found")
        else:
            raise BadRequestException("invalid request; recipientUserId provided is invalid")
       
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using('default').get(chat_thread_id=thread_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                threadAdmin = ChatThreadAdmin.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                participants = list(set(sorted(participants)))
                threadAdmin = list(set(sorted(threadAdmin)))

                if admin_id is not None:          
                    if admin_id not in threadAdmin:
                        raise AuthorizationException("authUserId provided is not authorized to assign specific user as admin")
                    if user_id not in participants:
                        raise AuthorizationException("recipientUserId provided is not authorized to this group")
                    if user_id in threadAdmin:
                        return ConflictException("conflict in request; recipientUserId provided is already admin")
                    if not thread.is_group:
                        return ConflictException("conflict in request; unable to assign admin not a group chat")    
                    else:
                        thread_admin = ChatThreadAdmin.objects.using('default').create(
                             chat_thread_id = thread.chat_thread_id,
                             user_id = user_id,
                             created_by = admin_id,
                             created_on = datetime.datetime.now(),
                             modified_on = datetime.datetime.now(),

                        )
                        
                        thread_admin.save() 

                        return AssignChatThreadAdminMutation(message="Successfully assign recipientId as admin", recipient_User_Id=user_id, thread_id=thread_id, auth_User_Id=admin_id )   
                else:
                    raise BadRequestException("invalid request; authUserId provided is invalid") 

            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")            


"""
    Remove Chat Thread Admin
"""
class RemoveChatThreadAdminMutation(graphene.Mutation):
    recipient_User_Id = graphene.Int()
    thread_id = graphene.Int()
    auth_User_Id= graphene.Int()
    message = graphene.String()
    class Arguments:
        recipientUserId = graphene.Int()
        threadId = graphene.Int() 
        authUserId= graphene.Int()

    def mutate(self, info, **kwargs):
        user_id = kwargs.get('recipientUserId')
        thread_id = kwargs.get('threadId')
        admin_id = kwargs.get('authUserId')
        if user_id is not None:
            try:
                user = User.objects.using('default').get(user_id = user_id)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found")
        else:
            raise BadRequestException("invalid request; userId provided is invalid")
       
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using('default').get(chat_thread_id=thread_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id', flat=True)
                threadAdmin = ChatThreadAdmin.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                participants = list(set(sorted(participants)))
                threadAdmin = list(set(sorted(threadAdmin)))

                if admin_id is not None:
                    if admin_id not in threadAdmin:
                        raise AuthorizationException("authUserId provided is not authorized to remove specific user as admin")
                    if user_id not in participants:
                        raise AuthorizationException("recipientUserId provided is not authorized to this group")
                    if user_id not in threadAdmin:
                        return ConflictException("conflict in request; recipientUserId provided is not a admin")
                    if not thread.is_group:
                        return ConflictException("conflict in request; unable to remove admin not a group chat")
                    else:
                        thread_admin = ChatThreadAdmin.objects.using('default').get(chat_thread_id=thread_id, user_id=user_id)
                        thread_admin.delete()


                        return RemoveChatThreadAdminMutation(message="Successfully removed recipientId as admin", recipient_User_Id=user_id, thread_id=thread_id, auth_User_Id=admin_id )   
                else:
                    raise BadRequestException("invalid request; authUserId provided is invalid") 

            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid") 


"""
    Leave Chat Thread
"""
class LeaveChatThreadMutation(graphene.Mutation):
    thread_id = graphene.Int()
    auth_User_Id= graphene.Int()
    message = graphene.String()
    class Arguments:
        threadId = graphene.Int() 
        authUserId= graphene.Int()

    def mutate(self, info, **kwargs):
        thread_id = kwargs.get('threadId')
        user_id = kwargs.get('authUserId')
        if user_id is not None:
            try:
                 User.objects.using('default').get(user_id = user_id)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found")
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid")
       
        if thread_id is not None:
            try:
                thread = ChatThread.objects.using('default').get(chat_thread_id=thread_id)
                participants = ChatThreadParticipant.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id', flat=True)
                threadAdmin = ChatThreadAdmin.objects.using('default').filter(chat_thread_id=thread_id).values_list('user_id',flat=True)
                participants = list(set(sorted(participants)))
                threadAdmin = list(set(sorted(threadAdmin)))

                if user_id is not None:
                    if user_id not in participants: 
                        raise AuthorizationException("authUserId provided is not authorized to this group")
                    if user_id in threadAdmin and len(threadAdmin)<2:
                        raise ConflictException("conflict in request; unable to leave admin member; assign another user as admin")       
                    if user_id not in threadAdmin:
                        thread_participant = ChatThreadParticipant.objects.using('default').get(chat_thread_id=thread_id, user_id=user_id)
                        thread_participant.delete()
                        return LeaveChatThreadMutation(message="User has successfully left the group", thread_id=thread_id, auth_User_Id=user_id )
                    else:
                        thread_participant = ChatThreadParticipant.objects.using('default').get(chat_thread_id=thread_id, user_id=user_id)
                        thread_admin = ChatThreadAdmin.objects.using('default').get(chat_thread_id=thread_id, user_id=user_id)
                        thread_participant.delete()
                        thread_admin.delete()

                        return LeaveChatThreadMutation(message="User has successfully left the group", thread_id=thread_id, auth_User_Id=user_id )   
                else:
                    raise BadRequestException("invalid request; authUserId provided is invalid") 

            except ChatThread.DoesNotExist:
                raise NotFoundException("threadId provided not found")
        else:
            raise BadRequestException("invalid request; threadId provided is invalid")            

       


"""..................................................................................END CHAT............................................................................................."""




class Mutation(graphene.ObjectType):
    send_message = ChatSendMessageMutation.Field()
    shared_attachment = ChatSendMessageSharesMutation.Field()
    add_reaction_message = AddReactionMessageMutation.Field()
    delete_reaction_message = DeleteReactionMessageMutation.Field()
    delete_message = DeleteMessageMutation.Field()
    delete_thread = DeleteThreadMutation.Field()
    accept_chat_request = AcceptRequestChatThreadMutation.Field()
    decline_chat_request = DeclineRequestChatThreadMutation.Field()

    change_group_name = ChangeGroupNameMutation.Field()
    change_group_photo = ChangeGroupPhotoMutation.Field()

    add_chat_member = AddMemberGroupThreadMutation.Field()
    remove_chat_member = RemoveMemberGroupThreadMutation.Field()
    assign_group_chat_admin=AssignChatThreadAdminMutation.Field()
    remove_group_chat_admin= RemoveChatThreadAdminMutation.Field()
    leave_group_chat = LeaveChatThreadMutation.Field()
