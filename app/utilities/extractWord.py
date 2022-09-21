# import the regex module
import re

# function to print all the hashtags in a text
def extract_tags_mentions(text):
	if text == None:
		return ([], [])
	# the regular expression
	regex_hashtag = "#(\w+)"
	regex_mention = "@(\w+)"
	
	# extracting the hashtags
	hashtag_list = re.findall(regex_hashtag, text)
	mentioned_list = re.findall(regex_mention, text)

	#cast every word into a lower case words.
	for i in range(len(hashtag_list)):
		hashtag_list[i] = hashtag_list[i].lower()

	# return list of hashtag words and mention words
	return (hashtag_list, mentioned_list)