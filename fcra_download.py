#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import modules_dl as dl
import os
import pickle
import requests
import sqlite3
from time import sleep

# Set up Chrome webdriver
chrome_options=webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920x1080')
# Path to your chromedriver here
driver = webdriver.Chrome(executable_path= \
                    "/usr/bin/chromedriver",
                    options=chrome_options)

logging.basicConfig(filename="download_fcra.log", level=logging.INFO, \
                    format="%(asctime)s:%(levelname)s:%(message)s")

logging.info("Started")
# Prepare a new SQLite database
#    db_name = input("Enter name of new or existing database file ./database/") + ".db"
#    db, c = database_connect(db_name)
#    initialize_database()
#    populate_district_table()

# Get list of years and year-quarters currently available


years = dl.get_years(driver)
qtrs = dl.get_quarters(years, driver)

# Open existing database: Andaman & Nicobar Islands
db_name="a_n.db" 
db, c = dl.database_connect(db_name)

# dl.initialize_database(db)

# Query database for numerical IDs and names of all districts of Andaman & Nicobar
# distnames = c.execute("SELECT state_dist_id, state_dist_name \
                                # FROM districts WHERE state_id='002'").fetchall()

# Read district table from pickle
with open('./obj/districts.p', 'rb') as f:
    districts = pickle.load(f)

# Prepare data to feed to scraping routine (A&N Islands only for now)
# districts = dict(distnames)
to_scrape = {'24':districts['24']}

# Download all districts of West Bengal for all quarters in database.
dl.download_disclosures(qtrs, to_scrape, driver, db, c)

driver.close()
logging.info("Ended")
