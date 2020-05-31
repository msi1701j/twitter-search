# twsearch - Twitter Search

## インストール

* [MyConfig](https://github.com/msi1701j/MyConfig) を使用しているので、環境変数 PYTHONPATH などで、読み込み可能なディレクトリに `custom_config/` を置いてください。
* 設定ファイルは `default/` `local/` の順に検索します。これらのディレクトリが存在するディレクトリを環境変数 `CUSTOM_CONFIG_DIR` に設定してください。
* `default/` 下のファイルは修正せず、`local/` 下にコピーして修正してください。
* `${CUSTOM_CONFIG_DIR}/local/twsearch.ini` に `ConsumerAPIKey` と `CosumerAPISecret` を設定してください。

```ini:default/twsearch.ini
AppName = Your Application Name
AppVersion = Your Application Version
# Consumer Key
ConsumerAPIKey = Your_Consumer_API_Key
# Consumer Secret
ConsumerAPISecret = Your_Consumer_API_Secret_Key
# Access Token
#AccessToken = Not Required
# Accesss Token Secret
#AccessTokenSecret = Not Required
```

## twsearch.py

指定した検索文字列を検索します。

初期設定ファイルはカレントディレクトリの twsearch.ini です。

```
usage: twsearch.py [-h] [-l] [-c DISPCOUNT] [-C COUNT] [-D] [-S SINCE_ID]
                   [-M MAX_ID] [--since_date SINCE_DATE] [--max_date MAX_DATE]
                   [-t TRYTIME] [-b SHELVE] [-B] [-o OUTPUTFILE] [-O] [-w]
                   [-j] [-i] [-I INIFILE] [-f] [-v | -s]
                   search_string

positional arguments:
  search_string         検索文字列 or ID (-i オプションで指定)

optional arguments:
  -h, --help            show this help message and exit
  -l, --localno         ローカル No.
  -c DISPCOUNT, --dispcount DISPCOUNT
                        表示数
  -C COUNT, --count COUNT
                        一度の取得数
  -D, --debug           Debug モード
  -S SINCE_ID, --since_id SINCE_ID
                        since_id の指定 (指定 id 含まない)
  -M MAX_ID, --max_id MAX_ID
                        max_id の指定 (指定 id 含む)
  --since_date SINCE_DATE
                        since_date (since) の指定 (指定日含む)
  --max_date MAX_DATE   max_date (until) の指定 (指定日含ない)
  -t TRYTIME, --trytime TRYTIME
                        リトライ回数
  -b SHELVE, --shelve SHELVE
                        Shelve (パラメータ格納) ファイルの指定
  -B, --shelve_reset    Shelve (パラメータ格納) ファイルのリセット
  -o OUTPUTFILE, --outputfile OUTPUTFILE
                        出力 (CSV|JSON) ファイル名
  -O, --outputfile_reset
                        出力 (CSV|JSON) ファイルリセット
  -w, --write_header    出力 CSV ファイルへヘッダタイトルを記入
  -j, --write_json      JSON 出力
  -i, --id              get Tweet as ID
  -I INIFILE, --inifile INIFILE
                        設定ファイルの指定
  -f, --dummy           dummy オプション
  -v, --verbose         Verbose 表示
  -s, --silence         Silence 表示
```

# tools

## dispshelve.py

shelve ファイルの内容を出力します。

```
usage: dispshelve.py [-h] shelvefile

positional arguments:
  shelvefile  shelveファイル名

optional arguments:
  -h, --help  show this help message and exit
```

# 変更履歴

|Version|Rlease Date|Desctiption|
|:--|:--|:--|
|[0.2.0](https://github.com/msi1701j/twitter-search/releases/tag/v0.2.0)|2020/05/31|[MyConfig](https://github.com/msi1701j/MyConfig) を使用して、モジュールを分離
|0.1.0|-|Initial Release
