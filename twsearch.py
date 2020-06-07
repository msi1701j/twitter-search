#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""twsearch.py"""

import sys
import logging
import shelve
import json
import csv
import datetime
import argparse
import re

from janome.tokenizer import Tokenizer

from tslib import TwsConfig
from tslib import Tweets
from tslib import epoch2datetime, \
            str2datetime, str2epoch, datetime2datevalue, str_to_datetime_jp

APP_NAME = "twsearch"
APP_VERSION = "v0.3.0"
DEFAULT_CONFIG_FILE = APP_NAME + ".ini"

SEARCH_ENDPOINT = 'https://api.twitter.com/1.1/search/tweets.json'
SEARCH_FAMILY = 'search'
SEARCH_RESOURCE = '/search/tweets'

GETID_ENDPOINT = "https://api.twitter.com/1.1/statuses/show.json"
GETID_FAMILY = "statuses"
GETID_RESOURCE = "statuses/show"

class TweetsBySearch(Tweets):
    """ Twitter を検索するクラス """
    __Default_Params = {
        'q': '',
        'result_type': 'recent',
        'count': 100,
        'since_id': 0,
        'include_entities': 'false',
        'tweet_mode': 'extended'
    }

    __Resource_Family = SEARCH_FAMILY
    __Resource = SEARCH_RESOURCE
    __Search_Endpoint = SEARCH_ENDPOINT

    def __init__(self, config: "TwsConfig",
                 endpoint=__Search_Endpoint,
                 default_params=__Default_Params,
                 resource_family=__Resource_Family,
                 resource=__Resource):
        super().__init__(
            config=config,
            endpoint=endpoint,
            default_params=default_params,
            resource_family=resource_family,
            resource=resource
        )


    def disp_limit_status(self):
        """Rate Limit 情報の表示"""
        gls_json = self.get_limit_status()
        print(json.dumps(gls_json, indent=2, ensure_ascii=False))

#{
#  "rate_limit_context": {
#    "application": "dummykey"
#  },
#  "resources": {
#    "search": {
#      "/search/tweets": {
#        "limit": 450,
#        "remaining": 0,
#        "reset": 1590937633
#      }
#    }
#  }
#}
        resources = gls_json['resources']['search']['/search/tweets']
        limit = resources['limit']
        remaining = resources['remaining']
        reset = resources['reset']
        e2d = epoch2datetime(reset)
        print(f"limit: {limit}")
        print(f"remaining: {remaining}")
        print(f"reset: {reset}")
        print(f"reset(epoch2datetime): {e2d}")


class _CSVWriter:   # unused in current
    """ CSV 書き出し用クラス """
    def __init__(self, config: "TwsConfig"):
        self.outputfile = config['outputfile']
        self.write_json = config['write_json']
        self.output_mode = config['output_mode']
        if self.outputfile == '-':
            if self.write_json:
                self.jsonfile = sys.stdout
            else:
                self.csvfile = sys.stdout    # 標準出力
        else:
            if self.write_json:
                self.jsonfile = open(self.outputfile,
                                     mode=self.output_mode, newline='', encoding='utf_8')
            else:
                self.csvfile = open(self.outputfile,
                                    mode=self.output_mode, newline='', encoding='utf_8_sig')

