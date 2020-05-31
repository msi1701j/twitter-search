# -*- coding: utf-8 -*-
"""Tweets を取得するためのクラスモジュール"""

import sys
from base64 import b64encode
import logging
import json
import time
import re

import requests

from .ts_dateutils import epoch2datetime

#from abc import ABCMeta
#class Tweets(metaclass=ABCMeta):
class Tweets:
    """ Tweets を取得する基底クラス """
    __Invalid_Param_Error = 195
    __Auth_Error = 99
    __Invalid_Count_Error = 44
    __Rate_Limit_Exceeded = 88

    def __init__(self, config, endpoint, default_params,
                 resource_family='search', resource='/search/tweets'):
        self.config = config
        self.logger = config.logger
        self.logger.debug("Called base Tweets")
        self.__UserAgent = config['AppName'] + " " + config['AppVersion']
        self.__Bearer = self.__get_bearer(config['ConsumerAPIKey'], config['ConsumerAPISecret'])
        self.__Endpoint = endpoint
        self.__Default_Params = default_params.copy()
        self.__Resource_Family = resource_family
        self.__Resource = resource
        self.__params = default_params.copy()
        self.MAX_COUNT = 100
        self.__count_pattern = re.compile(r'&count=\d+')

        self.set_param('count', config['count'], force=True)


    def __get_counts(self, count, dispcount):
        if count is None or count > self.MAX_COUNT:
            count = self.MAX_COUNT

        if dispcount is None or dispcount < 0:
            dispcount = -1
        elif dispcount == 0:
            self.logger.error("invalid dispcount: %d", dispcount)
            count = 0
        elif count > dispcount:
            count = dispcount
            dispcount = 0
        elif count <= dispcount:
            dispcount -= count
