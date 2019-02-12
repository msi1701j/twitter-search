#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

import datetime
import time
from dateutil.tz import *

import configparser
import argparse
import os

import requests
from base64 import b64encode
import json
import csv

import shelve

DEBUG = False
VERBOSE = False
SILENCE = False

def Debug_print( *strings ):
    if DEBUG:
        print( 'Debug:', *strings, file=sys.stderr )

                
def Verbose_print( *strings ):
    if VERBOSE:
        print( *strings )


def dateValue2datetime(datevalue):
    """Excel の DateValue 形式を datetime へ変換"""
    days = int(round(datevalue, 0))
    secs = int(round((datevalue - days) * 3600 * 24, 0))
    hour = int(round(secs / 3600, 0))
    remain = secs % 3600
    min = int(round(remain / 60))
    remain = remain % 60

    return datetime.datetime(1899, 12, 30) + datetime.timedelta(days=days, hours=hour, minutes=min, seconds=remain)


def datetime2dateValue(datetime_obj):
    """datetime を Excel の DateValue 形式へ変換"""
    delta = datetime_obj - datetime.datetime(1899, 12, 30)
    days = delta.days
    remain = delta.seconds / 3600 / 24
    microsec_remain = delta.microseconds / 1000000 / 3600 / 24
    return days + remain + microsec_remain


def datetime2epoch(d):
    """datetime (UTC) をエポックタイム (UNIX タイム)へ変換"""
    #UTC を localtime へ変換
    dl = d.replace(tzinfo=tzutc()).astimezone(tzlocal())
    return int(time.mktime(dl.timetuple()))


def epoch2datetime(epoch):
    """エポックタイム (UNIX タイム) を datetime (localtime) へ変換"""
    return datetime.datetime(*(time.localtime(epoch)[:6]))


def str2datetime(datestr):
    """ツイートの日付(UTC)文字列を datetime オブジェクトに変換"""
    return datetime.datetime.strptime(datestr,'%a %b %d %H:%M:%S +0000 %Y')
    

def str2epoch(datestr):
    """ツイートの日付(UTC)文字列をエポック time (UNIX タイム) に変換"""
    return datetime2epoch(str2datetime(datestr))
    

