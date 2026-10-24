import csv
import sqlite3
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

CSV_FILE = "Links.csv"
DB_FILE = "database.db"

# 2 + 3. create database and table if they do not exist
con = sqlite3.connect(DB_FILE)
con.execute("""CREATE TABLE IF NOT EXISTS tblLinks (
                   Link     TEXT PRIMARY KEY,
                   site    TEXT,
                   title    TEXT,
                   fromDate DATETIME,
                   tillDate DATETIME)""")

# 1. read the newspaper urls (first column; a header row is skipped automatically)
with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
    sites = [row[0].strip() for row in csv.reader(f)
             if row and row[0].strip().lower().startswith("http")]

# 4. for each site
for site in sites:
    try:
        # 4.1 visit link
        r = requests.get(site, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"FAILED {site}: {e}")
        continue

    T = datetime.now().strftime("%Y-%m-%d %H:%M:%S")      # 4.4 current date and time
    new = old = 0

    # 4.2 / 4.3 every <a> tag: href (H) and link text (LT)
    for a in soup.find_all("a", href=True):
        H = urljoin(site, a["href"].strip())               # relative -> full address
        LT = " ".join(a.get_text().split())
        if not H.startswith("http"):                       # skip mailto:, javascript: etc.
            continue
        if len(LT)<15:                       # skip mailto:, javascript: etc.
            continue
        if con.execute("SELECT 1 FROM tblLinks WHERE Link=?", (H,)).fetchone() is None:
            # 4.5 not found: insert (H, LT, T, T)
            con.execute("INSERT INTO tblLinks VALUES (?,?,?,?,?)", (H,site, LT, T, T))
            new += 1
        else:
            # 4.6 found: update till = T
            con.execute("UPDATE tblLinks SET tillDate=? WHERE Link=?", (T, H))
            old += 1

    con.commit()
    print(f"{site}: {new} new, {old} existing")

con.close()
