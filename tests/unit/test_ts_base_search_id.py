#!/usr/bin/env python3
# -*- cofing: utf-8 -*-
"""TwsConfig Test Unit"""

import os, sys
import unittest
from test.support import captured_stdout
import json
import re

import logging

DIR_BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR_BASE, '..'))
sys.path.insert(0, os.path.join(DIR_BASE, '../lib'))
sys.path.insert(0, os.path.join(DIR_BASE, '../..'))
sys.path.insert(0, os.path.join(DIR_BASE,'../../lib'))

from tslib import Tweets
from tslib import TwsConfig
from tslib import ts_dateutils

GETID_ENDPOINT = "https://api.twitter.com/1.1/statuses/show.json"
GETID_FAMILY = "statuses"
GETID_RESOURCE = "statuses/show"

RE_VALNUM = re.compile(r'(?P<target>("statuses_count"|"favorite_count"|"favourites_count"):\s*)\d+')

class TestTweetsSearchId(unittest.TestCase):
    """Tweets の unittest"""

    def setUp(self):
        argparams = {}
        self.config = TwsConfig(argparams)
        self.config['dryrun'] = False
       

    def test_001(self):
        """id 指定 Tweet のテスト(JSON 個別指定)"""
        params = {"tweet_mode": "extended"}
        tw = Tweets(self.config, endpoint=GETID_ENDPOINT,
                    default_params=params,
                    resource_family=GETID_FAMILY, resource=GETID_RESOURCE)
        search_id = "1268346734951964672"
        res_j = tw.get_one_tweet(search_id)
        self.assertEqual(res_j['id_str'], search_id)
        self.assertEqual(res_j['full_text'],
                         "ずいぶん前に作ったロゴ。\n#ロゴ #五十嵐家 #logo https://t.co/3xHgegtckl")
        self.assertEqual(res_j['user']['id_str'], "14963504")
        self.assertEqual(res_j['entities']['hashtags'][0]['text'], "ロゴ")
        self.assertEqual(res_j['entities']['hashtags'][1]['text'], "五十嵐家")
        self.assertEqual(res_j['entities']['hashtags'][2]['text'], "logo")
        epoch = 1591232401
        dt = ts_dateutils.str2datetime(res_j['created_at'])
        tw_epoch = ts_dateutils.datetime2epoch(dt)
        self.assertEqual(tw_epoch, epoch)
        del tw

    def test_002(self):
        """id 指定 Tweet のテスト(JSON 全体)"""
