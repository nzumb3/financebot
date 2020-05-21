from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime as dt
import json
import os

STUMP = "https://www.finanzen.net/"
#SAVEPATH = "G:/Coding/FinanceBot/data/"
SAVEPATH = "../data/"

NEWSPATH = "https://newslookup.com/results?ovs=&dp=&mt=-1&mtx=0&tp=&s=&groupby=no&cat=-1&fmt=&ut=&mkt=0&mktx=0&q=lufthansa&m="
GNEWSPATH = "https://news.google.com/search?q=lufthansa&hl=en-GB&gl=GB&ceid=GB:en"

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
    path = SAVEPATH + dt.now().strftime("%Y%m%d") + "/"
    os.mkdir(path)
    with open(path + str(round(dt.now().timestamp())) + ".json", "w") as f:
        json.dump(stock_sample, f)
    print("DONE!")

current = "deutsche_telekom-aktie"
crawlStock(current)