class SplunkWriter:
    """ Splunk 読み込み用に Tweet 毎に metadata を付加して書き込むための基底クラス """
    def __init__(self, config):
        self.config = config
        self.logger = config.logger
        self.__local_last_id = 0
        self.__local_last_date = epoch2datetime(0)
        self.__dbasename = config['ShelveFile'.lower()]
        self.__outfilename = config['OutputFile'.lower()]
        self.__outfile_open_mode = config['output_mode']
        self.__outfp = '-'
        self.__is_localno = False
        self.__is_json = config['write_json']
        self.__is_write_header = config['write_header']
        self.__write_header_yet = True
        self.__is_wakati = config['wakati']

        if config['getstatus']:
            return

        if self.__is_wakati:
            if config['user_simpledic'] is None:
                self._tokenizer = Tokenizer()
            else:
                self._tokenizer = Tokenizer(config['user_simpledic'], udic_type='simpledic', udic_enc='utf8')

        if config['search_id'] is None:
            if self.__dbasename is None:
                self.__dbase = None
            else:
                shelve_flag = config['shelve_flag']
                self.logger.debug("self.__dbasename: %s, shelve_flag: %s",
                                  self.__dbasename, shelve_flag)
                try:
                    self.__dbase = shelve.open(self.__dbasename, flag=shelve_flag, writeback=True)
                except Exception as e:
                    print("Cannot open {}".format(self.__dbasename), file=sys.stderr)
                    sys.exit(255)
                for key in ('since_id', 'since_date'):
                    key = key.lower()
                    self.logger.debug("shelve: %s: %s", key, self.__get_shelve_value(key))
                    if config[key] is None:
                        config[key] = self.__get_shelve_value(key)

        if self.__is_json:
            outfile_encoding = 'utf_8'
        else:
            outfile_encoding = 'utf_8_sig'

        if self.__outfilename == '-':
            self.__outfp = sys.stdout
        else:
            self.__outfp = open(self.__outfilename, mode=self.__outfile_open_mode,
                                newline='', encoding=outfile_encoding)

    def __del__(self):
        if self.__outfilename != '-' and self.__outfp != '-':
            self.__outfp.close()

        
    def disp_limit_status(self):
        """Rate Limit 情報の表示"""
        twbs = TweetsBySearch(self.config)
        return twbs.disp_limit_status()

    # Shelve File key check
    def __get_shelve_value(self, key):
        if self.__dbase is not None:
            if key in self.__dbase:
                return self.__dbase[key]
        return None

    def get_one_tweet(self):
        twbs = TweetsBySearch(self.config,
                              endpoint=GETID_ENDPOINT,
                              resource_family=GETID_FAMILY,
                              resource=GETID_RESOURCE)
        return twbs.get_one_tweet(self.config['search_id'])

    # @abstractmethod
    def generate(self, config):
        """レコード生成メソッド"""
        pass    # ignore

    def wakati_convert(self, text):
        """Text を分かち書きにする"""
        all_text = re.sub(r'[\n\t\s]+', ' ', text)
        # 分かち書きに変換
        # Not implemented yet
        wakati_text = ' '.join(self._tokenizer.tokenize(all_text, wakati=True))
        return wakati_text

    def convert(self, tweet, metadata, counter=-1):
        """時刻変換、追加、レコードの書き込み"""
        if self.config['search_id'] is None:
            self.logger.debug("local_last_id: %d, local_last_date: %s",
                              self.__local_last_id, self.__local_last_date)
            if self.__local_last_id < metadata['max_id']:
                self.__local_last_id = metadata['max_id']
                if self.__dbase is not None:
                    self.logger.debug("dbase writing: %s", metadata['max_id'])
                    self.__dbase['since_id'] = metadata['max_id']
                    self.__dbase.sync()

        if not tweet:
            return

        now = datetime.datetime.now()

        # tweet_id = tweet['id']
        created_datetime = str2datetime(tweet['created_at'])
        # workuser = tweet['user']

        if self.config['search_id'] is None:
            if self.__local_last_date < created_datetime:
                self.__local_last_date = created_datetime
                if self.__dbase is not None:
                    self.logger.debug("dbase writing: %s", created_datetime.strftime('%Y-%m-%d'))
                    self.__dbase['since_date'] = created_datetime.strftime('%Y-%m-%d')
                    self.__dbase.sync()