#        self.config.logger.setLevel(logging.DEBUG)
        default_params = {"tweet_mode": "extended"}
        tw = Tweets(self.config, endpoint=GETID_ENDPOINT,
                    default_params=default_params,
                    resource_family="statuses", resource="statuses/show")
        search_id = "1268346734951964672"
        res_j = tw.get_one_tweet(search_id)
        with captured_stdout() as stdout:
            print(json.dumps(res_j, indent=2, ensure_ascii=False))
            lines = stdout.getvalue().splitlines()

        tweet_content = """{
  "created_at": "Thu Jun 04 01:00:01 +0000 2020",
  "id": 1268346734951964672,
  "id_str": "1268346734951964672",
  "full_text": "ずいぶん前に作ったロゴ。\\n#ロゴ #五十嵐家 #logo https://t.co/3xHgegtckl",
  "truncated": false,
  "display_text_range": [
    0,
    28
  ],
  "entities": {
    "hashtags": [
      {
        "text": "ロゴ",
        "indices": [
          13,
          16
        ]
      },
      {
        "text": "五十嵐家",
        "indices": [
          17,
          22
        ]
      },
      {
        "text": "logo",
        "indices": [
          23,
          28
        ]
      }
    ],
    "symbols": [],
    "user_mentions": [],
    "urls": [],
    "media": [
      {
        "id": 1268346600008507392,
        "id_str": "1268346600008507392",
        "indices": [
          29,
          52
        ],
        "media_url": "http://pbs.twimg.com/media/EZoSg0GU4AAXUe8.jpg",
        "media_url_https": "https://pbs.twimg.com/media/EZoSg0GU4AAXUe8.jpg",
        "url": "https://t.co/3xHgegtckl",
        "display_url": "pic.twitter.com/3xHgegtckl",
        "expanded_url": "https://twitter.com/Ikarashi/status/1268346734951964672/photo/1",
        "type": "photo",
        "sizes": {
          "thumb": {
            "w": 116,
            "h": 116,
            "resize": "crop"
          },
          "small": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          },
          "medium": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          },
          "large": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          }
        }
      }
    ]
  },
  "extended_entities": {
    "media": [
      {
        "id": 1268346600008507392,
        "id_str": "1268346600008507392",
        "indices": [
          29,
          52
        ],
        "media_url": "http://pbs.twimg.com/media/EZoSg0GU4AAXUe8.jpg",
        "media_url_https": "https://pbs.twimg.com/media/EZoSg0GU4AAXUe8.jpg",
        "url": "https://t.co/3xHgegtckl",
        "display_url": "pic.twitter.com/3xHgegtckl",
        "expanded_url": "https://twitter.com/Ikarashi/status/1268346734951964672/photo/1",
        "type": "photo",
        "sizes": {
          "thumb": {
            "w": 116,
            "h": 116,
            "resize": "crop"
          },
          "small": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          },
          "medium": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          },
          "large": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          }
        }
      }
    ]
  },
  "source": "<a href=\\"https://mobile.twitter.com\\" rel=\\"nofollow\\">Twitter Web App</a>",
  "in_reply_to_status_id": null,
  "in_reply_to_status_id_str": null,
  "in_reply_to_user_id": null,
  "in_reply_to_user_id_str": null,
  "in_reply_to_screen_name": null,
  "user": {
    "id": 14963504,
    "id_str": "14963504",
    "name": "五十嵐智(いかちょー)",
    "screen_name": "Ikarashi",
    "location": "埼玉県さいたま市",
    "description": "ケロロフリーク、SFファン、CISSP、産業カウンセラー、キャリアコンサルティング技能士(2級)、国家資格登録キャリアコンサルタント。通称:いかちょー、筆名:ほりえみつお。",
    "url": "https://t.co/rNzDugMRlT",
    "entities": {
      "url": {
        "urls": [
          {
            "url": "https://t.co/rNzDugMRlT",
            "expanded_url": "http://ameblo.jp/vsa-v",
            "display_url": "ameblo.jp/vsa-v",
            "indices": [
              0,
              23
            ]
          }
        ]
      },
      "description": {
        "urls": []
      }
    },
    "protected": false,
    "followers_count": 1000,
    "friends_count": 2282,
    "listed_count": 82,
    "created_at": "Sat May 31 14:38:14 +0000 2008",
    "favourites_count": 10386,
    "utc_offset": null,
    "time_zone": null,
    "geo_enabled": true,
    "verified": false,
    "statuses_count": 36201,
    "lang": null,
    "contributors_enabled": false,
    "is_translator": false,
    "is_translation_enabled": false,
    "profile_background_color": "9AE4E8",
    "profile_background_image_url": "http://abs.twimg.com/images/themes/theme1/bg.png",
    "profile_background_image_url_https": "https://abs.twimg.com/images/themes/theme1/bg.png",
    "profile_background_tile": true,
    "profile_image_url": "http://pbs.twimg.com/profile_images/2175916038/ikacho-100x100_normal.png",
    "profile_image_url_https": "https://pbs.twimg.com/profile_images/2175916038/ikacho-100x100_normal.png",
    "profile_banner_url": "https://pbs.twimg.com/profile_banners/14963504/1398595872",
    "profile_link_color": "C27DFA",
    "profile_sidebar_border_color": "2200FF",
    "profile_sidebar_fill_color": "DED9FF",
    "profile_text_color": "000000",
    "profile_use_background_image": true,
    "has_extended_profile": true,
    "default_profile": false,
    "default_profile_image": false,
    "following": null,
    "follow_request_sent": null,
    "notifications": null,
    "translator_type": "none"
  },
  "geo": null,
  "coordinates": null,
  "place": null,
  "contributors": null,
  "is_quote_status": false,
  "retweet_count": 0,
  "favorite_count": 0,
  "favorited": false,
  "retweeted": false,
  "possibly_sensitive": false,
  "possibly_sensitive_appealable": false,
  "lang": "ja"
}
"""
        tc_lines = tweet_content.splitlines()
        for i, line in enumerate(lines):
            tc_line = tc_lines[i]
            line = RE_VALNUM.sub(r'\g<target>N', line)
            tc_line = RE_VALNUM.sub(r'\g<target>N', tc_line)
            self.assertEqual(line, tc_line)

if __name__ == "__main__":
    unittest.main()