def str_to_datetime_jp(datestr):
    """ツイートのdatetimeを日本標準時間に変換"""
    dts = str2datetime(datestr)
    return (dts + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S JST")


class Config:
    """ 設定保持するクラス """

    __Default_ConfigFile = './twsearch.ini'
    __Default_Config = {
        'AppName': 'Twitter-Search',
        'AppVersion': '2.0',
        'ConsumerAPIKey': '-',
        'ConsumerAPISecret': '-',
        'ShelveFile': './twsearch.shelve',
        'OutputFile': './twsearch.json'
    }

    def __init__(self):
        self.__argparams = {}
        self.__configfile = self.__Default_ConfigFile
        self.__argparse()
        
        if not os.path.exists(self.__configfile):
            raise Exception('No such file: ' + self.__configfile)
            
        self.__config = configparser.ConfigParser()
        self.__config.read(self.__configfile)
            
        if 'DEFAULT' not in self.__config:
            raise Exception('Required "DEFAULT" section')
            exit()

        self.__params = {}
        for key in self.__Default_Config:
            lkey = key.lower()
            self.__params[lkey] = self.__Default_Config[key]

        default_section = self.__config['DEFAULT']
        for key in default_section:
            key = key.lower()
            Debug_print('default_section: ', key, ':', default_section[key])
            self.__params[key] = default_section[key]

        self.__mydict = {} 
        for key in self.__params:
            key = key.lower()
            self.__mydict[key] = self.__params[key]
        for key in self.__argparams:
            key = key.lower()
            self.__mydict[key] = self.__argparams[key]
        
        if DEBUG:
            for key in self.__mydict:
                Debug_print('__mydict[\'' + key +'\'] = ', self.__mydict[key])

    def __argparse(self):
        global DEBUG
        global VERBOSE
        global SILENCE
        self.__configfile = self.__Default_ConfigFile
    
        parser = argparse.ArgumentParser()

        # オプションの設定
        parser.add_argument('search_string', 
                            help=u'検索文字列 or ID (-i オプションで指定)')
        parser.add_argument('-l', '--localno', action='store_true',
                            help=u'ローカル No.')
        parser.add_argument('-c', '--dispcount', type=int, default=0,
                            help=u'表示数')
        parser.add_argument('-C', '--count', type=int, default=100,
                            help=u'一度の取得数')
        parser.add_argument('-D', '--debug', action='store_true',
                            help=u'Debug モード')
        parser.add_argument('-S', '--since_id', type=str,
                            help=u'since_id の指定 (指定 id 含まない)')
        parser.add_argument('-M', '--max_id', type=str,
                            help=u'max_id の指定 (指定 id 含む)')
        parser.add_argument('--since_date', type=str,
                            help=u'since_date (since) の指定 (指定日含む)')
        parser.add_argument('--max_date', type=str,
                            help=u'max_date (until) の指定 (指定日含ない)')
        parser.add_argument('-t', '--trytime', type=int, default=10,
                            help=u'リトライ回数')
        parser.add_argument('-b', '--shelve', type=str,
                            help=u'Shelve (パラメータ格納) ファイルの指定')
        parser.add_argument('-B', '--shelve_reset', action='store_true',
                            help=u'Shelve (パラメータ格納) ファイルのリセット')
        parser.add_argument('-o', '--outputfile', type=str,
                            help=u'出力 (CSV|JSON) ファイル名')
        parser.add_argument('-O', '--outputfile_reset', action='store_true',
                            help=u'出力 (CSV|JSON) ファイルリセット')
        parser.add_argument('-w', '--write_header', action='store_true',
                            help=u'出力 CSV ファイルへヘッダタイトルを記入')
        parser.add_argument('-j', '--write_json', action='store_true',
                            help=u'JSON 出力')
        parser.add_argument('-i', '--id', action='store_true',
                            help=u'get Tweet as ID')
        parser.add_argument('-I', '--inifile', type=str, default=self.__Default_ConfigFile,
                            help=u'設定ファイルの指定')
        parser.add_argument('-f', '--dummy', action='store_true',
                            help=u'dummy オプション')

        # 排他オプション
        optgroup1 = parser.add_mutually_exclusive_group()
        optgroup1.add_argument('-v', '--verbose', action='store_true',
                            help=u'Verbose 表示')
        optgroup1.add_argument('-s', '--silence', action='store_true',
                            help=u'Silence 表示')

        args = parser.parse_args()
        
        if args.debug:
            self.__argparams['DEBUG'.lower()] = True
            DEBUG = True
        Debug_print('Debug is', DEBUG)
        if args.verbose:
            self.__argparams['VERBOSE'.lower()] = True
            VERBOSE = True
        Debug_print('Verbose is', VERBOSE)
        if args.silence:
            self.__argparams['SILENCE'.lower()] = True
            SILENCE = True
        Debug_print('Silence is', SILENCE)

        self.__argparams['shelve_flag'] = 'c'
        if args.shelve_reset:
            self.__argparams['shelve_flag'.lower()] = 'n'
        if args.shelve is not None:
            self.__argparams['ShelveFile'.lower()] = args.shelve
            Debug_print( 'shelvefile: {}, flag: {}'.format(self.__argparams['ShelveFile'.lower()], self.__argparams['shelve_flag'.lower()]) )
        else:
            Debug_print( 'shelvefile: {}, flag: {}'.format('N/A', self.__argparams['shelve_flag'.lower()]) )

        self.__argparams['output_mode'.lower()] = 'a'
        if args.outputfile_reset:
            self.__argparams['output_mode'.lower()] = 'w'
        self.__argparams['outputfile_reset'.lower()] = args.outputfile_reset
        if args.outputfile:
            self.__argparams['OutputFile'.lower()] = args.outputfile
            Debug_print( 'outputfile: {}, mode: {}'.format(self.__argparams['OutputFile'.lower()], self.__argparams['output_mode'.lower()]) )
        else:
            Debug_print( 'outputfile: {}, mode: {}'.format('N/A', self.__argparams['output_mode']) )

        self.__argparams['write_header'.lower()] = args.write_header
        Debug_print( 'write_header: ', self.__argparams['write_header'.lower()] )

        self.__argparams['search_string'.lower()] = args.search_string
        Debug_print( 'search_string: ', self.__argparams['search_string'.lower()] )

        self.__argparams['count'.lower()] = args.count
        Debug_print( 'count: ', self.__argparams['count'.lower()] )

        self.__argparams['dispcount'.lower()] = args.dispcount
        Debug_print( 'dispcount: ', self.__argparams['dispcount'.lower()] )

        self.__argparams['since_id'.lower()] = args.since_id
        Debug_print( 'since_id: ', self.__argparams['since_id'.lower()] )

        self.__argparams['max_id'.lower()] = args.max_id
        Debug_print( 'max_id: ', self.__argparams['max_id'.lower()] )

        self.__argparams['retry_max'.lower()] = args.trytime
        Debug_print( 'retry_max: ', self.__argparams['retry_max'.lower()] )

        self.__argparams['since_date'.lower()] = args.since_date
        Debug_print( 'since_date: ', self.__argparams['since_date'.lower()] )

        self.__argparams['max_date'.lower()] = args.max_date
        Debug_print( 'max_date: ', self.__argparams['max_date'.lower()] )

        self.__argparams['localno'.lower()] = args.localno
        Debug_print( 'localno: ', self.__argparams['localno'.lower()] )

        self.__argparams['write_json'.lower()] = args.write_json
        Debug_print( 'write_json: ', self.__argparams['write_json'.lower()] )

        self.__argparams['search_id'.lower()] = args.id
        Debug_print( 'search_id: ', self.__argparams['search_id'.lower()] )
        
        self.__argparams['configfile'.lower()] = args.inifile
        self.__configfile = args.inifile
        Debug_print( 'configfile: ', self.__argparams['configfile'.lower()] )
        
    def argparams(self, key):
        if key.lower() in self.__argparams:
            return self.__argparams[key.lower()]
        return None
    
    def params(self, key):
        if key.lower() in self.__params:
            return self.__params[key.lower()]
        return None
    
    def __getitem__(self, key):
        if key.lower() in self.__mydict:
            return self.__mydict[key.lower()]
        raise KeyError(key)
        
    def __setitem__(self, key, value):
        self.__mydict[key.lower()] = value
        
    def __contains__(self, key):
        return key.lower() in self.__mydict


#from abc import ABCMeta
#class Tweets(metaclass=ABCMeta):
class Tweets:
    """ Tweets を取得する基底クラス """
    __Invalid_Param_Error = 195
    __Auth_Error = 99
    
    def __init__(self, config, endpoint, default_params, resource_family='search', resource='/search/tweets'):
        self.__UserAgent = config['AppName']
        self.__Bearer = self.__getBearer(config['ConsumerAPIKey'], config['ConsumerAPISecret'])
        self.__params = {}
        self.__Endpoint = endpoint
        self.__Default_Params = default_params.copy()
        self.__Resource_Family = resource_family
        self.__Resource = resource
        self.__params = default_params.copy()
        
    def __getBearer(self, apikey, apisec):
        cred = self.__getCredential(apikey, apisec)
        Token_Endpoint = 'https://api.twitter.com/oauth2/token'
        headers = {
                'Authorization': 'Basic ' + cred,
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'User-Agent': self.__UserAgent
                }
        data = {
                'grant_type': 'client_credentials',
                }

        try:
                r = requests.post( Token_Endpoint, data=data, headers=headers )
                r.raise_for_status()
        except Exception as e:
                print(type(e), file=sys.stderr)
                print( "Error status:", r.status_code, file=sys.stderr )
                print( json.dumps(r.json(), ensure_ascii=False, indent=2), file=sys.stderr )
                return None

        rjson = r.json()
        return rjson['access_token']

    @staticmethod
    def __getCredential(apikey, apisec):
        s = apikey + ':' + apisec
        bcred = b64encode(s.encode('utf-8'))
        return bcred.decode()

    def __get_limit_status(self):
        Status_Endpoint = 'https://api.twitter.com/1.1/application/rate_limit_status.json'
        params = {
            'resources': self.__Resource_Family  # help, users, search, statuses etc.
        }
        headers = {
            'Authorization':'Bearer {}'.format(self.__Bearer),
            'User-Agent': self.__UserAgent
        }
        try:
            res = requests.get(Status_Endpoint, headers=headers, params=params)
            res.raise_for_status()
        except Exception as e:
            print(type(e), file=sys.stderr)
            print( "Error status:", res.status_code, file=sys.stderr )
            if res.json() is not None:
                print( json.dumps(res.json(), ensure_ascii=False, indent=2), file=sys.stderr )
            return None

        return res.json()

    @staticmethod
    def __calc_sleeptime(target_epoch_time):
        """target_epoch_time (UNIX タイム) までの Sleep 秒を返す"""
        sleepTime = target_epoch_time - int(round(time.time(), 0))
        Verbose_print( 'Calculated sleep seconds:', sleepTime )
        return sleepTime

    def wait_reset(self):
        status = self.__get_limit_status()
        Debug_print(json.dumps(status, ensure_ascii=False, indent=2))
        remaining = status['resources'][self.__Resource_Family][self.__Resource]['remaining']
        if remaining == 0:
            targetTime = status['resources'][self.__Resource_Family][self.__Resource]['reset']
            sleepTime = self.__calc_sleeptime( targetTime ) + 10 # 念のため、10 秒加算
            Debug_print( 'targetTime:', epoch2datetime(targetTime), ', sleepTime:', sleepTime)
            sys.stderr.flush()
            sys.stdout.flush()
            time.sleep(sleepTime)

    def set_param(self, key, value):
        if key in self.__params:
            self.__params[key] = value
        
    def set_params(self, given_params):
        if given_params is None:
            self.__params = None
        else:
            for key in given_params:
                self.__params[key] = given_params[key]

    def get_params(self):
        return self.__params

    def get(self, url, retry_max, interval_time):
        retry = 0
        params = self.__params.copy()

        headers = {
            'Authorization':'Bearer {}'.format(self.__Bearer),
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'User-Agent':   self.__UserAgent,
        }

        while retry < retry_max:
            Debug_print( 'params = ', json.dumps(params, ensure_ascii=False, indent=2) )

            res = requests.get(url, headers=headers, params=params)
            if res.status_code == 500 or res.status_code == 502 or res.status_code == 503 or res.status_code == 504:
                Verbose_print( 'retrying:', retry + 1)
                time.sleep(interval_time)
                retry += 1
                Verbose_print( 'retrying:', retry + 1)
                continue
            elif res.status_code == 403:
                brk = False
                for err in errors:
                    code = err['code']
                    if code == self.__Invalid_Param_Erro:
                        # "message": "Missing or invalid url parameter."
                        brk = True
                if brk:
                    raise Exception
                time.sleep(interval_time)
                retry += 1
                Verbose_print( 'retrying:', retry + 1)
                continue
            elif res.status_code == 401:
                # self.__Auth_Error:
                # Error status: 403
                # {
                #   "errors": [
                #     {
                #       "label": "authenticity_token_error",
                #       "code": 99,
                #       "message": "Unable to verify your credentials"
                #     }
                #   ]
                # }
                print('Auth Error', file=sys.stderr)
                raise Exception('Auth Error')
            else:
                return res

    @staticmethod
    def get_simple_hashtags(entities_hashtags):
        hashtags = []
        for ent in entities_hashtags:
            hashtags.append(ent['text'])
        return hashtags


class Tweets_By_Search(Tweets):
    """ Twitter を検索するクラス """
    __Default_Params = {
        'q': '',
        'result_type': 'recent',
        'count': 100,
        'since_id': 0,
        'include_entities': 'false',
        'tweet_mode': 'extended'
    }

    __Resource_Family = 'search'
    __Resource = '/search/tweets'
    __Search_Endpoint = 'https://api.twitter.com/1.1/search/tweets.json'
        
    def __init__(self, config):
        super().__init__(
            config, 
            self.__Search_Endpoint, 
            self.__Default_Params, 
            resource_family=self.__Resource_Family, 
            resource=self.__Resource
        )
        
    def __set_params(self, given_params):
        super().set_params(given_params)
        
    def __set_param(self, key, value):
        super().set_param(key, value)

    def __get_params(self):
        return super().get_params()
        
    def generator(self, given_params, retry_max=10, interval_time=5):
        Debug_print('given_params: ', given_params)
        self.__set_params(given_params)
        saved_params = self.__get_params()
        Debug_print('saved_params: ', saved_params)

        retry = -1
        local_retry_max = 1
        saved_max_id = None
        next_results = None
        url = self.__Search_Endpoint
        while retry < local_retry_max:
            res = False
            try:
                res = super().get(url, retry_max=retry_max, interval_time=interval_time)
            except Exception as e:
                if res:
                    resj = res.json()
                    errors = resj['errors']
                    for err in errors:
                        Debug_print( 'errors in generator:', json.dumps(resj, ensure_ascii=False, indent=2) )

                    if res.status_code == 429 or res.status_code == 420:
                        self.wait_reset()
                        retry = -1
                        continue
                else:
                    raise StopIteration()
                    return None
            
            entry = res.json()
            if res.status_code == 429 or res.status_code == 420:
                errors = entry['errors']
                Debug_print( 'errors in generator:', json.dumps(entry, ensure_ascii=False, indent=2) )
                for err in errors:
                    print( 'status_code ', res.status_code, ', errors: ', json.dumps(err, ensure_ascii=False, indent=2) )
                # {
                #   "errors": [
                #     {
                #       "code": 88,
                #       "message": "Rate limit exceeded"
                #     }
                #   ]
                # }
                self.wait_reset()
                retry = -1
                continue

            Debug_print('status_code:', res.status_code)
            Debug_print('entry:', entry)
            if 'search_metadata' not in entry:
                print('status_code:', res.status_code, file=sys.stderr)
                print('"search_metadata" is not in res: res.json() = ', json.dumps(entry, ensure_ascii=False, indent=2), file=sys.stderr)
                retry = retry + 1
                Verbose_print( 'retrying:', retry )
                time.sleep(interval_time * retry)
                continue
                
            metadata = entry['search_metadata']
            for tweet in entry['statuses']:
                saved_max_id = tweet['id']
                yield (tweet, metadata)

            if metadata is not None:
                Debug_print('metadata: ', json.dumps(metadata, ensure_ascii=False, indent=2))
                pass

            if 'next_results' not in metadata:
                retry = retry + 1
                Verbose_print( 'retrying:', retry )
                time.sleep(interval_time * retry)
            else:
                next_results = metadata['next_results']
                self.__set_param('max_id', saved_max_id - 1)
                url = self.__Search_Endpoint + next_results
                params = None
                retry = -1

        Debug_print( 'retry:', retry, '>', local_retry_max, ', StopIteration' )
        raise StopIteration()


class CSV_Writer:
    def __init__(self, config):
        if outputfile == '-':
            if write_json:
                jsonfile = sys.stdout
            else:
                csvfile = sys.stdout    # 標準出力
        else:
            if write_json:
                jsonfile = open(outputfile, mode=output_mode, newline='',encoding='utf_8')
            else:
                csvfile = open(outputfile, mode=output_mode, newline='',encoding='utf_8_sig')


class Splunk_Writer:
    """ Splunk 読み込み用に Tweet 毎に metadata を付加して書き込むための基底クラス """
    def __init__(self, config):
        self.__local_last_id = 0
        self.__local_last_date = epoch2datetime(0)
        self.__dbasename = config['ShelveFile'.lower()]
        self.__outfilename = config['OutputFile'.lower()]
        self.__outfile_open_mode = config['output_mode']
        self.__outfp = '-'
        self.__is_localno = False
        self.__is_json = config['write_json']
        self.__is_write_header = config['write_header']
        
        if self.__dbasename is None:
            self.__dbase = None
        else:
            shelve_flag = config['shelve_flag']
            self.__dbase = shelve.open(self.__dbasename, flag=shelve_flag, writeback=True)
            for key in ('since_id', 'since_date'):
                key = key.lower()
                Debug_print('shelve: ', key, ': ', self.__get_shelve_value(key))
                if config[key] is None:
                    config[key] = self.__get_shelve_value(key)
        
        if self.__is_json:
            outfile_encoding = 'utf_8'
        else:
            outfile_encoding = 'utf_8_sig'

        if self.__outfilename == '-':
            self.__outfp = sys.stdout
        else:
            self.__outfp = open(self.__outfilename, mode=self.__outfile_open_mode, newline='',encoding=outfile_encoding)

    # Shelve File key check
    def __get_shelve_value( self, key ):
        if self.__dbase is not None:
            if key in self.__dbase:
                return self.__dbase[key]
        return None

    # @abstractmethod
    def generate(self, config):
        pass

    def convert(self, tweet, metadata, counter=-1):
        Debug_print('local_last_id: ', self.__local_last_id, ', local_last_date: ', self.__local_last_date)
        if self.__local_last_id < metadata['max_id']:
            self.__local_last_id = metadata['max_id']
            if self.__dbase is not None:
                Debug_print('dbase writing: ', metadata['max_id'])
                self.__dbase['since_id'] = metadata['max_id']
                self.__dbase.sync()

        if not tweet:
            return

        now = datetime.datetime.now()

        tweet_id = tweet['id']
        created_datetime = str2datetime(tweet['created_at'])
        workuser = tweet['user']

        if self.__local_last_date < created_datetime:
            self.__local_last_date = created_datetime
            if self.__dbase is not None:
                Debug_print('dbase writing: ', created_datetime.strftime('%Y-%m-%d'))
                self.__dbase['since_date'] = created_datetime.strftime('%Y-%m-%d')
                self.__dbase.sync()


        if not SILENCE:
            print( 'get tweet: {}: {} - {}'.format( counter, tweet_id, created_datetime ) )

        tj = {
            'created_time': str2epoch(tweet['created_at']),
            'base': {
                'created_at': tweet['created_at'],
                'created_at_exceltime': datetime2dateValue(str2datetime(tweet['created_at'])),
                'created_at_epoch': str2epoch(tweet['created_at']),
                'created_at_jst': str_to_datetime_jp(tweet['created_at']),
                },
            'tweet': tweet,
            'search_metadata': metadata
            }

        if self.__is_localno:
            tj['base']['gettime'] = datetime2dateValue(now)
            tj['base']['localno'] = myCounter

        #Verbose_print(json.dumps(tj, indent=2, ensure_ascii=False))
        self.__write( tj )

    def flush(self):
        self.__outfp.flush()

    def __write(self, tweet_json):
        if self.__is_json:
            print(json.dumps(tweet_json, indent=2, ensure_ascii=False), file=self.__outfp)
            return

        # Not JSON, but CSV file
        Debug_print('Not JSON')
        fieldnames = [ 'created_at_exceltime', 'created_at_epoch', 'created_at', 'created_at_jst',
                        'text', 'extended_text', 'hashtags', 'id', 'userId', 'name', 'screen_name', 'fixlink', ]
        writer = csv.DictWriter(self.__outfp, fieldnames=fieldnames, extrasaction='ignore', quoting=csv.QUOTE_ALL)
        if self.__is_write_header:
            writer.writeheader()
            self.__outfp.flush()

        tweet = tweet_json['tweet']

        workuser = tweet['user']

        if 'full_text' in tweet:
            textkey = 'full_text'
        else:
            textkey = 'text'

        if 'extended_tweet' in tweet:
            extended_tweet = tweet['extended_tweet']
            extended_full_text = extended_tweet['full_text']
        else:
            extended_tweet = {}
            extended_full_text = ""

        entities = {'hashtags': [{'text': ''}]}
        if 'entities' in tweet:
            entities = tweet['entities']
        Debug_print( 'entities=', entities )

        Debug_print( 'textkey=', textkey )

        tj = {
            'userId': workuser['id'],
            'name': workuser['name'],
            'screen_name': workuser['screen_name'],
            'text': str(tweet[textkey]),
            'extended_full_text': str(extended_full_text),
            'hashtags': ','.join(Tweets.get_simple_hashtags(entities['hashtags'])),
            'id': tweet['id'],
            'created_at': tweet['created_at'],
            'created_at_exceltime': datetime2dateValue(str2datetime(tweet['created_at'])),
            'created_at_epoch': str2epoch(tweet['created_at']),
            'created_at_jst': str_to_datetime_jp(tweet['created_at']),
            'fixlink': 'https://twitter.com/' + workuser['screen_name'] + '/status/' + tweet['id_str']
            }
        if self.__is_localno:
            tj['gettime'] = datetime2dateValue(now)
            tj['localno'] = myCounter

        Verbose_print(json.dumps(tj, ensure_ascii=False, indent=2))
        writer.writerow(tj)


class Splunk_Writer_By_Search(Splunk_Writer):
    """ Splunk 用に Twitter を検索して取得するクラス """
    def __init__(self, config):
        super().__init__(config)

    def generate(self, config):
        query = config['search_string']
        params = {'q': query}
        since_id = config['since_id']
        if since_id is not None:
            params['since_id'] = since_id
        since_date = config['since_date']
        if since_date is not None:
            params['since_date'] = since_date
        twbs = Tweets_By_Search(config)
        tweets_generator = twbs.generator(params)
        counter = 0
        for tweet, metadata in tweets_generator:
            counter += 1
            super().convert(tweet, metadata, counter)
    

if __name__ == '__main__':
    config = Config()
    Debug_print(config['AppName'])
    sw = Splunk_Writer_By_Search(config)
    sw.generate(config)
