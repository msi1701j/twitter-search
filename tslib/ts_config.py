# -*- coding: utf-8 -*-
"""TWitter Search の設定用クラスモジュール"""

import os
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

    def __init__(self, argparams):
        self.logger = logging.getLogger('twsearch')
        self.logging_level = argparams['logging_level'] if 'logging_level' in argparams else logging.WARN
        self.logger.setLevel(self.logging_level)

        self.__Default_ConfigDir = os.path.join(os.path.dirname(__file__), "..")

        self.__argparams = argparams
        self.__configfile = self.__Default_ConfigFile

        if 'configfile' in self.__argparams:
            self.__configfile = self.__argparams['configfile']

        super().__init__(self.__configfile, default_config=self.__Default_Config)

        for key in self.__argparams:
            key = key.lower()
            super().__setitem__(key, self.__argparams[key])

        for key in self.__iter__():
            if key in ("consumerapikey", "consumerapisecret"):
                self.logger.debug("__params['%s'] = %s",
                                  key, "********************** (not display)")
            else:
                self.logger.debug("__params['%s'] = %s",
                                  key, self.__getitem__(key))


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
