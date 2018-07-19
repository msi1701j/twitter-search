#!/opt/python/twitter-search/bin/python3
# -*- coding: utf-8 -*-

from DebugTools import *
import os, sys
import argparse
import requests
from json import dumps
import datetime
import time

import csv
import shelve

DEBUG = False
VERBOSE = False
SILENCE = False

def Verbose_print( *strings ):
	if VERBOSE:
		print( *strings )


# Excel の DateValue 形式を datetime へ変換
def dateValue2datetime(datevalue):
	days = int(round(datevalue, 0))
	secs = int(round((datevalue - days) * 3600 * 24, 0))
	hour = int(round(secs / 3600, 0))
	remain = secs % 3600
	min = int(round(remain / 60))
	remain = remain % 60

	return datetime.datetime(1899, 12, 30) + datetime.timedelta(days=days, hours=hour, minutes=min, seconds=remain)


# datetime を Excel の DateValue 形式へ変換
def datetime2dateValue(datetime_obj):
	delta = datetime_obj - datetime.datetime(1899, 12, 30)
	days = delta.days
	remain = delta.seconds / 3600 / 24
	microsec_remain = delta.microseconds * 1000000 / 3600 / 24
	return days + remain + microsec_remain


# datetime をエポックタイム (UNIX タイム)へ変換
def datetime2epoch(d):
	return int(time.mktime(d.timetuple()))


# エポックタイム (UNIX タイム) を datetime へ変換
def epoch2datetime(epoch):
	return datetime.datetime(*(time.localtime(epoch)[:6]))


# ツイートの日付文字列を datetime オブジェクトに変換
def str2datetime(datestr):
	return datetime.datetime.strptime(datestr,'%a %b %d %H:%M:%S +0000 %Y')
	

# ツイートの日付文字列をエポック time (UNIX タイム) に変換
def str2epoch(datestr):
	return datetime2epoch(str2datetime(datestr))
	

