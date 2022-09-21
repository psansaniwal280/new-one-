
from app.models import *
from django.db.models import Count

def getParticipantMatch(participants):

    participants_list =(ChatThreadParticipant.objects
                .values('chat_thread_id')
                .annotate(count=Count('user_id'))
                .order_by()
            )

    matchCount = [uid for uid in participants_list if uid['count']==len(participants)]
    result={'match_thread_id':None,'user_list':[]}
    for data in matchCount:
        userList=ChatThreadParticipant.objects.using('default').filter(chat_thread_id=data['chat_thread_id']).values_list('user_id',flat=True)
        userList=list(set(sorted(userList))) 
        if userList == participants:
            result={'match_thread_id':data['chat_thread_id'],'user_list':userList}
        else:    
            pass
    return result    

def getParticipantContains(userId):   
    allParticipants = ChatThreadParticipant.objects.using('default').values('chat_thread_id','user_id')
    result=[]
    for data in allParticipants:
        if data['user_id'] == userId:
            result.append({'chat_thread_id':data['chat_thread_id'],'user_id':data['user_id']})
        else:
            pass    

    return result





