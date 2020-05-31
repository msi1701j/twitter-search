#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""twsearch.py"""

import sys
import logging
import shelve
import json
import csv
import datetime

from tslib import TwsConfig
from tslib import Tweets
from tslib import epoch2datetime, \
            str2datetime, str2epoch, datetime2datevalue, str_to_datetime_jp

__APP_VERSION__ = "v0.2.0"

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

    __Resource_Family = 'search'
    __Resource = '/search/tweets'
    __Search_Endpoint = 'https://api.twitter.com/1.1/search/tweets.json'

    def __init__(self, config: "TwsConfig"):
        super().__init__(
            config=config,
            endpoint=self.__Search_Endpoint,
            default_params=self.__Default_Params,
            resource_family=self.__Resource_Family,
            resource=self.__Resource
        )

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

        if self.__dbasename is None:
            self.__dbase = None
        else:
            shelve_flag = config['shelve_flag']
            self.logger.debug("self.__dbasename: %s, shelve_flag: %s",
                              self.__dbasename, shelve_flag)
            self.__dbase = shelve.open(self.__dbasename, flag=shelve_flag, writeback=True)
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

    # Shelve File key check
    def __get_shelve_value(self, key):
        if self.__dbase is not None:
            if key in self.__dbase:
                return self.__dbase[key]
        return None

    # @abstractmethod
    def generate(self, config):
        """レコード生成メソッド"""
        pass

    def convert(self, tweet, metadata, counter=-1):
        """時刻変換、追加、レコードの書き込み"""
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
                                                    '/status/' + tweet['id_str']
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
        query = config['search_string']
        params = {'q': query}
        for key in ('since_id', 'since_date', 'max_id', 'max_date', 'count'):
            value = config[key]
            if value is not None:
                params[key] = value

        twbs = TweetsBySearch(config)
        tweets_generator = twbs.generator(params, retry_max=config['retry_max'],
                                          interval_time=config['interval_time'],
                                          dispcount=config['dispcount'])
        counter = 0
        for tweet, metadata in tweets_generator:
            counter += 1
            super().convert(tweet, metadata, counter)


def main():
    """main()"""
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.WARN)
    config = TwsConfig()
    config.logger.info("config['AppName']: %s", config['AppName'])
    splunk_writer = SplunkWriterBySearch(config=config)
    splunk_writer.generate(config)


if __name__ == '__main__':
    main()
