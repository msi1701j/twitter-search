#!/opt/python/twitter-search/bin/python3
# -*- coding: utf-8 -*-

import requests, json
import datetime
import os
import sys

# status family
###################################
# application 
# favorites 
# followers 
# friends 
# friendships 
# geo 
# help 
# lists 
# search 
# statuses 
# trends 
# users 
###################################
#
def get_status(apikey, useragent,
	resources='application,favorites,followers,friends,friendships,geo,help,lists,search,statuses,trends,users'
				):

	Status_Endpoint = 'https://api.twitter.com/1.1/application/rate_limit_status.json'

	params = {
		'resources': resources	# help, users, search, statuses etc.
		}

	headers = {
		'Authorization':    'Bearer {}'.format(apikey),
	#       'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
		'User-Agent': useragent,
		}

	try:
		res = requests.get(Status_Endpoint, headers=headers, params=params)
		res.raise_for_status()
	except Exception as e:
		print( "Error status:", res.status_code )
		print( json.dumps(res.json(), ensure_ascii=False, indent=2) )
		return None

	return res.json()

def main():
	try:
		apikey = os.environ['TWITTER_TOKEN']
		userAgent = os.environ['TWITTER_AGENT']
	except KeyError:
		print('環境変数 TWITTER_TOKEN を設定してください。', file=sys.stderr)
		exit(1)

	#twitter_status = get_status(apikey, userAgent)
	twitter_status = get_status(apikey, userAgent, resources='search')

	if twitter_status is not None:
		print( json.dumps(twitter_status, ensure_ascii=False, indent=2) )
		print( 'reset:', datetime.datetime.fromtimestamp(twitter_status['resources']['search']['/search/tweets']['reset']) )
	else:
		exit(1)
#	resources": {
#	    "search": {
#		      "/search/tweets": {
#	          "remaining": 450,
#	          "limit": 450,
#	          "reset": 1526111078
#		        }

if __name__ == '__main__':
	main()
