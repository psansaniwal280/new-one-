import pandas as pd
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelBinarizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score 
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor 
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.svm import LinearSVR
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
import pickle
from sklearn.preprocessing import LabelEncoder
import psycopg2
import psycopg2 as pg
import random
from psycopg2.extensions import register_adapter, AsIs
psycopg2.extensions.register_adapter(np.int64, psycopg2._psycopg.AsIs)

# Creating connection to database
connection = psycopg2.connect(    user="postgres",
                                  password="oJTxJtZcWuo1",
                                  host="lexdatabasedev.ckcopyzigcyo.us-west-1.rds.amazonaws.com",
                                  port="5432",
                                  database="loopexperiencesdb")
cursor = connection.cursor()
print(connection)


user_query = """select u.user_id,u."DOB",g.gender_name,STRING_AGG ( distinct upt.user_profile_tag_name ,',' ORDER BY upt.user_profile_tag_name) as user_profile_tag_name,(select d.language_preference from user_device  ud left join device d on ud.device_id=d.device_id  where u.user_id=ud.user_id order by ud.created_on limit 1) as language_preference, (select a.longitude from city a where up.city_id=a.city_id   ) as longitude, (select a.latitude from city a where up.city_id=a.city_id ) as latitude from public.user u left join public.user_profile up on u.user_id=up.user_id left join public.user_tag ut on ut.user_id=up.user_id left join public.user_profile_tag upt on upt.user_profile_tag_id=ut.user_profile_tag_id left join public.gender g on up.gender_id=g.gender_id group  by u.user_id,u."DOB",g.gender_name,up.city_id"""


column_names = ['user_id','DOB','gender_name','user_profile_tag_name','language_preference','longitude','latitude']


cursor.execute(user_query)
user_records = cursor.fetchall()
user_df_raw = pd.DataFrame(user_records, columns = column_names)


user_df = user_df_raw.copy()
# Dropping unwanted rows from head and tail both
user_df.drop(index=user_df.index[:128],inplace=True, axis=0)
user_df.drop(index=user_df.index[-4:],inplace=True, axis=0)
# Extracting rows those does not have null values in user_profile_tag_name
user_df_500 = user_df[~user_df['user_profile_tag_name'].isnull()]


# Taking top 500 rows for training data creation

user_df_500 = user_df_500.iloc[0:500]

# Converting datatype of DOB column to datatime

user_df_500['DOB'] =  pd.to_datetime(user_df_500['DOB'])

convert_dict = {'longitude': np.float64,
                'latitude': np.float64  
               }
user_df_500 = user_df_500.astype(convert_dict)

# finding user's age form DOB

now = pd.Timestamp('now')
# user_df_500['DOB'] = pd.to_datetime(user_df_500['DOB'])    # 1
user_df_500['DOB'] = user_df_500['DOB'].where(user_df_500['DOB'] < now, user_df_500['DOB'] -  np.timedelta64(100, 'Y'))   # 2
user_df_500['age'] = (now - user_df_500['DOB']).astype('<m8[Y]')    # 3
# Dropping DOB column
user_df_500 = user_df_500.drop(['DOB'], axis=1)
# Filling missing value for language_preference column

user_df_500["language_preference"]=user_df_500["language_preference"].fillna('English')

# Creating post query

post_query = """select distinct
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
where p.post_id=pv.post_id) as wath_time,

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
;
"""


# Creating column names

column_names_post = ['post_id','venue_id','title','user_rating','is_verified_booking','post_description',
                    'user_id','post_comment','post_like','post_disinterested','post_venue_click','is_active',
                    'level','DOB','gender_id','user_status_id','user_profile_tag_name','language_preference',
                    'video_duration','watch_time','longitude','latitude','venue_level_id','venue_type_id',
                    'age_restriction_id','venue_category_id','languages_id',
                    'report_post_count','post_saved_count']
                    
# Executing query for post data extraction
cursor.execute(post_query)
post_records = cursor.fetchall()
post_df_raw = pd.DataFrame(post_records, columns = column_names_post)

# creating post_df dataframe from post_df_raw dataframe

post_df = post_df_raw.copy()

