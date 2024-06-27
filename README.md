# scrapy-qiita

## setup

```console
pip3 install -r requirements.txt
```

## run

```console
scrapy crawl items -o qiita`date "+%Y%m%d"`.json -t jsonlines --nolog
```