# ツイートのdatetimeを日本標準時間に変換
def str_to_datetime_jp(datestr):
	dts = str2datetime(datestr)
	return (dts + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S JST")


# target_epoch_time (UNIX タイム) までの Sleep 秒を返す
def calc_sleeptime(target_epoch_time):
	sleepTime = target_epoch_time - int(round(time.time(), 0))
	Verbose_print( 'Calculated sleep seconds:', sleepTime )
	return sleepTime


# Twitter API サーチの制限を取得する
def get_status(apikey, useragent, resources='search'):

	Status_Endpoint = 'https://api.twitter.com/1.1/application/rate_limit_status.json'
	params = {
		'resources': resources  # help, users, search, statuses etc.
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
		print(type(e), file=sys.stderr)
		print( "Error status:", res.status_code, file=sys.stderr )
		if res.json() is not None:
			print( dumps(res.json(), ensure_ascii=False, indent=2), file=sys.stderr )
		return None

	return res.json()


# Twitter API サーチ
def get_search_tweets( q, apikey,
			geocode=None,
			lang=None,
			locale=None,
			result_type='recent',
			count=100,
			until=None,
			since=None,
			since_id=None,
			max_id=None,
			include_entities='false',
			useragent='-',
			next_results=None,
			interval_time=5,
			retry_max=10
			):

	global SILENCE

	Search_Endpoint = 'https://api.twitter.com/1.1/search/tweets.json'

	params = {}
	for key in (
			'geocode',
			'lang',
			'locale',
			'result_type',
			'count',
			'until',
			'since',
			'since_id',
			'max_id',
			'include_entities'
			):
		if eval(key) is not None:
			params[key] = eval(key)
	params['tweet_mode'] = 'extended'
	saved_params = params.copy()

	headers = {
		'Authorization':'Bearer {}'.format(apikey),
		'Content-Type':	'application/x-www-form-urlencoded;charset=UTF-8',
		'User-Agent':	useragent,
		}

	retry = 0
	saved_max_id = None
	while True:
		if retry == 0:
			if next_results is None:
				url = Search_Endpoint
				params['q'] = q
				saved_params = params.copy()
			else:
				url = Search_Endpoint + next_results
				params = None
		elif retry <= retry_max:
			Debug_print( 'retry =', retry )
			url = Search_Endpoint
			params = saved_params.copy()
			if saved_max_id is not None:
				params['max_id'] = saved_max_id - 1
			saved_params = params.copy()
		else:
			raise StopIteration()

		Verbose_print( 'params =', dumps(params, ensure_ascii=False, indent=2) )
		Verbose_print( 'url =', url )

		try:
			res = requests.get(url, headers=headers, params=params)
			res.raise_for_status()
		except Exception as e:
			print(type(e), file=sys.stderr)
			print( "Error status:", res.status_code, file=sys.stderr )
			if not SILENCE and res.json() is not None:
				print( dumps(res.json(), ensure_ascii=False, indent=2), file=sys.stderr )
			if res.status_code == 429 or res.status_code == 420:
				stat = get_status(apikey, useragent)
				if not SILENCE and stat is not None:
					print( dumps(stat, ensure_ascii=False, indent=2), file=sys.stderr )
				targetTime = stat['resources']['search']['/search/tweets']['reset']
				if not SILENCE:
					print( 'Target Time:', datetime.datetime.fromtimestamp(targetTime), file=sys.stderr )

				sleepTime = calc_sleeptime( targetTime )
				Debug_print( 'sleep time:', sleepTime )
				time.sleep(sleepTime + 1)
				continue

			elif res.status_code == 500 or res.status_code == 502 or res.status_code == 503 or res.status_code == 504:
				if retry > retry_max:
					Debug_print( 'retry:', retry, '>', retry_max, ', StopIteration' )
					raise StopIteration()
				retry = retry + 1
				Verbose_print( 'retrying:', retry )
				time.sleep(interval_time)
				continue

			else:
				raise StopIteration()

		entry = res.json()
		metadata = entry['search_metadata']
		last_index = -1
		for tweet in entry['statuses']:
			retry = 0
			saved_max_id = tweet['id']
			yield (tweet, metadata)
			last_index = last_index + 1

		if metadata is not None:
			Debug_print(dumps(metadata, ensure_ascii=False, indent=2))

		if 'next_results' not in metadata:
			retry = retry + 1
			if retry > retry_max:
				Debug_print( 'retry:', retry, '>', retry_max, ', StopIteration' )
				raise StopIteration()
			Verbose_print( 'retrying:', retry )
			time.sleep(interval_time * retry)
		else:
			retry = 0
			next_results = metadata['next_results']


# Shelve File key check
def get_shelve_value( shelvedb, key ):
	if shelvedb is not None:
		if key in shelvedb:
			return shelvedb[key]
	return None


# return option value if the value is not None, then return shelvedb value
# Shelve 内容よりも、option の内容が優先される
def get_shelve_value_or_option( shelvedb, key, option ):
	if option is not None:
		return option
	return get_shelve_value( shelvedb, key )


# main
def main():
	global DEBUG
	global VERBOSE
	global SILENCE
	Debug_print( __name__ )

	#####################################
	# コマンド引数確認、設定セクション
	#####################################
	parser = argparse.ArgumentParser()

	parser.add_argument('search_string', 
						help=u'検索文字列')
	parser.add_argument('-c', '--dispcount', type=int, default=0,
						help=u'表示数')
	parser.add_argument('-C', '--count', type=int, default=100,
						help=u'一度の取得数')
	parser.add_argument('-D', '--debug', action='store_true',
						help=u'Debug モード')
	parser.add_argument('-S', '--since_id', type=str, default=None,
						help=u'since_id の指定 (指定 id 含まない)')
	parser.add_argument('-M', '--max_id', type=str, default=None,
						help=u'max_id の指定 (指定 id 含む)')
	parser.add_argument('--since_date', type=str, default=None,
						help=u'since_date (since) の指定 (指定日含む)')
	parser.add_argument('--max_date', type=str, default=None,
						help=u'max_date (until) の指定 (指定日含ない)')
	parser.add_argument('-t', '--trytime', type=int, default=10,
						help=u'リトライ回数')

	parser.add_argument('-b', '--shelve', type=str, default=None,
						help=u'Shelve (パラメータ格納) ファイルの指定')
	parser.add_argument('-B', '--shelve_reset', action='store_true',
						help=u'Shelve (パラメータ格納) ファイルのリセット')

	parser.add_argument('-o', '--outputfile', type=str, default='output.csv',
						help=u'出力 CSV ファイル名')
	parser.add_argument('-O', '--outputfile_reset', action='store_true',
						help=u'出力 CSV ファイルリセット')
	parser.add_argument('-w', '--write_header', action='store_true',
						help=u'出力 CSV ファイルへヘッダタイトルを記入')



	# 排他オプション
	optgroup1 = parser.add_mutually_exclusive_group()
	optgroup1.add_argument('-v', '--verbose', action='store_true',
						help=u'Verbose 表示')
	optgroup1.add_argument('-s', '--silence', action='store_true',
						help=u'Silence 表示')


	args = parser.parse_args()

	if args.debug:
		DEBUG = True
	Debug_init(DEBUG)
	Debug_print('Debug is', DEBUG)

	if args.verbose:
		VERBOSE = True
	Debug_print('Verbose is', VERBOSE)

	if args.silence:
		SILENCE = True
	Debug_print('Silence is', SILENCE)

	shelvefile = args.shelve
	shelve_flag = 'c'
	if args.shelve_reset:
		shelve_flag = 'n'
	Debug_print( 'shelvefile: {}, flag: {}'.format(shelvefile, shelve_flag) )

	outputfile = args.outputfile
	output_mode = 'a'
	if args.outputfile_reset:
		output_mode = 'w'
	output_reset = args.outputfile_reset

	outputfile = args.outputfile
	Debug_print( 'outputfile: {}, mode: {}'.format(outputfile, output_mode) )

	write_header = args.write_header
	Debug_var_print( 'write_header', write_header )

	query_str = args.search_string
	Debug_var_print( 'query_str', query_str )

	count = args.count
	Debug_var_print( 'count', count )

	dispcount = args.dispcount
	Debug_var_print( 'dispcount', dispcount )

	since_id = args.since_id
	Debug_var_print( 'since_id', since_id )

	max_id = args.max_id
	Debug_var_print( 'max_id', max_id)

	retry_max = args.trytime
	Debug_var_print( 'retry_max', retry_max)

	since_date = args.since_date
	Debug_var_print( 'since_date', since_date )

	max_date = args.max_date
	Debug_var_print( 'max_date', max_date )


	# 環境変数確認セクション
	# TWITTER REST API TOKEN, UserAgent 設定確認
	try:
		apikey = os.environ['TWITTER_TOKEN']
		userAgent = os.environ['TWITTER_AGENT']
	except KeyError:
		print('環境変数 TWITTER_TOKEN, TWITTER_AGENT を設定してください。', file=sys.stderr)
		exit(1)

	#################################################
	if DEBUG:
		stat = get_status(apikey, userAgent)
		if stat is not None:
			print( dumps(stat, ensure_ascii=False, indent=2), file=sys.stderr )
		targetTime = stat['resources']['search']['/search/tweets']['reset']
		sleepTime = calc_sleeptime( targetTime )
		Debug_print( 'sleep time:', sleepTime )

	if shelvefile is None:
		dbase = None
	else:
		dbase = shelve.open(shelvefile, flag=shelve_flag)

	saved_max_id = get_shelve_value( dbase, 'last_id' )
	saved_since_id = get_shelve_value( dbase, 'last_id' )
	since_id = get_shelve_value_or_option( dbase, 'last_id', since_id )
	since_date = get_shelve_value_or_option( dbase, 'last_date', since_date )

	Debug_var_print( 'saved_max_id', saved_max_id )
	Debug_var_print( 'saved_since_id', saved_since_id )

	if outputfile == '-':
		csvfile = sys.stdout	# 標準出力
	else:
		csvfile = open(outputfile, mode=output_mode, newline='',encoding='utf_8_sig')

	#################################################
	tweets_generator = get_search_tweets( query_str, apikey,
						geocode=None,
						lang=None,
						locale=None,
						result_type='recent',
						count=count,
						until=max_date,
						since=since_date,
						since_id=since_id,
						max_id=max_id,
						include_entities='false',
						useragent=userAgent,
						next_results=None,
						retry_max=retry_max,
						interval_time=5
						)

	fieldnames = [
			'created_at_exceltime',
			'created_at_epoch',
			'created_at',
			'created_at_jst',
			'text',
			'id',
			'userId',
			'name',
			'screen_name',
			'fixlink',
			]
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore', quoting=csv.QUOTE_ALL)

	if write_header:
		writer.writeheader()

	myCounter = 0
	local_max_id = 0
	local_last_date = epoch2datetime(0)
	for tweet, metadata in tweets_generator:
		myCounter = myCounter + 1
		workuser = tweet['user']

		tweet_id = tweet['id']
		created_datetime = str2datetime(tweet['created_at'])

		if not SILENCE:
			print( 'get tweet: {}: {}'.format( myCounter, tweet_id ) )

		if local_max_id < tweet_id:
			local_max_id = tweet_id
			if dbase is not None:
				dbase['last_id'] = tweet_id
				dbase.sync()

		if local_last_date < created_datetime:
			local_last_date = created_datetime
			if dbase is not None:
				dbase['last_date'] = created_datetime.strftime('%Y-%m-%d')
				dbase.sync()

		if 'full_text' in tweet:
			textkey = 'full_text'
		else:
			textkey = 'text'

		Debug_print( 'textkey=', textkey )

		tj = {
			'myCounter': myCounter,
			'userId': workuser['id'],
			'name': workuser['name'],
			'screen_name': workuser['screen_name'],
			'text': tweet[textkey],
			'id': tweet['id'],
			'created_at': tweet['created_at'],
			'created_at_exceltime': datetime2dateValue(str2datetime(tweet['created_at'])),
			'created_at_epoch': str2epoch(tweet['created_at']),
			'created_at_jst': str_to_datetime_jp(tweet['created_at']),
			'fixlink': 'https://twitter.com/' + workuser['screen_name'] + '/status/' + tweet['id_str']
			}
		Verbose_print(dumps(tj, ensure_ascii=False, indent=2))
		writer.writerow(tj)

	if outputfile != '-':
		csvfile.close()
	if not SILENCE:
		print( "Total:", myCounter, "items" )


if __name__ == '__main__':
	main()