# Dropping unneccessary rows from head and tail

post_df.drop(index=post_df.index[:78],inplace=True, axis=0)
post_df.drop(index=post_df.index[-41:],inplace=True, axis=0)

# Selecting rows by excluding missing values for "user_profile_tag_name"
post_df_500 = post_df[~post_df['user_profile_tag_name'].isnull()]
# Selecting top 500 rows for training data creation
post_df_500 =post_df_500.iloc[0:500]
# Changing datatype of DOB column to pd.datetime

post_df_500['DOB'] =  pd.to_datetime(post_df_500['DOB'])

# Calculating age
now = pd.Timestamp('now')
# user_df_500['DOB'] = pd.to_datetime(user_df_500['DOB'])    # 1
post_df_500['DOB'] = post_df_500['DOB'].where(post_df_500['DOB'] < now, post_df_500['DOB'] -  np.timedelta64(100, 'Y'))   # 2
post_df_500['age'] = (now - post_df_500['DOB']).astype('<m8[Y]')    # 3

# deleting DOB column

post_df_500 = post_df_500.drop(['DOB'], axis=1)

# Converting datatype
convert_dict_p = {'user_rating':np.float64,
                'longitude': np.float64,
                'latitude': np.float64,
               }
               
post_df_500 = post_df_500.astype(convert_dict_p)

# handling missing values
post_df_500["language_preference"]=post_df_500["language_preference"].fillna('English')
post_df_500["video_duration"]=post_df_500["video_duration"].fillna(0)
post_df_500["watch_time"]=post_df_500["watch_time"].fillna(0)
post_df_500["venue_level_id"]=post_df_500["venue_level_id"].fillna(0)
post_df_500["languages_id"]=post_df_500["languages_id"].fillna(0)

post_df_500 = post_df_500.astype({'venue_type_id':np.int64,'languages_id':np.int64})

# Merging user and post to create user,post pair

df =  user_df_500.merge(post_df_500, how = 'cross')
df_250k = df.copy()
# selecting top 25000 rows to create training data

df_25k = df.iloc[0:25000]

# Removing rows where auth user and post author is same
df_final = df_25k[df_25k['user_id_x'] != df_25k['user_id_y']]

# Extracting user post interactions

engine = pg.connect("dbname='loopexperiencesdb' user='postgres' host='lexdatabasedev.ckcopyzigcyo.us-west-1.rds.amazonaws.com' port='5432' password='oJTxJtZcWuo1'")
df_post_like = pd.read_sql('select user_id,post_id from post_like', con=engine)
df_post_comment = pd.read_sql('select user_id,post_id from post_comment', con=engine)
df_post_saved = pd.read_sql('select user_id,post_id from post_saved', con=engine)
df_post_disinterested = pd.read_sql('select user_id,post_id from post_disinterested', con=engine)
df_user_follower = pd.read_sql('select user_id,follower_user_id from user_follower', con=engine)
df_post_view = pd.read_sql('select user_id,post_id from post_view', con=engine)
df_booking_purchase = pd.read_sql('select user_id, venue_id from booking_purchase', con=engine)


i_post_like = []
for each in df_final.index:
    i_post_like.append(len( df_post_like[(df_post_like['user_id']==df_final['user_id_x'][each]) & (df_post_like['post_id']==df_final['post_id'][each])]))
    i_post_comment.append(len( df_post_comment[(df_post_comment['user_id']==df_final['user_id_x'][each]) & (df_post_comment['post_id']==df_final['post_id'][each])]))
    i_post_saved.append(len( df_post_saved[(df_post_saved['user_id']==df_final['user_id_x'][each]) & (df_post_saved['post_id']==df_final['post_id'][each])]))
    i_post_disinterested.append(len( df_post_disinterested[(df_post_disinterested['user_id']==df_final['user_id_x'][each]) & (df_post_disinterested['post_id']==df_final['post_id'][each])]))
    i_user_follower.append(len( df_user_follower[(df_user_follower['user_id']==df_final['user_id_x'][each]) & (df_user_follower['follower_user_id']==df_final['user_id_y'][each])]))
    i_post_view.append(len( df_post_view[(df_post_view['user_id']==df_final['user_id_x'][each]) & (df_post_view['post_id']==df_final['post_id'][each])]))
    i_booking_purchase.append(len( df_booking_purchase[(df_booking_purchase['user_id']==df_final['user_id_x'][each]) & (df_booking_purchase['venue_id']==df_final['venue_id'][each])]))
    
