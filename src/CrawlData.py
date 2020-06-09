from bs4 import BeautifulSoup
from pathlib import Path
import requests
import time
from datetime import datetime as dt
import json
import os
import numpy as np
from newsapi import NewsApiClient
import pandas as pd

STUMP = "https://www.finanzen.net/"
SAVEPATH = str((Path(__file__).parent / "../data/").resolve()) + "/"
ENNEWS = "https://newslookup.com/results?p={}&q={}&dp=4&mt=-1&ps=10&s=1&cat=-1&fmt=&groupby=no&site=&dp=4"
DENEWS = "https://www.finanzen.net/nachrichten/alle/{}/{}" #no -aktie     de lufthansa

NEWS_API = "20d6fa82bc7d4423b1b6fb50c73ee796"

def make_api_calls(name):
    api = NewsApiClient(api_key=NEWS_API)
    query = '+"{}"'.format(name.lower().replace("_", " "))
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
            "author": a["author"],
            "url": a["url"],
            "timestamp": int(dt.strptime(a["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").timestamp()),
            "title": a["title"],
            "description": a["description"],
            'content': content
        }
        out.append(tmp)
    return out


def extractWKN(soup):
    return soup.title.string.split(" | ")[-1][1:-1].split(",")[0]

def extractValue(soup):
    for div in soup.find_all("div", attrs={"class":"col-xs-5 col-sm-4 text-sm-right text-nowrap"}):
        if div.text[-3:] == "EUR":
            return div.text[:-3].replace(",", ".")

def extractTableFeatures(soup):
    out = {}
    for tr in soup.find_all("tr"):
        if len(tr.find_all("td")) > 1 and tr.find_all("td")[0].string.split(" in ")[0] == "Marktkapitalisierung":
            out["Marktkapitalisierung"] = {
                "Size": tr.find_all("td")[0].string.split(" in ")[1].split(".")[0],
                "Value": tr.find_all("td")[1].string.replace(",", ".")
            }
        if len(tr.find_all("td")) > 1 and tr.find_all("td")[0].string == "KBV":
            out['KBV'] = tr.find_all("td")[1].string.replace(",", ".")
        if len(tr.find_all("td")) > 1 and tr.find_all("td")[0].string == "KCV":
            out['KCV'] = tr.find_all("td")[1].string.replace(",", ".")
        if len(tr.find_all("td")) > 1 and tr.find_all("td")[0].string == "KGV":
            out['KGV'] = tr.find_all("td")[1].string.replace(",", ".")
        if len(tr.find_all("td")) > 1 and tr.find_all("td")[0].string == "KGV":
            out['KGV'] = tr.find_all("td")[1].string.replace(",", ".")
        if len(tr.find_all("td")) > 1 and tr.find_all("td")[0].string == "30 Tage Vola":
            out['Vola30'] = tr.find_all("td")[1].string.replace(",", ".")
        if len(tr.find_all("td")) > 1 and tr.find_all("td")[0].string == "180 Tage Vola":
            out['Vola180'] = tr.find_all("td")[1].string.replace(",", ".")
        if len(tr.find_all("td")) > 2 and tr.find_all("td")[2].string == "Gewinn/Aktie":
            out['GA'] = tr.find_all("td")[3].string.replace(",", ".")
        if len(tr.find_all("td")) > 2 and tr.find_all("td")[2].string == "Buchwert/Aktie":
            out['BA'] = tr.find_all("td")[3].string.replace(",", ".")
        if len(tr.find_all("td")) > 2 and tr.find_all("td")[2].string == "Cashflow/Aktie":
            out['CA'] = tr.find_all("td")[3].string.replace(",", ".")
        if len(tr.find_all("td")) > 2 and tr.find_all("td")[2].string == "90 Tage Vola":
            out['Vola90'] = tr.find_all("td")[3].string.replace(",", ".")
        if len(tr.find_all("td")) > 2 and tr.find_all("td")[2].string == "250 Tage Vola":
            out['Vola250'] = tr.find_all("td")[3].string.replace(",", ".")
    return out

def getComparisonSoup(soup):
    link = STUMP
    for a in soup.find_all("a"):
        if a.text == "Vergleich":
            link += a["href"]
            break
    timeout()
    r = requests.get(link)
    return BeautifulSoup(r.content, features="lxml")

