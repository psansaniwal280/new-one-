
import math
import graphene
from app.schemas.commonObjects.objectTypes import PageInfoObject
from app.utilities.errors import *
from app.models import *
from app.schemas.postSchema.postType import PostListType,  PostPageListType
import datetime
from graphene import Date, DateTime
import pandas as pd
from django.db.models import Sum, Max
import numpy as np
from app.utilities.preprocessing import extract_hashtags, remove_hashtags, remove_stopwords, deEmojify, apply_stemming, rejoin_words 
# import nltk
# from nltk.corpus import stopwords
# from nltk.stem.porter import PorterStemmer 
import pickle
from django.db import connection
import os

class Query(graphene.ObjectType):

    #Feed Posts Queries
    followingFeed = graphene.Field(PostPageListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    discoveryFeed = graphene.List(PostListType, userId=graphene.Int(),days= graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    discoveryFeeds = graphene.List(PostListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())
    followingFeedConcat = graphene.List(PostListType, userId=graphene.Int(), page=graphene.Int(), limit=graphene.Int())

    #Get Discovery Feed for each user
    def resolve_discoveryFeed(parent, info, **kwargs):
        authUserId = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        days = kwargs.get('days')
        # if not info.context.session[id]:
        #     raise AuthorizationException("Please login to access", 401)
        # id = info.context.session[id]['userId']
        # # id = kwargs.get('userId')
        if authUserId is not None:
            try:
                user = User.objects.using('default').get(user_id=authUserId)
            except User.DoesNotExist:
                raise NotFoundException("authUserId provided not found", 404)
        else:
            raise BadRequestException("invalid request; authUserId provided is invalid", 400)
        
        if(days <= 0):
            raise BadRequestException("invalid request; Days must be greater than 0",400)
        
        # Extracting user data from database
        try:
            post_des_vectoriser = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","post_des_vectoriser"),'rb'))
            post_title_vectoriser = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","post_title_vectoriser"),'rb'))
            profile_vectoriser = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","profile_vectoriser"),'rb'))
            post_hashtag_vectoriser = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","post_hashtag_vectoriser"),'rb'))
            gender_labelBinarizer = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","gender_labelBinarizer"),'rb'))
            var_booking_binarizer = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","var_booking_binarizer"),'rb'))
            is_active_binarizer = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","is_active_binarizer"),'rb'))
            # user_status_binarizer = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","user_status_binarizer"),'rb'))
            lang_pref_encoder = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","lang_pref_encoder"),'rb'))
            # linear_regression_model = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","linear_regression_model"),'rb'))
            # SVR_model = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","SVR_model"),'rb'))
            Lin_SVR_model = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","Lin_SVR_model"),'rb'))
            # Random_Forest_Regressor = pickle.load(open(os.path.join(os.getcwd(),"app","ML_model","discoveryfeed","RandomForestRegressor"),'rb'))
        except Exception as error:
            print("Unable to load the models",error)
        
        # create database connection
        try:
            cursor = connection.cursor()
            cursor.execute("""select distinct
                                p.post_id,
                                p.venue_id,
                                p.title,
                                p.user_rating,
                                p.is_verified_booking,
                                p.post_description,
                                p.user_id,
                                count(distinct pc.post_comment_id) as post_comment,
                                count(distinct pl.post_like_id) as post_like,
                                count(distinct pd.post_disinterested_id) as post_disinterested,
                                count(distinct pvc.post_venue_click_id) as post_venue_click,
                                u.is_active,
                                u.level,
                                u."DOB",
                                up.gender_id,
                                u.user_status_id,
                                STRING_AGG (
                                    distinct upt.user_profile_tag_name ,
                                        ','
                                    ORDER BY
                                        upt.user_profile_tag_name
                                    ) as user_profile_tag_name,
                                (select d.language_preference from user_device  ud left join device d
                                on ud.device_id=d.device_id  where p.user_id=ud.user_id order by ud.created_on limit 1) as language_preference,

                                (select sum(pv.video_duration) from  post_view pv
                                where p.post_id=pv.post_id limit 1) as video_duration,

                                (select sum(EXTRACT(EPOCH FROM (pv.video_end_time  - pv.video_start_time)))  from  post_view pv
                                where p.post_id=pv.post_id) as watch_time,

                                (select a.longitude from address a where vi.address_id=a.address_id  ) as longitude,
                                (select a.latitude from address a where vi.address_id=a.address_id ) as latitude,
                                vi.venue_level_id  ,
                                vi.venue_type_id  ,
                                vi.age_restriction_id,
                                vi.venue_category_id,
                                (select vl.language_id from public.venue_languages  vl
                                where vl.venue_internal_id=vi.venue_internal_id order by vl.created_on limit 1)
                                as languages,
                                count(distinct pc.post_id) as report_post_count,
                                count(distinct ps.post_id) as post_saved_count                            

                                from post p left join post_venue_click pvc
                                on p.post_id=pvc.post_id
                                left join public.post_comment pc
                                on p.post_id=pc.post_id
                                left join public.shared s
                                on p.post_id=s.post_id
                                left join public.post_like pl
                                on p.post_id=pl.post_id
                                left join public.report_post rp
                                on p.post_id=rp.post_id 
                                left join public.post_saved ps
                                on p.post_id=ps.post_id 
                                left join public.post_disinterested pd
                                on p.post_id=pd.post_id
                                left join public.user u
                                on p.user_id=u.user_id
                                left join public.user_profile up
                                on u.user_id=up.user_id
                                left join public.user_tag ut
                                on u.user_id=ut.user_id
                                left join  public.user_profile_tag upt
                                on ut.user_profile_tag_id =upt.user_profile_tag_id
                                left join  public.venue v
                                on v.venue_id=p.venue_id
                                left join  public.venue_internal vi
                                on v.venue_id=vi.venue_id
                                left join  public.venue_type vt
                                on vt.venue_type_id=vi.venue_type_id
                                where (DATE_PART('day', current_date::timestamp - p.created_on::timestamp) <= %s)
                                group by p.post_id,
                                p.title,
                                p.user_rating,
                                p.is_verified_booking,
                                p.post_description,
                                p.user_id,
                                u.is_active,
                                u.level,
                                u."DOB",
                                up.gender_id ,
                                u.user_status_id,
                                vi.address_id,
                                p.venue_id,
                                vi.venue_level_id  ,
                                vi.venue_type_id  ,
                                vi.age_restriction_id,
                                vi.venue_category_id,
                                vi.venue_internal_id
                                order by p.post_id,p.user_id
                                ;""", [days])
            column_names_post = ['post_id','venue_id','title','user_rating','is_verified_booking','post_description',
                        'user_id','post_comment','post_like','post_disinterested','post_venue_click','is_active',
                        'level','DOB','gender_id','user_status_id','user_profile_tag_name','language_preference',
                        'video_duration','watch_time','longitude','latitude','venue_level_id','venue_type_id','age_restriction_id',
                        'venue_category_id','languages_id',
                        'report_post_count','post_saved_count']
            post_records = cursor.fetchall()
        except Exception as error:
            print("Unable to connect to the database.",error)
        post_df = pd.DataFrame(post_records, columns = column_names_post)
        convert_dict_p = {'user_rating':np.float64,
                'longitude': np.float64,
                'latitude': np.float64,
               }
        post_df = post_df.astype(convert_dict_p)
        
        if(len(post_df)<=0):
            raise BadRequestException("No post has been created in last %s days",[days])
        
        user_data = User.objects.using('default').filter(user_id = authUserId).values('user_id',
                                                                              'DOB',
                                                                              'userprofile__gender__gender_name',
                                                                              'userprofile__city__longitude',
                                                                              'userprofile__city__latitude',
                                                                              'userdevice__device__language_preference')
        user_df = pd.DataFrame.from_records(user_data)
        user_p_tag = User.objects.using('default').filter(user_id = authUserId).values('usertag__user_profile_tag__user_profile_tag_name')
        user_tag_df = pd.DataFrame.from_records(user_p_tag)
        user_tag = ''
        for i in range(0,user_tag_df.shape[0]):
            if(user_tag_df['usertag__user_profile_tag__user_profile_tag_name'][i]) is not None:
                user_tag = user_tag +','+(user_tag_df['usertag__user_profile_tag__user_profile_tag_name'][i])
        user_df['user_profile_tag'] = user_tag
        
        # Renaming the column names as per required to preprocess
        user_df.rename(columns = {'user_id':'user_id',
                                  'DOB':'DOB',
                                  'userprofile__gender__gender_name':'gender_name',
                                  'userprofile__city__longitude':'longitude',
                                  'userprofile__city__latitude':'latitude',
                                  'userdevice__device__language_preference':'language_preference',
                                  'user_profile_tag':'user_profile_tag_name'}, inplace = True)
        
        # Calculating the Age of user
        now = pd.Timestamp('now')
        user_df['DOB'] = pd.to_datetime(user_df['DOB'])    # 1
        user_df['DOB'] = user_df['DOB'].where(user_df['DOB'] < now, user_df['DOB'] -  np.timedelta64(100, 'Y'))   # 2
        user_df['age'] = (now - user_df['DOB']).astype(np.int64)    # 3
        user_df = user_df.drop(['DOB'], axis=1)
        convert_dict = {'longitude': np.float64,
                'latitude': np.float64    
            }
        user_df = user_df.astype(convert_dict)
        
        # Calculating the age from DOB of the users
        post_df['DOB'] = pd.to_datetime(post_df['DOB'])    # 1
        post_df['DOB'] = post_df['DOB'].where(post_df['DOB'] < now, post_df['DOB'] -  np.timedelta64(100, 'Y'))   # 2
        post_df['age'] = (now - post_df['DOB']).astype(np.int64) #('<m8[Y]')    # 3
        post_df = post_df.drop(['DOB'], axis=1)
        
        df_user_post= user_df.merge(post_df, how = 'cross')
        df = df_user_post.copy()
        df["language_preference_x"]=df["language_preference_x"].fillna('English')
        df["language_preference_y"]=df["language_preference_y"].fillna('English')
        df["video_duration"]=df["video_duration"].fillna(0)
        df["watch_time"]=df["watch_time"].fillna(0)
        df['age_x'] = df['age_x'].fillna(22)
        df['age_y'] = df['age_y'].fillna(22)
        df['user_profile_tag_name_y'] = df['user_profile_tag_name_y'].fillna('Not Available')
        df['venue_level_id'] = df['venue_level_id'].fillna(0)
        df['languages_id'] = df['languages_id'].fillna(0)
        df['venue_level_id'] = df['venue_level_id'].astype(np.int64)
        
        # Extracting Hashtag from the post_description column and storing in another column named as hashtags
        df['hashtags'] = df.apply(lambda x: extract_hashtags(x['post_description']), axis = 1)
      
        # preprocess post_description column
        df['post_description'] = df.apply(lambda x: remove_hashtags(x['post_description']), axis = 1) # Remove hashtags
        df['post_description'] = df.apply(lambda x: remove_stopwords(x['post_description']), axis=1)  # Remove Stopwords
        df["post_description"] = df["post_description"].apply(lambda s: deEmojify(s))                 # Remove emoji and empty string
        df['post_description'] = df.apply(lambda x: apply_stemming(x['post_description']), axis=1)  # Apply Stemming
        df['post_description'] = df.apply(lambda x: rejoin_words(x['post_description']), axis=1)    # Rejoin all words
        post_des = post_des_vectoriser.transform(df['post_description'])
        post_des = pd.DataFrame.sparse.from_spmatrix(post_des)
        col_map = {v:k for k, v in post_des_vectoriser.vocabulary_.items()}
        for col in post_des.columns:
            post_des.rename(columns={col: col_map[col]}, inplace=True)
        
        # preprocess title column
        df['title'] = df.apply(lambda x: remove_hashtags(x['title']), axis = 1) # Remove hashtags
        df['title'] = df.apply(lambda x: remove_stopwords(x['title']), axis=1)  # Remove Stopwords
        df["title"] = df["title"].apply(lambda s: deEmojify(s))                 # Remove emoji and empty string
        df['title'] = df.apply(lambda x: apply_stemming(x['title']), axis=1)    # Apply Stemming
        df['title'] = df.apply(lambda x: rejoin_words(x['title']), axis=1)      # Rejoin all words
        post_title = post_title_vectoriser.transform(df['title'])
        post_title = pd.DataFrame.sparse.from_spmatrix(post_title)
        col_map = {v:k for k, v in post_title_vectoriser.vocabulary_.items()}
        for col in post_title.columns:
            post_title.rename(columns={col: col_map[col]}, inplace=True)
        
        df['hashtags'] = df.apply(lambda x: rejoin_words(x['hashtags']), axis=1)    # Rejoin all words
        post_hashtag = post_hashtag_vectoriser.transform(df['hashtags'])
        post_hashtag = pd.DataFrame.sparse.from_spmatrix(post_hashtag)
        col_map = {v:k for k, v in post_hashtag_vectoriser.vocabulary_.items()}
        for col in post_hashtag.columns:
            post_hashtag.rename(columns={col: col_map[col]}, inplace=True)
        
        # preprocess user_profile_tag_name_x column
        df['user_profile_tag_name_x'] = df.apply(lambda x: remove_hashtags(x['user_profile_tag_name_x']), axis = 1) # Remove hashtags
        df['user_profile_tag_name_x'] = df.apply(lambda x: rejoin_words(x['user_profile_tag_name_x']), axis=1)      # Rejoin all words
        profile_x = profile_vectoriser.transform(df['user_profile_tag_name_x'])
        profile_x = pd.DataFrame.sparse.from_spmatrix(profile_x)
        col_map = {v:k for k, v in profile_vectoriser.vocabulary_.items()}
        for col in profile_x.columns:
            profile_x.rename(columns={col: col_map[col]}, inplace=True)
        
        # preprocess user_profile_tag_name_y column
        df['user_profile_tag_name_y'] = df.apply(lambda x: remove_hashtags(x['user_profile_tag_name_y']), axis = 1) # Remove hashtags
        df['user_profile_tag_name_y'] = df.apply(lambda x: rejoin_words(x['user_profile_tag_name_y']), axis=1)      # Rejoin all words
        profile_y = profile_vectoriser.transform(df['user_profile_tag_name_y'])
        profile_y = pd.DataFrame.sparse.from_spmatrix(profile_y)
        col_map = {v:k for k, v in profile_vectoriser.vocabulary_.items()}
        for col in profile_y.columns:
            profile_y.rename(columns={col: col_map[col]}, inplace=True)

        df = df.join(post_des,lsuffix='x', rsuffix='y')
        df = df.join(post_title,lsuffix='x', rsuffix='y')
        df = df.join(post_hashtag,lsuffix='x', rsuffix='y')
        df = df.join(profile_x,lsuffix='_j', rsuffix='_k')
        df = df.join(profile_y,lsuffix='_x', rsuffix='_y')  
        
        df = df.drop(['user_profile_tag_name_x','title', 'post_description', 'hashtags','user_profile_tag_name_y'], axis=1)
        gen_x = gender_labelBinarizer.transform(df.gender_name)
        df_gen_x = pd.DataFrame(gen_x)
        df_gen_x.rename(columns = {0 : 'gen_x'}, inplace = True)
        df = df.join(df_gen_x,lsuffix='x', rsuffix='y')
        df = df.drop(['gender_name'], axis=1)
        
        var_booking = var_booking_binarizer.transform(df.is_verified_booking)
        df_var_booking = pd.DataFrame(var_booking)
        df_var_booking.rename(columns = {0 : 'var_booking'}, inplace = True)
        df = df.join(df_var_booking,lsuffix='x', rsuffix='y')
        df = df.drop(['is_verified_booking'], axis=1)
        
        is_active = is_active_binarizer.transform(df.is_active)
        df_is_active = pd.DataFrame(is_active)
        df_is_active.rename(columns = {0 : 'is_active_b'}, inplace = True)
        df = df.join(df_is_active,lsuffix='x', rsuffix='y')
        df = df.drop(['is_active'], axis=1)
        
        lang_pref_x = lang_pref_encoder.transform(df.language_preference_x)
        df_lang_pref_x = pd.DataFrame(lang_pref_x)
        df_lang_pref_x.rename(columns = {0 : 'lang_pref_x'}, inplace = True)
        df = df.join(df_lang_pref_x,lsuffix='x', rsuffix='y')
        
        lang_pref_y = lang_pref_encoder.transform(df.language_preference_y)
        df_lang_pref_y = pd.DataFrame(lang_pref_y)
        df_lang_pref_y.rename(columns = {0 : 'lang_pref_y'}, inplace = True)
        df = df.join(df_lang_pref_y,lsuffix='x', rsuffix='y')
        df = df.drop(['language_preference_x','language_preference_y'], axis=1)
        
        post_id_result = []
        # # for i in range(0,df.shape[0]):
        # #     pred = linear_regression_model.predict(df[i])
        # #     if (pred>2):
        # #         posts.append(each['post_id'])
        
        # preds = linear_regression_model.predict(df)
        # preds = SVR_model.predict(df)
        preds = Lin_SVR_model.predict(df)
        # preds = Random_Forest_Regressor.predict(df)    

        for i in range(0, df.shape[0]):
            # if preds[i]>=0:
                post_id_result.append(df['post_id'][i])
        
        if id is not None:
            result = []
            try:               
                for i in post_id_result:
                    result.append(PostListType(i))  
                if result:
                    if len(result) > 0:
                        if page and limit:
                            totalPages = math.ceil(len(result) / limit)
                            if page <= totalPages:
                                start = limit * (page - 1)
                                result = result[start:start + limit]
                                return result
                            else:
                                raise BadRequestException("invalid request; page provided exceeded total")
                        elif page == limit is None:
                            return result                                                    
                        elif page is None:
                            raise BadRequestException("invalid request; limit cannot be provided without page")
                        elif limit is None:
                            raise BadRequestException("invalid request; page cannot be provided without limit")
                        else:
                            return []                              
                    else:
                        return []
            except User.DoesNotExist:
                raise NotFoundException("userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId is invalid", 400)

 #Get Following Feed for each user       
    def resolve_followingFeed(parent, info, **kwargs):
        id = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if id is not None:
            try:
                if User.objects.using('default').get(user_id=id) is not None:
                    
                    following_ids = UserFollowing.objects.using('default').filter(user_id=id).values_list('following_user_id', flat=True)
                    result = []
                    if following_ids:
                        for i in Post.objects.using('default').filter(user_id__in=following_ids).order_by('-created_on'):
                            # if i.post_id >= 49 and i.post_id <=58:
                                result.append(PostListType(i.post_id))
                    result.sort(key=lambda x:x.post_id)
                    if result:
                        if len(result) > 0:
                            if page and limit:
                                totalPages = math.ceil(len(result) / limit)
                                if page <= totalPages:
                                    start = limit * (page - 1)
                                    result = result[start:start + limit]
                                    return PostPageListType(posts=result, page_info=PageInfoObject(
                                        nextPage=page + 1 if page + 1 <= totalPages else None, limit=limit))
                                else:
                                    raise BadRequestException("invalid request; page provided exceeded total")
                            elif page == limit is None:
                                return PostPageListType(posts=result,
                                                        page_info=PageInfoObject(nextPage=None, limit=None))
                            elif page is None:
                                raise BadRequestException("invalid request; limit cannot be provided without page")
                            elif limit is None:
                                raise BadRequestException("invalid request; page cannot be provided without limit")
                        else:
                            return PostPageListType(posts=[],
                                                    page_info=PageInfoObject(nextPage=None, limit=None))
                    else:
                        return PostPageListType(posts=[],
                                                page_info=PageInfoObject(nextPage=None, limit=None))
                    
            except User.DoesNotExist:
                raise NotFoundException("userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)
    
    def resolve_followingFeedConcat(parent, info, **kwargs):
        id = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        if id is not None:
            try:
                if User.objects.using('default').get(user_id=id) is not None:
                    
                    following_ids = UserFollowing.objects.using('default').filter(user_id=id).values_list('following_user_id', flat=True)
                    result = []
                    if following_ids:
                        for i in Post.objects.using('default').filter(user_id__in=following_ids).order_by('-created_on'):
                            # if i.post_id >= 49 and i.post_id <=58:
                                result.append(PostListType(i.post_id))
                    result.sort(key=lambda x:x.post_id)
                    if result:
                        if len(result) > 0:
                            if page and limit:
                                totalPages = math.ceil(len(result) / limit)
                                if page <= totalPages:
                                    start = limit * (page - 1)
                                    result = result[start:start + limit]
                                    return result
                                else:
                                    raise BadRequestException("invalid request; page provided exceeded total")
                            elif page == limit is None:
                                return result
                            elif page is None:
                                raise BadRequestException("invalid request; limit cannot be provided without page")
                            elif limit is None:
                                raise BadRequestException("invalid request; page cannot be provided without limit")
                        else:
                            return []
                    else:
                        return []
                    
            except User.DoesNotExist:
                raise NotFoundException("userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId provided is invalid", 400)

    
    def resolve_discoveryFeeds(parent, info, **kwargs):
        id = kwargs.get('userId')
        page = kwargs.get('page')
        limit = kwargs.get('limit')
        # if not info.context.session[id]:
        #     raise AuthorizationException("Please login to access", 401)
        # id = info.context.session[id]['userId']
        # # id = kwargs.get('userId')
        if id is not None:
            result = []
            try:
                if User.objects.using('default').get(user_id=id) is not None:
                    for i in Post.objects.all().order_by('-created_on'):
                       # if i.post_id >= 32 and i.post_id <=48:
                            result.append(PostListType(i.post_id))

                    if result:
                        if len(result) > 0:
                            if page and limit:
                                totalPages = math.ceil(len(result) / limit)
                                if page <= totalPages:
                                    start = limit * (page - 1)
                                    result = result[start:start + limit]
                                    return result
                                else:
                                    raise BadRequestException("invalid request; page provided exceeded total")
                            elif page == limit is None:
                                return result                                                    
                            elif page is None:
                                raise BadRequestException("invalid request; limit cannot be provided without page")
                            elif limit is None:
                                raise BadRequestException("invalid request; page cannot be provided without limit")
                        else:
                            return []
                                                   
                    else:
                        return []
                                              
            except User.DoesNotExist:
                raise NotFoundException("userId not found", 404)
        else:
            raise BadRequestException("invalid request; userId is invalid", 400)