df_final['i_post_like'] = i_post_like
df_final['i_post_comment'] = i_post_comment
df_final['i_post_saved'] = i_post_saved
df_final['i_post_disinterested'] = i_post_disinterested
df_final['i_user_follower'] = i_user_follower
df_final['i_post_view'] = i_post_view
df_final['i_booking_purchase'] = i_booking_purchase


df_final['rel_score'] =10 * df_final['i_post_like']+ 6 * df_final['i_post_comment']+ 10 * df_final['i_post_saved']-10 * df_final['i_post_disinterested']+6 * df_final['i_user_follower']-10 * df_final['i_post_view']

df_final['hashtags'] = df_final.apply(lambda x: extract_hashtags(x['post_description']), axis = 1)

df = df_final.copy()

df.reset_index(inplace = True,drop=True)

df['post_description'] = df.apply(lambda x: remove_hashtags(x['post_description']), axis = 1) # Remove hashtags
df['post_description'] = df.apply(lambda x: remove_stopwords(x['post_description']), axis=1)  # Remove Stopwords
df["post_description"] = df["post_description"].apply(lambda s: deEmojify(s))                 # Remove emoji and empty string
df['post_description'] = df.apply(lambda x: apply_stemming(x['post_description']), axis=1)  # Apply Stemming
df['post_description'] = df.apply(lambda x: rejoin_words(x['post_description']), axis=1)    # Rejoin all words

# preprocess title column
df['title'] = df.apply(lambda x: remove_hashtags(x['title']), axis = 1) # Remove hashtags
df['title'] = df.apply(lambda x: remove_stopwords(x['title']), axis=1)  # Remove Stopwords
df["title"] = df["title"].apply(lambda s: deEmojify(s))                 # Remove emoji and empty string
df['title'] = df.apply(lambda x: apply_stemming(x['title']), axis=1)    # Apply Stemming
df['title'] = df.apply(lambda x: rejoin_words(x['title']), axis=1)      # Rejoin all words

df['hashtags'] = df.apply(lambda x: rejoin_words(x['hashtags']), axis=1)    # Rejoin all words

user_tag=pd.DataFrame()
user_tag['profile_tag'] = df['user_profile_tag_name_x'] +' '+df['user_profile_tag_name_y']

# preprocess user_profile_tag_name_x column
df['user_profile_tag_name_x'] = df.apply(lambda x: remove_hashtags(x['user_profile_tag_name_x']), axis = 1) # Remove hashtags
df['user_profile_tag_name_x'] = df.apply(lambda x: rejoin_words(x['user_profile_tag_name_x']), axis=1)      # Rejoin all words

# preprocess user_profile_tag_name_y column
df['user_profile_tag_name_y'] = df.apply(lambda x: remove_hashtags(x['user_profile_tag_name_y']), axis = 1) # Remove hashtags
df['user_profile_tag_name_y'] = df.apply(lambda x: rejoin_words(x['user_profile_tag_name_y']), axis=1)      # Rejoin all words


post_des_vectoriser = TfidfVectorizer(analyzer='word')
post_des_vectoriser.fit(df['post_description'])
pickle.dump(post_des_vectoriser, open('post_des_vectoriser', 'wb'))
# Using TfidfVectorizer to vectorize post_description column and adding it to df_test dataframe
post_des = post_des_vectoriser.transform(df['post_description'])
post_des = pd.DataFrame.sparse.from_spmatrix(post_des)
col_map = {v:k for k, v in post_des_vectoriser.vocabulary_.items()}
for col in post_des.columns:
    post_des.rename(columns={col: col_map[col]}, inplace=True)
df = df.join(post_des,lsuffix='x', rsuffix='y')