#        else:
#            dispcount = -1
        self.logger.debug("returning __get_counts(): count:%d, dispcount:%d", count, dispcount)
        return count, dispcount


    def __get_bearer(self, apikey, apisec):
        cred = self.__get_credential(apikey, apisec)
        TOKEN_ENDPOINT = 'https://api.twitter.com/oauth2/token'
        headers = {
            'Authorization': 'Basic ' + cred,
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'User-Agent': self.__UserAgent
            }
        data = {
            'grant_type': 'client_credentials',
            }

        try:
            res = requests.post(TOKEN_ENDPOINT, data=data, headers=headers, timeout=10.0)
            res.raise_for_status()
        except (TimeoutError, requests.ConnectionError) as e:
            self.logger.exception("Timeout: %s", e)
            self.dump_response(logging.ERROR, "Timeout", res)
            raise Exception("Cannot get Bearer")
        except requests.exceptions.HTTPError as e:
            self.logger.exception("Exception Type: %s", type(e))
            self.dump_response(logging.ERROR, "Cannot get Bearer", res)
            if res.status_code == 403:
                raise requests.exceptions.HTTPError("Auth Error")
            raise requests.exceptions.HTTPError("Other Exception")
        except Exception as e:
            self.logger.exception("Exception Type: %s", type(e))
            self.dump_response(logging.ERROR, "Cannot get Bearer", res)
            raise Exception("Cannot get Bearer")
        rjson = res.json()
        return rjson['access_token']

    @staticmethod
    def __get_credential(apikey, apisec):
        pair = apikey + ':' + apisec
        bcred = b64encode(pair.encode('utf-8'))
        return bcred.decode()

    def __get_limit_status(self):
        STATUS_ENDPOINT = 'https://api.twitter.com/1.1/application/rate_limit_status.json'
        params = {
            'resources': self.__Resource_Family  # help, users, search, statuses etc.
        }
        headers = {
            'Authorization':'Bearer {}'.format(self.__Bearer),
            'User-Agent': self.__UserAgent
        }
        try:
            res = requests.get(STATUS_ENDPOINT, headers=headers, params=params, timeout=10.0)
            res.raise_for_status()
        except (TimeoutError, requests.ConnectionError) as e:
            self.logger.exception("Timeout: %s", e)
            self.dump_response(logging.ERROR, "Timeout", res)
            raise requests.ConnectionError("Cannot get Limit Status")
        except Exception as e:
            self.logger.exception("Exception Type: %s", type(e))
            self.dump_response(logging.ERROR, "Cannot get Limit Status", res)
            raise Exception("Cannot get Limit Status")
        self.dump_response(logging.INFO, "Limit Status", res)
        return res.json()

    def __calc_sleeptime(self, target_epoch_time):
        """target_epoch_time (UNIX タイム) までの Sleep 秒を返す"""
        sleep_time = target_epoch_time - int(round(time.time(), 0))
        self.logger.info("Calculated sleep seconds: %d", sleep_time)
        return sleep_time

    def wait_reset(self):
        """reset 時刻まで sleep する"""
        status = self.__get_limit_status()
        self.logger.debug("status: %s", json.dumps(status, ensure_ascii=False, indent=2))
        remaining = status['resources'][self.__Resource_Family][self.__Resource]['remaining']
        if remaining == 0:
            target_time = status['resources'][self.__Resource_Family][self.__Resource]['reset']
            sleep_time = self.__calc_sleeptime(target_time) + 10 # 念のため、10 秒加算
            self.logger.debug("target_time: %d, sleep_time: %d",
                              epoch2datetime(target_time), sleep_time)
            sys.stderr.flush()
            sys.stdout.flush()
            time.sleep(sleep_time)

    def set_param(self, key, value, force=False):
        """__params[] への登録"""
        if force:
            self.__params[key] = value
        elif key in self.__params:
            self.__params[key] = value
        else:
            raise KeyError("{} does not exist.".format(key))


    def set_params(self, given_params):
        """__params[] への一括登録"""
        if given_params is None:
            self.__params = None
        else:
            for key in given_params:
                self.__params[key] = given_params[key]

    def get_params(self):
        """__params[] の一括取得"""
        return self.__params

    def get_param(self, key):
        """__params[] の取得"""
        if key in self.__params:
            return self.__params[key]
        return None

    def generator(self, given_params, retry_max=5, interval_time=5, dispcount=-1):
        """Tweet を取得して一つずつに分離し、それぞれを metadata と対にして返す"""
        self.logger.debug("called Tweets.generator(%s, %d, %d)",
                          given_params, retry_max, interval_time)

        self.set_params(given_params)

        count, dispcount = self.__get_counts(self.get_param('count'), dispcount)
        self.set_param('count', count, force=True)
        # saved_params = self.__params.copy()
        params = self.get_params()

        self.logger.debug("count: %d", params['count'])

        headers = {
            'Authorization':'Bearer {}'.format(self.__Bearer),
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'User-Agent':   self.__UserAgent,
        }

        saved_max_id = None
        next_results = None
        retry = 0
        self.logger.debug("retry: %d, retry_max: %d", retry, retry_max)
        url = self.__Endpoint
