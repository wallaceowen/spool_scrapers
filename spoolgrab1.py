#!/usr/bin/env python3

"""spoolgrab.py

A simple script to grab spool data from the 3dprinting wiki and put it into
an sqlite db.

Uses Beautiful soup for scrping the site's data
"""

import os
import re
import sqlite3
import lxml
from bs4 import BeautifulSoup

URL="https://3dprintingwiki.info/wiki/Spool_weight"
LOCAL_FILENAME="Spool_weight.html"
DB_PATH="spool_weights.db"
DB_CREATE_CMD="""CREATE TABLE spool_weights (
        id             INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        mfr            VARCHAR,
        url            VARCHAR,
        empty_grams    INTEGER
    )"""
INSERT_STMT = "INSERT INTO spool_weights (mfr, url, empty_grams) VALUES (?, ?, ?)"

def fetch_wiki_data():
    os.system(f"wget -q -O {LOCAL_FILENAME} {URL}")
    bs_object = BeautifulSoup(open(LOCAL_FILENAME, encoding='utf-8'), "lxml")
    return bs_object

def make_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(DB_CREATE_CMD)
    db.commit()
    return db

def create_spools_db_from_wiki():

    # Delete any existing database and make a fresh one
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    db = make_db()

    c = db.cursor()
    rec = re.compile(r'~*(?P<grams>\d+)')
    bs_object = fetch_wiki_data()
    spools_data = bs_object.find("table", attrs={"class": "wikitable sortable"}).find("tbody")
    for row in spools_data.find_all("tr"):
        tds = row.find_all("td")
        if not len(tds):
            continue
        # Ignore the "Example" entry
        if tds[0].string.strip() == "Example":
            continue
        else:
            mfr = tds[0].string
            url = tds[1].string
            weight = tds[2].string
            match = rec.match(weight.strip())
            if match:
                try:
                    grams = int(match.group('grams'))
                except ValueError:
                    grams_str = tds[2].text
                    # Bad field content currently only hitting
                    # 3 lines, and two are the same.
                    # If it gets worse I'll switch to a regex.
                    if grams_str.startswith("est. ~200-220g"):
                        grams = 220
                    elif grams_str.startswith("133g (seems to be"):
                        grams = 133
                    else:
                        print(f'Choked on grams field {grams_str} for mfr {mfr}')
                        grams = 0
                c.execute(INSERT_STMT, (mfr, url, grams))
            else:
                print(f'No match for grams in "{weight}"')

    db.commit()
    db.close()

if __name__ == '__main__':
    create_spools_db_from_wiki()
