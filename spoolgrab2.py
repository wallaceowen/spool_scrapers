#!/usr/bin/env python3

"""spoolgrab2.py

A simple script to grab spool data from the 3dprinting wiki and put it into
an sqlite db.

Uses Beautiful soup for scrping the site's data
"""

import os
import re
import sqlite3
import lxml
from bs4 import BeautifulSoup

URL="https://help.matterhackers.com/article/129-empty-spool-weights"
LOCAL_FILENAME="129-empty-spool-weights.html"
DB_PATH="spool_weights2.db"
DB_CREATE_CMD="""CREATE TABLE spool_weights (
        id             INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        brand            VARCHAR,
        size           VARCHAR,
        year           VARCHAR,
        color          VARCHAR,
        width          VARCHAR,
        dia            VARCHAR,
        empty_grams    INTEGER
    )"""
INSERT_STMT = "INSERT INTO spool_weights (brand, size, year, color, width, dia, empty_grams) VALUES (?, ?, ?, ?, ?, ?, ?)"

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
    bs_object = fetch_wiki_data()
    BRAND, SIZE, YEAR, COLOR, WIDTH, DIA, WEIGHT = range(7)
    spools_data = bs_object.find("table").find("tbody")
    rec = re.compile(r'~*(?P<grams>\d+)')
    for row in spools_data.find_all("tr"):
        tds = row.find_all("td")
        if not len(tds):
            continue
        # Ignore the "Example" entry
        if tds[0].text.strip() == "Example":
            continue
        else:
            brand = tds[BRAND].string
            size = tds[SIZE].string
            year = tds[YEAR].string
            color = tds[COLOR].string
            width = tds[WIDTH].string
            dia = tds[DIA].string
            weight = tds[WEIGHT].string
            match = rec.match(weight.strip())
            if match:
                try:
                    grams = int(match.group('grams'))
                except ValueError:
                    print(f'Choked on grams field {weight} for brand {brand}')
                    grams = 0
                c.execute(INSERT_STMT, (brand, size, year, color, width, dia, weight))
            else:
                print(f'No match for grams in "{weight}"')
    db.commit()
    db.close()

if __name__ == '__main__':
    create_spools_db_from_wiki()
