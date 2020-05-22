from bs4 import BeautifulSoup
from pathlib import Path
import requests
import time
from datetime import datetime as dt
import json
import os

STUMP = "https://www.finanzen.net/"
#SAVEPATH = "G:/Coding/FinanceBot/data/"
SAVEPATH = str((Path(__file__).parent / "../data/").resolve()) + "/"

ENNEWS = "https://newslookup.com/results?p={}&q={}&dp=4&mt=-1&ps=10&s=1&cat=-1&fmt=&groupby=no&site=&dp=4"
DENEWS = "https://www.finanzen.net/nachrichten/alle/{}/{}" #no -aktie     de lufthansa

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
    r = requests.get(link)
    return BeautifulSoup(r.content, features="lxml")

def extractRivals(soup, current):
    rivals = []
    for td in soup.find_all("td"):
        for a in td.find_all("a"):
            if len(a["href"].split("/")) > 2 and a["href"].split("/")[2] != current and a["href"].split("/")[1] == "aktien" and a["href"].split("-")[-1] == "aktie":
                rivals.append(a["href"].split("/")[-1])
    return rivals

def extractName(soup):
    return "_".join(list(filter(lambda x: x.lower() != "aktie",soup.title.string.split(" | ")[0].split(" "))))

def exctractEnText(name):
    times, bodies, out = [], [], []
    for i in range(1,3):
        tmppath = ENNEWS.format(i, current[:-6].replace("_", "+"))
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
    deres = requests.get(DENEWS.format("de", name[:-6].replace(" ", "_")))
    enres = requests.get(DENEWS.format("en", name[:-6].replace(" ", "_")))
    desoup = BeautifulSoup(deres.content, features="lxml")
    ensoup = BeautifulSoup(enres.content, features="lxml")
    deheaders, detimes = [], []
    enheaders, entimes = [], []
    out = {"de":[], "en": []}
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
        out['de'].append((t, h))
    for (h, t) in zip(enheaders, entimes):
        out['en'].append((t, h))
    return out

def crawlStock(name):
    if name[-6:] != "-aktie":
        name += "-aktie"
    print("Crawling {}".format(name))
    res = requests.get(STUMP + "aktien/" + name)
    soup = BeautifulSoup(res.content, features="lxml")
    stock_sample = {
        "postfix": name,
        "name": extractName(soup),
        "wkn": extractWKN(soup),
        "ts": dt.now().strftime("%Y.%m.%d %H:%M"),
        "features": extractTableFeatures(soup)
    }
    print("Zzzzz...")
    time.sleep(5)
    print("Crawling Comparison")
    comp_soup = getComparisonSoup(soup)
    stock_sample["rivals"] = extractRivals(comp_soup, name)
    print("Saving...")
    #with open(SAVEPATH + str(round(dt.now().timestamp())) + ".json", "w") as f:
    os.mkdir(SAVEPATH)
    path = SAVEPATH + dt.now().strftime("%Y%m%d") + "/"
    os.mkdir(path)
    with open(path + str(round(dt.now().timestamp())) + ".json", "w") as f:
        json.dump(stock_sample, f)
    print("DONE!")

current = "deutsche_telekom-aktie"
#crawlStock(current)
#res = requests.get()
#depath = DENEWS.format(current[:-6].replace("_", "+"))
#enpath = ENNEWS.format(current[:-6].replace("_", "+"))

#res = requests.get(enpath)
#soup = BeautifulSoup(res.content, features="lxml")

print(extractHeaders(current))