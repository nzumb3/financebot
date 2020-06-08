import os
from pathlib import Path

SAVEPATH = str((Path(__file__).parent / "../data/").resolve()) + "/"
tmp = set()
for a, b, c in os.walk(str((Path(__file__).parent / "../data/").resolve()) + "/"):
    for dat in c:
        tmp.add(dat[:-5])
#print(len(tmp))

#os.remove(SAVEPATH + "stocks.txt")
with open(SAVEPATH + "stocks.txt", "w") as f:
    for stock in tmp:
        f.write(str(stock.encode("utf-8"))+"\n")
print("SAVED!")