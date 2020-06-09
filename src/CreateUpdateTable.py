import pandas as pd
from pathlib import Path
import time


SAVEPATH = str((Path(__file__).parent / "../data/").resolve()) + "/"

def getToCrawl():
    out = []
    with open(SAVEPATH + "stocks.txt", "r") as f:
        for line in f.readlines():
            out.append(line.replace("\n", ""))
    return out

li = getToCrawl()
last_update = []

for stock in li:
    last_update.append(0)

df = pd.DataFrame()
df['stock'] = li
df['last_update'] = last_update

df.to_csv(SAVEPATH + "stocks.csv", index=False)