#        if not SILENCE:
#            print('get tweet: {}: {} - {}'.format(counter, tweet_id, created_datetime))

        tweet_dict = {
            'created_time': str2epoch(tweet['created_at']),
            'base': {
                'created_at': tweet['created_at'],
                'created_at_exceltime': datetime2datevalue(str2datetime(tweet['created_at'])),
                'created_at_epoch': str2epoch(tweet['created_at']),
                'created_at_jst': str_to_datetime_jp(tweet['created_at']),
                },
            'tweet': tweet,
            'search_metadata': metadata
            }

        # 分かち書きの処理
        if self.__is_wakati:
            tmp_dict = dict()
            textkey = 'text'
            if 'full_text' in tweet:
                textkey = 'full_text'
            tmp_dict['text'] = self.wakati_convert(tweet[textkey])

            if 'extended_tweet' in tweet:
                tmp_dict['extended_text'] = self.wakati_convert(tweet['extended_tweet']['full_text'])

            wakati_tweet_dict = {
                'wakati': tmp_dict
                }
            tweet_dict.update(wakati_tweet_dict)

        if self.__is_localno:
            tweet_dict['base']['gettime'] = datetime2datevalue(now)
            tweet_dict['base']['localno'] = counter

        self.__write(tweet_dict)

    def flush(self):
        """出力ファイルの flush"""
        self.__outfp.flush()

    def __write(self, tweet_json):
        if self.__is_json:
            print(json.dumps(tweet_json, indent=2, ensure_ascii=False), file=self.__outfp)
            return

        # Not JSON, but CSV file
        self.logger.debug("Not JSON")
        fieldnames = [
            'created_at_exceltime', 'created_at_epoch', 'created_at', 'created_at_jst',
            'text', 'extended_text', 'hashtags', 'id', 'userId', 'name', 'screen_name', 'fixlink',
            'wakati_text', 'wakati_extended_text'
            ]
        writer = csv.DictWriter(self.__outfp, fieldnames=fieldnames,
                                extrasaction='ignore', quoting=csv.QUOTE_ALL)
        if self.__is_write_header and self.__write_header_yet:
            writer.writeheader()
            self.__outfp.flush()
            self.__write_header_yet = False

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
        self.logger.debug("entities = %s", entities)

        self.logger.debug("textkey = %s", textkey)

        if self.__is_wakati:
            wakati = tweet_json['wakati']
            wakati_text = wakati['text']
            wakati_extended_text = wakati['extended_text'] if 'extended_text' in wakati else ''
        else:
            wakati_text = ''
            wakati_extended_text = ''
            
            

        tweet_dict = {
            'userId': workuser['id'],
            'name': workuser['name'],
            'screen_name': workuser['screen_name'],
            'text': str(tweet[textkey]),
            'extended_full_text': str(extended_full_text),
            'hashtags': ','.join(Tweets.get_simple_hashtags(entities['hashtags'])),
            'id': tweet['id'],
            'created_at': tweet['created_at'],
            'created_at_exceltime': datetime2datevalue(str2datetime(tweet['created_at'])),
            'created_at_epoch': str2epoch(tweet['created_at']),
            'created_at_jst': str_to_datetime_jp(tweet['created_at']),
            'fixlink': 'https://twitter.com/' + workuser['screen_name'] + \
                                                    '/status/' + tweet['id_str'],
            'wakati_text': wakati_text,
            'wakati_extended_text': wakati_extended_text
            }
        if self.__is_localno:
            tweet_dict['gettime'] = tweet_json['base']['gettime']
            tweet_dict['localno'] = tweet_json['base']['localno']

        self.logger.debug("writing dict: %s", json.dumps(tweet_dict, ensure_ascii=False, indent=2))
        writer.writerow(tweet_dict)


class SplunkWriterBySearch(SplunkWriter):
    """ Splunk 用に Twitter を検索して取得するクラス """
#    def __init__(self, config):
#        super().__init__(config)

    def generate(self, config):
        if config['search_id'] is None:
            query = config['search_string']
            params = {'q': query}
            for key in ('since_id', 'since_date', 'max_id', 'max_date', 'count'):
                value = config[key]
                self.logger.debug("in generate, key: %s, value %s", key, value)
                if value is not None:
                    params[key] = value

        if config['search_id'] is None:
            twbs = TweetsBySearch(config)
            tweets_generator = twbs.generator(params, retry_max=config['retry_max'],
                                              interval_time=config['interval_time'],
                                              dispcount=config['dispcount'])
            counter = 0
            for tweet, metadata in tweets_generator:
                counter += 1
                super().convert(tweet, metadata, counter)
        else:   # config['search_id' is not None
            twbs = TweetsBySearch(self.config,
                                  endpoint=GETID_ENDPOINT,
                                  resource_family=GETID_FAMILY,
                                  resource=GETID_RESOURCE)
            tweet = twbs.get_one_tweet(config['search_id'])
            self.convert(tweet, metadata={}, counter=1)