post_title_vectoriser = TfidfVectorizer(analyzer='word')
post_title_vectoriser.fit(df['title'])
pickle.dump(post_title_vectoriser, open('post_title_vectoriser', 'wb'))
# Using TfidfVectorizer to vectorize title column and adding it to df_test dataframe
post_title = post_title_vectoriser.transform(df['title'])
post_title = pd.DataFrame.sparse.from_spmatrix(post_title)
col_map = {v:k for k, v in post_title_vectoriser.vocabulary_.items()}
for col in post_title.columns:
    post_title.rename(columns={col: col_map[col]}, inplace=True)
df = df.join(post_title,lsuffix='x', rsuffix='y')


post_hashtag_vectoriser = TfidfVectorizer(analyzer='word')
post_hashtag_vectoriser.fit(df['hashtags'])
pickle.dump(post_hashtag_vectoriser, open('post_hashtag_vectoriser', 'wb'))
# Using TfidfVectorizer to vectorize hashtags column and adding it to df_test dataframe
post_hashtag = post_hashtag_vectoriser.transform(df['hashtags'])
post_hashtag = pd.DataFrame.sparse.from_spmatrix(post_hashtag)
col_map = {v:k for k, v in post_hashtag_vectoriser.vocabulary_.items()}
for col in post_hashtag.columns:
    post_hashtag.rename(columns={col: col_map[col]}, inplace=True)
df = df.join(post_hashtag,lsuffix='x', rsuffix='y')

profile_vectoriser = TfidfVectorizer(analyzer='word')
profile_vectoriser.fit(user_tag['profile_tag'])
pickle.dump(profile_vectoriser, open('profile_vectoriser', 'wb'))
# Using TfidfVectorizer to vectorize user_profile_tag_name_x column and adding it to df_test dataframe
# profile_x = profile_vectoriser.transform(df['user_profile_tag_name_x'])
# profile_x = pd.DataFrame.sparse.from_spmatrix(profile_x)
# col_map = {v:k for k, v in profile_vectoriser.vocabulary_.items()}
# for col in profile_x.columns:
#     profile_x.rename(columns={col: col_map[col]}, inplace=True)
# df = df.join(profile_x, lsuffix='_x', rsuffix='_y')

# Using TfidfVectorizer to vectorize user_profile_tag_name_y column and adding it to df_test dataframe
profile_y = profile_vectoriser.transform(df['user_profile_tag_name_y'])
profile_y = pd.DataFrame.sparse.from_spmatrix(profile_y)
col_map = {v:k for k, v in profile_vectoriser.vocabulary_.items()}
for col in profile_y.columns:
    profile_y.rename(columns={col: col_map[col]}, inplace=True)
df= df.join(profile_y,lsuffix='_x', rsuffix='_y')

# delete unneccessary columns from df
df = df.drop(['user_profile_tag_name_x','title', 'post_description', 'hashtags','user_profile_tag_name_y'], axis=1)

gender_labelBinarizer = LabelBinarizer().fit(df.gender_name)
pickle.dump(gender_labelBinarizer, open('gender_labelBinarizer', 'wb'))
# Binarize the gender_name_x column
gen_x = gender_labelBinarizer.transform(df.gender_name)
df_gen_x = pd.DataFrame(gen_x) 
df_gen_x.rename(columns = {0 : 'gen_x'}, inplace = True)
df = df.join(df_gen_x,lsuffix='x', rsuffix='y')
df = df.drop(['gender_name'], axis=1)

var_booking_binarizer = LabelBinarizer().fit(df.is_verified_booking)
pickle.dump(var_booking_binarizer, open('var_booking_binarizer', 'wb'))
# Binarize the is_verified_booking column
var_booking = var_booking_binarizer.transform(df.is_verified_booking)
df_var_booking = pd.DataFrame(var_booking)
df_var_booking.rename(columns = {0 : 'var_booking'}, inplace = True)
df= df.join(df_var_booking,lsuffix='x', rsuffix='y')
df= df.drop(['is_verified_booking'], axis=1)


is_active_binarizer = LabelBinarizer().fit(df.is_active)
pickle.dump(is_active_binarizer, open('is_active_binarizer', 'wb'))
# Binarize the is_active column
is_active = is_active_binarizer.transform(df.is_active)
df_is_active = pd.DataFrame(is_active)
df_is_active.rename(columns = {0 : 'is_active_b'}, inplace = True)
df = df.join(df_is_active,lsuffix='x', rsuffix='y')
df = df.drop(['is_active'], axis=1)