#        while retry <= retry_max:
        while True:
            self.logger.debug("dryrun: %s", self.config['dryrun'])
            if self.config['dryrun']:
                retry += 1
                if retry > retry_max:
                    break  # StopIteration
                self.logger.info("dryrun, retry %d", retry)
                continue

            try:
                res = requests.get(url, headers=headers, params=params, timeout=10.0)
                res.raise_for_status()
            except (TimeoutError, requests.ConnectionError) as e:
                self.logger.exception("Timeout: %s", e)
                retry += 1
                if retry > retry_max:
                    break  # StopIteration
                self.logger.info("retrying: %d sleep well...", retry)
                time.sleep(interval_time)
                continue
            except requests.HTTPError as e:
                if res is not None and (res.status_code == 429 or res.status_code == 420):
                    # {
                    #   "errors": [
                    #     {
                    #       "code": 88,
                    #       "message": "Rate limit exceeded"
                    #     }
                    #   ]
                    # }
                    self.dump_response(logging.INFO, "Rate limit in generator", res)
                    self.logger.info("Rate limit in generator: %d, %s", res.status_code, e)
                    self.wait_reset()
                    retry = 0
                    continue

                if res.status_code == 500 or res.status_code == 502 or \
                    res.status_code == 503 or res.status_code == 504:

                    self.dump_response(logging.ERROR, "50x Error", res)
                    retry += 1
                    if retry > retry_max:
                        break  # StopIteration
                    self.logger.info("retrying: %d sleep well...", retry)
                    time.sleep(interval_time)
                    continue

                if res.status_code == 400:
                    # {
                    #   "errors": [
                    #     {
                    #       "code": 44,
                    #       "message": "count parameter is invalid."
                    #     }
                    #   ]
                    # }
                    self.dump_response(logging.ERROR, "Invalid Parameters", res)
                    raise Exception("Invalid Parameter")

                if res.status_code == 401:
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
                    self.dump_response(logging.ERROR, "Auth Error", res)
                    raise Exception('Auth Error')

                if res.status_code == 403:
                    brk = False
                    entry = res.json()
                    if entry is not None:
                        errors = entry['errors']
                        for err in errors:
                            code = err['code']
                            if code == self.__Invalid_Param_Error:
                                # "message": "Missing or invalid url parameter."
                                brk = True
                    if brk:
                        raise Exception("Missing or invalid url parameter")
                    retry += 1
                    if retry > retry_max:
                        break  # StopIteration
                    self.logger.info("retrying: %d sleep well...", retry)
                    time.sleep(interval_time)
                    continue

                self.logger.exception("Exception: %s", e)
                self.dump_response(logging.ERROR, "HTTPError", res)
                raise requests.HTTPError("HTTPError")

            except Exception as e:
                self.logger.exception("Exception: %s", e)
                self.dump_response(logging.ERROR, "Unexpected Exception", res)
                raise Exception("Unexpected Exception")

            entry = res.json()
            self.logger.debug("status_code: %d", res.status_code)
#           self.logger.debug("entry: %s", entry)
            if 'search_metadata' not in entry:
                self.logger.info("status_code: %d", res.status_code)
                self.logger.info("'search_metadata' is not in res: res.json() = %s",
                                 json.dumps(entry, ensure_ascii=False, indent=2))
                retry += 1
                if retry > retry_max:
                    break  # StopIteration
                self.logger.info("retrying: %d sleep well...", retry)
                time.sleep(interval_time * retry)
                continue

            metadata = entry['search_metadata']
            for tweet in entry['statuses']:
                saved_max_id = tweet['id']
                self.logger.info("saved_max_id: %d", saved_max_id)
                yield (tweet, metadata)

            if metadata is not None:
                self.logger.debug("metadata: %s",
                                  json.dumps(metadata, ensure_ascii=False, indent=2))

            if 'next_results' not in metadata:
                retry += 1
                if retry > retry_max:
                    break  # StopIteration
                self.logger.info("retrying: %s sleep well...", retry)
                time.sleep(interval_time * retry)
            else:
                self.logger.debug("next_results exists: %s", metadata['next_results'])
                if dispcount == 0:
                    self.logger.debug("Returnning with dispcount == 0")
                    break  # StopIteration
                count, dispcount = self.__get_counts(count, dispcount)
                self.set_param('max_id', saved_max_id - 1, force=True)
                params = None
                next_results = self.__count_pattern.sub('&count={}'.format(count),
                                                        metadata['next_results'])
                self.logger.debug("next_results: %s", next_results)
                url = self.__Endpoint + next_results
                retry = 0
        return  # StopIteration

    @staticmethod
    def get_simple_hashtags(entities_hashtags):
        """ハッシュタグをリストにして取得"""
        hashtags = []
        for ent in entities_hashtags:
            hashtags.append(ent['text'])
        return hashtags


    def dump_response(self, level, message, res):
        """requests のエラーを level でダンプ出力"""
        if res is not None:
            entry = res.json()
            if entry is not None:
                self.logger.log(level, "%s: status_code: %d, %s",
                                message, res.status_code,
                                json.dumps(entry, ensure_ascii=False, indent=2))
                errors = entry['errors'] if 'errors' in entry else ()
                for err in errors:
                    self.logger.log(level, "errors: %s",
                                    json.dumps(err, ensure_ascii=False, indent=2))