def tw_argparse():
    """コマンドライン引数の Parse"""

    parser = argparse.ArgumentParser()

    # オプションの設定
    parser.add_argument('search_string', nargs='*', default=[],
                        help=u'検索文字列 or ID (-i オプションで指定)')
    parser.add_argument('-l', '--localno', action='store_true',
                        help=u'ローカル No.')
    parser.add_argument('-c', '--dispcount', type=int, default=-1,
                        help=u'表示数')
    parser.add_argument('-C', '--count', type=int, default=100,
                        help=u'一度の取得数 (デフォルト 100 (最大値))')
    parser.add_argument('-S', '--since_id', type=str, default=None,
                        help=u'since_id の指定 (指定 id 含まない)')
    parser.add_argument('-M', '--max_id', type=str, default=None,
                        help=u'max_id の指定 (指定 id 含む)')
    parser.add_argument('--since_date', type=str, default=None,
                        help=u'since_date (since) の指定 (指定日含む)')
    parser.add_argument('--max_date', type=str, default=None,
                        help=u'max_date (until) の指定 (指定日含ない)')
    parser.add_argument('-t', '--retry_max', type=int, default=5,
                        help=u'リトライ回数 (デフォルト 5)')
    parser.add_argument('-b', '--shelvefile', type=str,
                        help=u'Shelve (パラメータ格納) ファイルの指定')
    parser.add_argument('-B', '--shelve_reset', action='store_true',
                        help=u'Shelve (パラメータ格納) ファイルのリセット')
    parser.add_argument('-o', '--outputfile', type=str,
                        help=u'出力 (CSV|JSON) ファイル名')
    parser.add_argument('-O', '--outputfile_reset', action='store_true',
                        help=u'出力 (CSV|JSON) ファイルリセット (不指定時はファイルに追記)')
    parser.add_argument('-w', '--write_header', action='store_true',
                        help=u'出力 CSV ファイルへヘッダタイトルを記入')
    parser.add_argument('-j', '--write_json', action='store_true',
                        help=u'JSON 出力')
    parser.add_argument('-i', '--id', type=str, default=None,
                        help=u'get Tweet as ID')
    parser.add_argument('-I', '--inifile', type=str, default=DEFAULT_CONFIG_FILE,
                        help=u'設定ファイルの指定 (デフォルトは {})'.format(DEFAULT_CONFIG_FILE) + \
                        u'ディレクトリの指定は環境変数CUSTOM_CONFIG_DIR')
    parser.add_argument('-f', '--dummy', action='store_true',
                        help=u'dummy オプション')
    parser.add_argument('-d', '--dryrun', action='store_true',
                        help=u'Dry Run, no execution')
    parser.add_argument('-g', '--getstatus', action='store_true',
                        help=u'limit status 情報を取得・表示して終了')
    parser.add_argument('--wakati', action='store_true',
                        help=u'Tweet 本文を分かち書きにする')

    # 排他オプション
    optgroup1 = parser.add_mutually_exclusive_group()
    optgroup1.add_argument('-v', '--verbose', action='store_true',
                           help=u'Verbose 表示 (logging INFO レベル)')
    optgroup1.add_argument('-s', '--silence', action='store_true',
                           help=u'Silence 表示')
    optgroup1.add_argument('-D', '--debug', action='store_true',
                           help=u'Debug モード')

    args = parser.parse_args()

    argparams = dict()

    argparams['logging_level'] = logging.WARN
    logging.basicConfig(level=logging.WARN)

    argparams['DEBUG'.lower()] = args.debug
    if args.debug:
        argparams['logging_level'] = logging.DEBUG
        logging.basicConfig(level=logging.DEBUG)
    logging.debug('Debug is %s', args.debug)

    argparams['VERBOSE'.lower()] = args.verbose
    if args.verbose:
        argparams['logging_level'] = logging.INFO
        logging.basicConfig(level=logging.INFO)
    logging.debug('Verbose is %s', args.verbose)

    argparams['SILENCE'.lower()] = args.silence
    if args.silence:
        argparams['logging_level'] = logging.ERROR
        logging.basicConfig(level=logging.ERROR)
    logging.debug('Silence is %s', args.silence)


    argparams['shelve_flag'] = 'c'
    if args.shelve_reset:
        argparams['shelve_flag'.lower()] = 'n'
    if args.shelvefile is not None:
        argparams['ShelveFile'.lower()] = args.shelvefile
        logging.debug('shelvefile: %s, flag: %s',
                      argparams['ShelveFile'.lower()],
                      argparams['shelve_flag'.lower()])
    else:
        logging.debug('shelvefile: %s, flag: %s', 'N/A', argparams['shelve_flag'.lower()])

    argparams['output_mode'.lower()] = 'a'
    if args.outputfile_reset:
        argparams['output_mode'.lower()] = 'w'
    argparams['outputfile_reset'.lower()] = args.outputfile_reset
    if args.outputfile:
        argparams['OutputFile'.lower()] = args.outputfile
        logging.debug('outputfile: %s, mode: %s',
                      argparams['OutputFile'.lower()],
                      argparams['output_mode'.lower()])
    else:
        logging.debug('outputfile: %s, mode: %s', 'N/A', argparams['output_mode'])

    argparams['write_header'.lower()] = args.write_header
    logging.debug('write_header: %s', argparams['write_header'.lower()])

    argparams['search_string'.lower()] = ' '.join(args.search_string)
    logging.debug('search_string: %s', argparams['search_string'.lower()])

    argparams['count'.lower()] = args.count
    logging.debug('count: %s', argparams['count'.lower()])

    argparams['dispcount'.lower()] = args.dispcount
    logging.debug('dispcount: %s', argparams['dispcount'.lower()])

    argparams['since_id'.lower()] = args.since_id
    logging.debug('since_id: %s', argparams['since_id'.lower()])

    argparams['max_id'.lower()] = args.max_id
    logging.debug('max_id: %s', argparams['max_id'.lower()])

    argparams['retry_max'.lower()] = args.retry_max
    logging.debug('retry_max: %s', argparams['retry_max'.lower()])

    argparams['since_date'.lower()] = args.since_date
    logging.debug('since_date: %s', argparams['since_date'.lower()])

    argparams['max_date'.lower()] = args.max_date
    logging.debug('max_date: %s', argparams['max_date'.lower()])

    argparams['localno'.lower()] = args.localno
    logging.debug('localno: %s', argparams['localno'.lower()])

    argparams['write_json'.lower()] = args.write_json
    logging.debug('write_json: %s', argparams['write_json'.lower()])
    if args.write_json and (not args.outputfile):
        argparams['OutputFile'.lower()] = APP_NAME + '.json'
        logging.debug('outputfile: %s, mode: %s',
                      argparams['OutputFile'.lower()],
                      argparams['output_mode'.lower()])

    argparams['search_id'.lower()] = args.id
    logging.debug('search_id: %s', argparams['search_id'.lower()])

    argparams['configfile'.lower()] = args.inifile
    logging.debug('configfile: %s', argparams['configfile'.lower()])

    argparams['dryrun'.lower()] = args.dryrun
    logging.debug('dryrun: %s', argparams['dryrun'.lower()])

    argparams['getstatus'.lower()] = args.getstatus
    logging.debug('getstatus: %s', argparams['getstatus'.lower()])

    argparams['wakati'.lower()] = args.wakati
    logging.debug('wakati: %s', argparams['wakati'.lower()])

    if argparams['search_id'] is None and argparams['search_string'] == "":
        print("Search String is required", file=sys.stderr)
        parser.print_usage()
        sys.exit(2)
    return argparams


def main():
    """main()"""
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.WARN)
    config = TwsConfig(tw_argparse())
    config.logger.info("config['AppName']: %s", config['AppName'])
    splunk_writer = SplunkWriterBySearch(config=config)
    if config['getstatus']:
        splunk_writer.disp_limit_status()
        sys.exit(0)
    splunk_writer.generate(config)


if __name__ == '__main__':
    main()