lang_pref_encoder = LabelEncoder().fit(df.language_preference_y)
pickle.dump(lang_pref_encoder, open('lang_pref_encoder', 'wb'))
# Encoding language_preference_x
lang_pref_x = lang_pref_encoder.transform(df.language_preference_x)
df_lang_pref_x = pd.DataFrame(lang_pref_x)
df_lang_pref_x.rename(columns = {0 : 'lang_pref_x'}, inplace = True)
df = df.join(df_lang_pref_x,lsuffix='x', rsuffix='y')
df = df.drop(['language_preference_x'], axis=1)

# Encoding language_preference_y
lang_pref_y = lang_pref_encoder.fit_transform(df.language_preference_y)
df_lang_pref_y = pd.DataFrame(lang_pref_y)
df_lang_pref_y.rename(columns = {0 : 'lang_pref_y'}, inplace = True)
df = df.join(df_lang_pref_y,lsuffix='x', rsuffix='y')
df = df.drop(['language_preference_y'], axis=1)


# divide the columns in features and label
Y = df['rel_score']
X = df.drop(['rel_score','i_post_like','i_post_comment','i_post_disinterested','i_post_saved','i_user_follower','i_post_view','i_booking_purchase'],axis = 1)


# divide dataset into train, valid and test datasets
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, random_state=1)
X_train, X_valid, y_train, y_valid = train_test_split(X_train, y_train, test_size=0.3, random_state=1)


# Create models and run on data and calculate the RMSE and R2 Score
#Creating LinearRegression model
LR_model = LinearRegression()
LR_model.fit(X_train,y_train)
pickle.dump(LR_model, open('linear_regression_model', 'wb'))
score_dataset(X_train,X_valid,y_train,y_valid, LR_model)




def extract_hashtags(text):
     
    # initializing hashtag_list variable
    hashtag_list = []
     
    # splitting the text into words
    for word in text.split():
         
        # checking the first character of every word
        if word[0] == '#':
             
            # adding the word to the hashtag_list
            hashtag_list.append(word[1:])
    return hashtag_list


def remove_hashtags(text):
     
    # initializing hashtag_list variable
    word_list = []
     
    # splitting the text into words
    for word in text.split():
         
        # checking the first character of every word
        if word[0] != '#':
             
            # adding the word to the hashtag_list
            word_list.append(word)
    return word_list
    
    
def remove_stopwords(tokenized_column):
    """Return a list of tokens with English stopwords removed. 

    Args:
        column: Pandas dataframe column of tokenized data from tokenize()

    Returns:
        tokens (list): Tokenized list with stopwords removed.

    """
    stops = set(stopwords.words("english"))
    return [word for word in tokenized_column if not word in stops]
    
    
def deEmojify(inputString):
    word_list = []
    for word in inputString:
        if len(word) > 0:             #removing empty string
            word_list.append(word.encode('ascii', 'ignore').decode('ascii'))
    return word_list
    

def apply_stemming(tokenized_column):
    """Return a list of tokens with Porter stemming applied.

    Args:
        column: Pandas dataframe column of tokenized data with stopwords removed.

    Returns:
        tokens (list): Tokenized list with words Porter stemmed.

    """

    stemmer = PorterStemmer() 
    return [stemmer.stem(word) for word in tokenized_column]
    
    
def rejoin_words(tokenized_column):
    """Rejoins a tokenized word list into a single string. 
    
    Args:
        tokenized_column (list): Tokenized column of words. 
        
    Returns:
        string: Single string of untokenized words. 
    """
    
    return ( " ".join(tokenized_column))
    
    
def score_dataset(X_train,X_valid,y_train,y_valid, input_model):
    model = input_model
    #model.fit(X_train,y_train)
    preds = model.predict(X_valid)
    srt = np.sqrt(mean_squared_error(y_valid, preds))
    r2 = r2_score(y_valid, preds)
    print("srt: ",srt,"       r2: ",r2)