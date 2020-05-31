#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""時刻変換のユーティリティ"""

import datetime
import time

from dateutil import tz

def datevalue2datetime(datevalue):
    """Excel の DateValue 形式を datetime へ変換"""
    days = int(round(datevalue, 0))
    secs = int(round((datevalue - days) * 3600 * 24, 0))
    hours = int(round(secs / 3600, 0))
    remain = secs % 3600
    minutes = int(round(remain / 60))
    seconds = remain % 60

    return datetime.datetime(1899, 12, 30) + \
            datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def datetime2datevalue(datetime_obj):
    """datetime を Excel の DateValue 形式へ変換"""
    delta = datetime_obj - datetime.datetime(1899, 12, 30)
    days = delta.days
    remain = delta.seconds / 3600 / 24
    microsec_remain = delta.microseconds / 1000000 / 3600 / 24
    return days + remain + microsec_remain


def datetime2epoch(d_utc):
    """datetime (UTC) をエポックタイム (UNIX タイム)へ変換"""
    #UTC を localtime へ変換
    date_localtime = d_utc.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
    return int(time.mktime(date_localtime.timetuple()))


def epoch2datetime(epoch):
    """エポックタイム (UNIX タイム) を datetime (localtime) へ変換"""
    return datetime.datetime(*(time.localtime(epoch)[:6]))


def str2datetime(datestr):
    """ツイートの日付(UTC)文字列を datetime オブジェクトに変換"""
    return datetime.datetime.strptime(datestr, '%a %b %d %H:%M:%S +0000 %Y')


def str2epoch(datestr):
    """ツイートの日付(UTC)文字列をエポック time (UNIX タイム) に変換"""
    return datetime2epoch(str2datetime(datestr))


def str_to_datetime_jp(datestr):
    """ツイートのdatetimeを日本標準時間に変換"""
    dts = str2datetime(datestr)
    return (dts + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S JST")
