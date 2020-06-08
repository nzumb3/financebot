import datetime as dt
from newsapi import NewsApiClient

NEWS_API = "20d6fa82bc7d4423b1b6fb50c73ee796"


query = '+"ABERCROMBIE FITCH"'

def make_api_calls(name):
    api = NewsApiClient(api_key=NEWS_API)
    query = '+"{}"'.format(name.replace("_", " "))
    articles_en_1 = api.get_everything(
        q= query,
        language= 'en',
        page_size=20,
        page=1
    )

    articles_en_2 = api.get_everything(
        q= query,
        language= 'en',
        page_size=20,
        page=2
    )

    articles_de_1 = api.get_everything(
        q= query,
        language= 'de',
        page_size=20,
        page=1
    )

    articles_de_2 = api.get_everything(
        q= query,
        language= 'de',
        page_size=20,
        page=2
    )

    return {
        "en": extract_articles(articles_en_1) + extract_articles(articles_en_2),
        "de": extract_articles(articles_de_1) + extract_articles(articles_de_2)
    }

def extract_articles(api_res):
    out = []
    for a in api_res["articles"]:
        content = ""
        if a["content"] is not None:
            content = a["content"]
        tmp = {
            "author": a["author"].encode("utf-8"),
            "url": a["url"],
            "timestamp": int(dt.datetime.strptime(a["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").timestamp()),
            "title": a["title"].encode("utf-8"),
            "description": a["description"].encode("utf-8"),
            'content': content.encode("utf-8")
        }
        out.append(tmp)
    return out
