# -*- coding: utf-8 -*-
"""TWitter Search の設定用クラスモジュール"""

import os
import argparse
import logging

from custom_config import Config

class TwsConfig(Config):
    """ 設定保持するクラス """

    __Default_ConfigFile = 'twsearch.ini'
    __Default_Config = {
        'AppName': 'Twitter-Search',
        'AppVersion': '2.0',
        'ConsumerAPIKey': '-',
        'ConsumerAPISecret': '-',
        'ShelveFile': 'twsearch.shelve',
        'OutputFile': 'twsearch.csv',
        'OutputFilePrefix': 'twsearch',
        'OutputFileExtention': 'csv',
        'Interval_Time': 5,
        'Count': 100,
        'DispCount': -1,
    }

    def __init__(self):
        self.logger = logging.getLogger('twsearch')
        self.logging_level = logging.WARN
        self.logger.setLevel(self.logging_level)

        self.__Default_ConfigDir = os.path.join(os.path.dirname(__file__), "..")

        self.__argparams = {}
        self.__configfile = self.__Default_ConfigFile
        self.__argparse()

        if 'configfile' in self.__argparams:
            self.__configfile = self.__argparams['configfile']

        super().__init__(self.__configfile, default_config=self.__Default_Config)

        for key in self.__argparams:
            key = key.lower()
            super().__setitem__(key, self.__argparams[key])

        for key in self.__iter__():
            if key == "consumerapikey" or key == "consumerapisecret":
                self.logger.debug("__params['%s'] = %s",
                                  key, "********************** (not display)")
            else:
                self.logger.debug("__params['%s'] = %s",
                                  key, self.__getitem__(key))

    def __argparse(self):
        self.__configfile = self.__Default_ConfigFile

        parser = argparse.ArgumentParser()

        # オプションの設定
        parser.add_argument('search_string',
                            help=u'検索文字列 or ID (-i オプションで指定)')
        parser.add_argument('-l', '--localno', action='store_true',
                            help=u'ローカル No.')
        parser.add_argument('-c', '--dispcount', type=int, default=-1,
                            help=u'表示数')
        parser.add_argument('-C', '--count', type=int, default=100,
                            help=u'一度の取得数 (デフォルト 100 (最大値))')
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
        parser.add_argument('-t', '--trytime', type=int, default=5,
                            help=u'リトライ回数 (デフォルト 5)')
        parser.add_argument('-b', '--shelve', type=str,
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
        parser.add_argument('-i', '--id', action='store_true',
                            help=u'get Tweet as ID')
        parser.add_argument('-I', '--inifile', type=str, default=self.__Default_ConfigFile,
                            help=u'設定ファイルの指定 (デフォルトは {})'.format(self.__Default_ConfigFile) + \
                            u'ディレクトリの指定は環境変数CUSTOM_CONFIG_DIR')
        parser.add_argument('-f', '--dummy', action='store_true',
                            help=u'dummy オプション')
        parser.add_argument('-d', '--dryrun', action='store_true',
                            help=u'Dry Run, no execution')

        # 排他オプション
        optgroup1 = parser.add_mutually_exclusive_group()
        optgroup1.add_argument('-v', '--verbose', action='store_true',
                               help=u'Verbose 表示 (logging INFO レベル)')
        optgroup1.add_argument('-s', '--silence', action='store_true',
                               help=u'Silence 表示')

        args = parser.parse_args()

        self.__argparams['VERBOSE'.lower()] = args.verbose
        if args.verbose:
            self.logging_level = logging.INFO
            self.logger.setLevel(logging.INFO)
        self.logger.debug('Verbose is %s', args.verbose)

        self.__argparams['SILENCE'.lower()] = args.silence
        if args.silence:
            self.logging_level = logging.ERROR
            self.logger.setLevel(logging.ERROR)
        self.logger.debug('Silence is %s', args.silence)

        self.__argparams['DEBUG'.lower()] = args.debug
        if args.debug:
            self.logging_level = logging.DEBUG
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug('Debug is %s', args.debug)

        self.__argparams['shelve_flag'] = 'c'
        if args.shelve_reset:
            self.__argparams['shelve_flag'.lower()] = 'n'
        if args.shelve is not None:
            self.__argparams['ShelveFile'.lower()] = args.shelve
            self.logger.debug('shelvefile: %s, flag: %s',
                              self.__argparams['ShelveFile'.lower()],
                              self.__argparams['shelve_flag'.lower()])
        else:
            self.logger.debug('shelvefile: %s, flag: %s',
                              'N/A',
                              self.__argparams['shelve_flag'.lower()])

        self.__argparams['output_mode'.lower()] = 'a'
        if args.outputfile_reset:
            self.__argparams['output_mode'.lower()] = 'w'
        self.__argparams['outputfile_reset'.lower()] = args.outputfile_reset
        if args.outputfile:
            self.__argparams['OutputFile'.lower()] = args.outputfile
            self.logger.debug('outputfile: %s, mode: %s',
                              self.__argparams['OutputFile'.lower()],
                              self.__argparams['output_mode'.lower()])
        else:
            self.logger.debug('outputfile: %s, mode: %s',
                              'N/A',
                              self.__argparams['output_mode'])

        self.__argparams['write_header'.lower()] = args.write_header
        self.logger.debug('write_header: %s', self.__argparams['write_header'.lower()])

        self.__argparams['search_string'.lower()] = args.search_string
        self.logger.debug('search_string: %s', self.__argparams['search_string'.lower()])

        self.__argparams['count'.lower()] = args.count
        self.logger.debug('count: %s', self.__argparams['count'.lower()])

        self.__argparams['dispcount'.lower()] = args.dispcount
        self.logger.debug('dispcount: %s', self.__argparams['dispcount'.lower()])

        self.__argparams['since_id'.lower()] = args.since_id
        self.logger.debug('since_id: %s', self.__argparams['since_id'.lower()])

        self.__argparams['max_id'.lower()] = args.max_id
        self.logger.debug('max_id: %s', self.__argparams['max_id'.lower()])

        self.__argparams['retry_max'.lower()] = args.trytime
        self.logger.debug('retry_max: %s', self.__argparams['retry_max'.lower()])

        self.__argparams['since_date'.lower()] = args.since_date
        self.logger.debug('since_date: %s', self.__argparams['since_date'.lower()])

        self.__argparams['max_date'.lower()] = args.max_date
        self.logger.debug('max_date: %s', self.__argparams['max_date'.lower()])

        self.__argparams['localno'.lower()] = args.localno
        self.logger.debug('localno: %s', self.__argparams['localno'.lower()])

        self.__argparams['write_json'.lower()] = args.write_json
        self.logger.debug('write_json: %s', self.__argparams['write_json'.lower()])
        if args.write_json and (not args.outputfile):
            self.__argparams['OutputFile'.lower()] = \
                self.__Default_Config['OutputFilePrefix'] + '.json'
            self.logger.debug('outputfile: %s, mode: %s',
                              self.__argparams['OutputFile'.lower()],
                              self.__argparams['output_mode'.lower()])


        self.__argparams['search_id'.lower()] = args.id
        self.logger.debug('search_id: %s', self.__argparams['search_id'.lower()])

        self.__argparams['configfile'.lower()] = args.inifile
        self.__configfile = args.inifile
        self.logger.debug('configfile: %s', self.__argparams['configfile'.lower()])

        self.__argparams['dryrun'.lower()] = args.dryrun
        self.__dryrun = args.dryrun
        self.logger.debug('dryrun: %s', self.__argparams['dryrun'.lower()])

#    def argparams(self, key):
#        if key.lower() in self.__argparams:
#            return self.__argparams[key.lower()]
#        return None
#
#    def params(self, key):
#        if key.lower() in self.__params:
#            return self.__params[key.lower()]
#        return None
#
#    def __getitem__(self, key):
#        if key.lower() in self.__mydict:
#            return self.__mydict[key.lower()]
#        raise KeyError(key)
#
#    def __setitem__(self, key, value):
#        self.__mydict[key.lower()] = value
#
#    def __contains__(self, key):
#        return key.lower() in self.__mydict
