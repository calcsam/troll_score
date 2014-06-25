from __future__ import division
import json
import urllib2
import itertools
import csv
from operator import itemgetter

weekSeconds = 604800
replyWindow = 86400 # one day
startTime = 1396138355 # rnadom()
measurementInterval = 1000 # seconds, about 20m

item_URL = "https://hn.algolia.com/api/v1/items/"
#print json.load(urllib2.urlopen(item_URL+"1000"))


def author_comments_URL(author, start, end):
	return "https://hn.algolia.com/api/v1/search_by_date?tags=comment,author_" + author \
		 + "&numericFilters=created_at_i>" + str(start) + ",created_at_i<" + str(end) \
		 + "&hitsPerPage=1"

def condense_comment(comment_data, important_details):
	return {variable: comment_data[variable] for variable in important_details}

def flatten_array(array2d):
	return [item for sublist in array2d for item in sublist]

def num_comments(author, start, end):
	author_URL = author_comments_URL(author, start, end)
	return json.load(urllib2.urlopen(author_URL))['nbHits']

def get_set_of_comments():
	baseString = construct_initital_query()
	print baseString
	initial_page = json.load(urllib2.urlopen(baseString))	
	comments = []
	relevant_data = initial_page
	important_details = ['objectID','author','created_at_i', 'comment_text']
	for page_num in range(0,min(5,initial_page['nbPages'])):
		page_entries = json.load(urllib2.urlopen(baseString+"&page="+str(page_num)))['hits']	
		for comment in page_entries:
			comments.append(condense_comment(comment, important_details))
	return comments

def get_authors_of_comments():
	relevant_comments = get_set_of_comments()
	for original_comment in relevant_comments:
		comment_copy = json.load(urllib2.urlopen(item_URL + str(original_comment['objectID'])))
		if comment_copy['children']:
			first_child = comment_copy['children'][0]
			print first_child
			if first_child['created_at_i'] - original_comment['created_at_i'] < replyWindow:
				original_comment['original_prior_week_comments'] = num_comments(original_comment['author'], original_comment['created_at_i'] - weekSeconds, original_comment['created_at_i']) 
				original_comment['original_subsequent_week_comments'] =  num_comments(original_comment['author'], first_child['created_at_i'], first_child['created_at_i'] + weekSeconds)
				original_comment['responder_text'] = first_child['text']
				original_comment['differential'] = original_comment['responder_subsequent_week_comments'] - original_comment['responder_prior_week_comments']
			else:
				original_comment['differential'] = 0
		else:
			original_comment['differential'] = 0
	sorted_comments = sorted(relevant_comments, key=itemgetter('differential'))
	with open('comments.csv', 'w') as f:
		writer = csv.writer(f, delimiter=',', quotechar='"')
		header = ['Responder Subsequent Week Comments', 'Responder Prior Week Comments', 'Differential', 'Comment Text', 'Response Text']
		writer.writerow(header)
		for entry in sorted_comments:
			row = [entry.get('responder_subsequent_week_comments',0), 
				entry.get('responder_prior_week_comments', 0), 
				entry.get('differential', 0), 
				entry.get('comment_text','').encode('utf-8'),
				entry.get('responder_text','').encode('utf-8')]
			writer.writerow(row)

def construct_initital_query():
	queryString = "https://hn.algolia.com/api/v1/search_by_date?"
	endTime = startTime + measurementInterval

	queryString += "tags=comment&"	
	queryString += "numericFilters=created_at_i>=%d," % startTime
	queryString += "created_at_i<=%d" % endTime 
	#queryString += ",num_comments=1"
	return queryString

get_authors_of_comments()









