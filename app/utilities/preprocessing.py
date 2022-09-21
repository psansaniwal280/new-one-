from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer 

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