def extractRivals(soup, current):
    rivals = []
    for td in soup.find_all("td"):
        for a in td.find_all("a"):
            if len(a["href"].split("/")) > 2 and a["href"].split("/")[2] != current and a["href"].split("/")[1] == "aktien" and a["href"].split("-")[-1] == "aktie":
                rivals.append(a["href"].split("/")[-1])#.encode("utf-8"))
    return rivals

def extractName(soup):
    return "_".join(list(filter(lambda x: x.lower() != "aktie",soup.title.string.split(" | ")[0].split(" "))))

def exctractEnText(name):
    times, bodies, out = [], [], []
    for i in range(1,3):
        tmppath = ENNEWS.format(i, name[:-6].replace("_", "+"))
        timeout()
        res = requests.get(tmppath)
        soup = BeautifulSoup(res.content, features="lxml")
        for (a, p) in zip(soup.find_all("a", attrs={"class": "title"}), soup.find_all("p", attrs={"class": "desc"})):
            bodies.append(a.text + p.text)
        for span in soup.find_all("span", attrs={"class": "stime"}):
            times.append(span.text[:-4])
    for (b, t) in zip(bodies, times):
        out.append((t, b))
    return out

def extractHeaders(name):
    timeout()
    deres = requests.get(DENEWS.format("de", name[:-6].replace(" ", "_")))
    timeout()
    enres = requests.get(DENEWS.format("en", name[:-6].replace(" ", "_")))
    desoup = BeautifulSoup(deres.content, features="lxml")
    ensoup = BeautifulSoup(enres.content, features="lxml")
    deheaders, detimes = [], []
    enheaders, entimes = [], []
    out = {"finanzen_de":[], "finanzen_en": []}
    for a in desoup.find_all("a", attrs={"class": "teaser"}):
        deheaders.append(a.text)
    for td in desoup.find_all("td"):
        for div in td.find_all("div"):
            if div.text[-3:] == "Uhr":
                detimes.append(dt.now().strftime("%Y.%m.%d"))
            elif div.text[-2:] == "20":
                detimes.append(div.text)
    for a in ensoup.find_all("a", attrs={"class": "teaser"}):
        enheaders.append(a.text)
    for td in ensoup.find_all("td"):
        for div in td.find_all("div"):
            if div.text[-3:] == "Uhr":
                entimes.append(dt.now().strftime("%Y.%m.%d"))
            elif div.text[-2:] == "20":
                entimes.append(div.text)
    for (h, t) in zip(deheaders, detimes):
        out['finanzen_de'].append((t, h))
    for (h, t) in zip(enheaders, entimes):
        out['finanzen_en'].append((t, h))
    return out

def update_entry(stock, ts):
    df = pd.read_csv(SAVEPATH + "stocks.csv")
    df.loc[df["stock"]==stock, "last_update"] = ts
    df.to_csv(SAVEPATH + "stocks.csv", index=False)

def crawlStock(name):
    if name[-6:] != "-aktie":
        name += "-aktie"
    print("Crawling {}".format(name))
    timeout()
    res = requests.get(STUMP + "aktien/" + name)
    soup = BeautifulSoup(res.content, features="lxml")
    stock_sample = {
        "postfix": name,
        "name": extractName(soup),
        "wkn": extractWKN(soup),
        "time": dt.now().strftime("%Y.%m.%d %H:%M"),
        "ts": round(time.time()),
        "features": extractTableFeatures(soup)
    }
    print("Crawling Comparison")
    comp_soup = getComparisonSoup(soup)
    stock_sample["rivals"] = extractRivals(comp_soup, name)
    print("Getting Text Data")
    txt_dict = extractHeaders(name)
    stock_sample["finanzen_de"] = txt_dict["finanzen_de"]
    stock_sample["finanzen_en"] = txt_dict["finanzen_en"]
    stock_sample["newslookup"] = exctractEnText(name)
    txt_dict = make_api_calls(stock_sample["name"])
    stock_sample["newsapi_de"] = txt_dict["de"]
    stock_sample["newsapi_en"] = txt_dict["en"]
    print("Saving...")
    update_entry(name, stock_sample["ts"])
    path = SAVEPATH + dt.now().strftime("%Y%m%d") + "/"
    try:
        os.mkdir(SAVEPATH)
    except:
        True
    try:
        os.mkdir(path) 
    except:
        True
    with open(path + name + ".json", "w") as f:
        json.dump(stock_sample, f)
    print("DONE!")

def timeout(long= False):
    tosleep = 1
    if long:
        tosleep = np.random.normal(loc=5, scale=1)
    else:
        tosleep = np.random.normal(loc=2, scale=0.5)
    if tosleep < 0.05:
        tosleep = 2
    time.sleep(tosleep)

def getToCrawl():
    out = []
    with open(SAVEPATH + "stocks.txt", "r") as f:
        for line in f.readlines():
            out.append(line.replace("\n", ""))
    return out

def removeIdentical(li):
    print('Removing identical stocks')
    filtered = []
    i = 0
    for a in li:
        flag = True
        for b in filtered:
            total = len(b)
            cnt = 0
            for k in range(len(b)):
                if k >= len(a):
                    break
                if a[k] == b[k]:
                    cnt += 1
                else:
                    break
            if cnt/float(total) >= 0.95:
                flag = False
                break
        if len(filtered) == 0 or flag:
            filtered.append(a)
        i += 1
        if i%8 == 0:
            print("{:03.2f}% done!".format(float(i)/len(li)*100))
    return filtered

def extendToCrawl():
    toCrawl = removeIdentical(getToCrawl())
    new = []
    print("Began with {} stocks.".format(len(toCrawl)))
    for stock in toCrawl:
        print('Doing {}'.format(stock))
        if stock not in new:
            timeout(True)
            res = requests.get(STUMP + "aktien/" + stock)
            soup = BeautifulSoup(res.content, features="lxml")
            soup = getComparisonSoup(soup)
            rivals = extractRivals(soup, stock)
            new.append(stock)
            for r in rivals:
                if r not in toCrawl and r not in new:
                    new.append(r)
    print("New number of stocks: {}".format(len(new)))
    if len(new) != len(toCrawl):
        os.remove(SAVEPATH + "stocks.txt")
        with open(SAVEPATH + "stocks.txt", "w") as f:
            for stock in new:
                f.write(str(stock)+"\n")
        print("SAVED!")
    return new

def extend_stock_list(stock_li):
    new = []
    for stock in stock_li:
        timeout(True)
        res = requests.get(STUMP + "aktien/" + stock)
        soup = BeautifulSoup(res.content, features="lxml")
        soup = getComparisonSoup(soup)
        rivals = extractRivals(soup, stock)
        for r in rivals:
            if r not in stock_li and r not in new:
                new.append(r)
    print("Found {} new stocks".format(len(new)))
    return new

def select_to_crawl(df):
    mask = df["last_update"] < round(time.time())-60*60*24*2
    df = df[mask]
    stocks = np.random.choice(df["stock"], replace=False, size=120 if df.shape[0] > 120 else df.shape[0])
    return stocks

def load_data(extend=False):
    df = pd.read_csv(SAVEPATH + "stocks.csv")
    if extend:
        print(df.shape)
        df.drop_duplicates(subset=["stock"], inplace=True)
        print(df.shape)
        stock_li = list(df["stock"])
        new_stocks = extend_stock_list(stock_li)
        for stock in new_stocks:
            df = df.append({"stock": stock, "last_update": 0}, ignore_index=True)
        df = df.reset_index(drop=True)
        print(df.shape)
        df.to_csv(SAVEPATH + "stocks.csv", index=False)
    return select_to_crawl(df)


if __name__ == "__main__":
    #toCrawl = load_data()
    '''stock="procter_gamble-aktie"
    res = requests.get(STUMP + "aktien/" + stock)
    soup = BeautifulSoup(res.content, features="lxml")
    soup = getComparisonSoup(soup)
    rivals = extractRivals(soup, stock)
    tmp = {
        "rivals": rivals
    }
    print(rivals)
    path = SAVEPATH + dt.now().strftime("%Y%m%d") + "/"
    try:
        os.mkdir(SAVEPATH)
    except:
        True
    try:
        os.mkdir(path) 
    except:
        True
    with open(path + stock + ".json", "w") as f:
        json.dump(tmp, f)'''
    toCrawl = load_data()
    print("CRAWLING {}".format(len(toCrawl)))
    total = len(toCrawl)
    i = 0
    for stock in toCrawl:
        crawlStock(stock)
        i += 1
        print("FINISHED: {:03.2f}".format(float(i)/total*100))
