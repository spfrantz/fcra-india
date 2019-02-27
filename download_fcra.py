#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from selenium import webdriver
from selenium.webdriver.support.ui import Select
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
                    "/Users/Sam/Documents/Python/WebDrivers/chromedriver",
                    options=chrome_options)

logging.basicConfig(filename="download_fcra.log", level=logging.INFO, \
                    format="%(asctime)s:%(levelname)s:%(message)s")

def main():
    '''
    Demonstrates how to initialize a new SQLite database to store FCRA disclosures.
    Currently downloads all disclosures for West Bengal (state ID 14).
    '''
    logging.info("Started")
    # Prepare a new SQLite database
#    db_name = input("Enter name of new or existing database file ./database/") + ".db"
#    db, c = database_connect(db_name)
#    initialize_database()
#    populate_district_table()

    # Get list of years and year-quarters currently available
    years = get_years()
    qtrs = get_quarters(years)

    # Open existing database
    db_name="example_wb.db" # change back to: "example_wb.db"
    db, c = database_connect(db_name)

    # Query database for numerical IDs and names of all districts of West Bengal
    distnames = c.execute("SELECT state_dist_id, state_dist_name \
                                     FROM districts WHERE state_id='14'").fetchall()

    # Prepare data to feed to scraping routine (West Bengal only for now)
    districts = dict(distnames)
    to_scrape = {'14':districts}

    # Download all districts of West Bengal for all quarters in database.
    download_disclosures(qtrs, to_scrape)

    driver.close()
    logging.info("Ended")

    return 0

# Helper functions
def get_years():
    '''Retrieve a list of fiscal years available in the FCRA database'''
    years = []
    driver.get('https://fcraonline.nic.in/fc_qtrfrm_report.aspx')
    years_options = driver.find_elements_by_xpath \
                ("//select[@id='ddl_block_year']//option[@value!='0']")
    for option in years_options:
        years.append(option.text)
    print("Years available: ", years)
    return years

def get_quarters(years):
    '''Retrieve a list of quarters available for each fiscal year'''
    quarters = []
    driver.get('https://fcraonline.nic.in/fc_qtrfrm_report.aspx')
    for year in years:
        years_menu = Select(driver.find_element_by_id("ddl_block_year"))
        years_menu.select_by_value(year)
        sleep(2)
        quarters_options = driver.find_elements_by_xpath \
            ("//select[@id='ddl_qtr_returns']//option")
        for option in quarters_options[1:]:
            option_value = option.get_attribute("value")
            quarters.append((year, option_value))
    print("Quarters available: ", quarters)
    return quarters

def get_state_list():
    '''Construct a dictionary of numerical state IDs and state names'''
    driver.get('https://fcraonline.nic.in/fc_qtrfrm_report.aspx')
    states_values = (driver.find_elements_by_xpath \
                   ("//select[@id='DdnListState']//option"))
    state_ids = []
    for item in states_values:
        state_ids.append(item.get_attribute("value"))
    print(state_ids)
    states = {}
    for id in state_ids[1:]:
        states[id] = (driver.find_element_by_xpath \
                                  ("//select[@id='DdnListState']//option[@value=" \
                                   + '"' + id + '"' + ']').text)

    # Save states list to file
    pickle.dump(states, open("./obj/states.p", "wb"))
    print("States available: ", states)
    return states

def get_district_lists(states):
    '''
    Retrieve a list of districts in the FCRA database by navigating the
    drop-down menus. Takes as input a dictionary that has state IDs as keys.
    Returns a dictionary of dictionaries in the following format:
        {'state1_id':{'state1_dist1_id':'state1_dist1_name'...}, /
        'state2_id':{'state2_dist1_id':'state2_dist1_name'...}...}
    '''
    district_list = {}
    for id in states.keys():
        state_dists = {}
        driver.get('https://fcraonline.nic.in/fc_qtrfrm_report.aspx')
        states_menu = Select(driver.find_element_by_id("DdnListState"))
        states_menu.select_by_value(id)
        sleep(3)
        dist_options = (driver.find_elements_by_xpath \
                        ("//select[@id='DdnListdist']//option"))
        for option in dist_options[1:]:
            dist_id = option.get_attribute("value")
            dist_name = option.text
            state_dists[dist_id] = dist_name
        district_list[id] = state_dists

    # Save districts list to file
    pickle.dump(district_list, open("./obj/districts.p", "wb"))
    return(district_list)

# SQLite database initialization
def database_connect(db_name):
    '''Connect to SQLite database'''
    db = sqlite3.connect("./database/" + db_name)
    c = db.cursor()
    return db, c

def initialize_database():
    '''Set up an SQLite database'''
    # Districts table
    db.execute("CREATE TABLE IF NOT EXISTS `districts` ( \
    	`dist_id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, \
    	`state_id`	VARCHAR(3) NOT NULL, \
    	`state_name`	VARCHAR(25) NOT NULL, \
    	`state_dist_id`	VARCHAR(4) NOT NULL, \
    	`state_dist_name` VARCHAR(255) NOT NULL)")
    db.commit()

    # Organizations table
    db.execute("CREATE TABLE IF NOT EXISTS `organizations` ( \
        `org_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
        `fcra` VARCHAR(15) NOT NULL, \
        `org_name` VARCHAR(255))")
    db.commit()

    # Disclosures table
    db.execute("CREATE TABLE IF NOT EXISTS `disclosures` ( \
	`disc_id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
	`fcra`	VARCHAR(15) NOT NULL, \
	`year`	VARCHAR(8), \
	`quarter`	VARCHAR(4), \
	`donor_name`	VARCHAR(255), \
	`donor_type`	VARCHAR(255), \
	`donor_address`	TEXT, \
	`purposes`	VARCHAR(255), \
	`amount` VARCHAR(20))")
    db.commit()

def populate_district_table():
    '''Populate database table of states and districts'''
    print("Gathering all districts for all states. This will take a few minutes.")
    states = get_state_list()
    districts = get_district_lists(states)
    counter = 0
    for state in states.keys():
        for district in districts[state].keys():
            c.execute("INSERT INTO districts (state_id, state_name, state_dist_id, \
                                      state_dist_name) VALUES (:state_id, \
                                      :state_name, :state_dist_id, :state_dist_name)", \
                                    {'state_id':state, 'state_name':states[state], \
                                    'state_dist_id':district, \
                                    'state_dist_name':districts[state][district]})
            counter += 1
    db.commit()
    print("Populated districts table with ", counter, "districts")


# Linux only (requires pdftk): verify integrity of downloaded file
def verify_pdf(path):
    '''Checks PDF integrity and re-downloads if file appears corrupt'''
    result = subprocess.run([verify_pdf.sh, path], stdout=subprocess.PIPE])
    return result

def get_file():
    '''Downloads a disclosure'''
    r = requests.get(starturl + org + "R&fin_year=" \
                     + yr +"&quarter=" + qtr)
    with open(filepath + '/D_' + org + '_' + yr + '_' \
              + qtr +".pdf", 'wb') as file:
        file.write(r.content)
    print("Wrote file D_" + org + '_' + yr + '_' \
              + qtr +".pdf to disk")
    try_count += 1
    sleep(1)
    return(filepath + '/D_' + org + '_' + yr + '_' + qtr +".pdf")


# Download disclosures of selected years, quarters, districts
def download_disclosures(quarters, districts):
    '''Downloads PDF disclosures for the quarters and districts specified by
    the user

    INPUT:
        quarters: [('yyyy-yyyy', 'q')...] e.g., [('2015-2016', '3'), ('2015-2016', '4')]
        districts: {'stateid':{'districtid1':'name1'...}...}
    '''
    starturl='https://fcraonline.nic.in/Fc_qtrFrm_PDF.aspx?rcn='
    for quarter in quarters:
        (yr, qtr) = quarter
        for state in districts.keys():
            for district in districts[state].keys():
                try:
                    # Navigate the drop-down menus
                    driver.get('https://fcraonline.nic.in/fc_qtrfrm_report.aspx')
                    years_menu = Select(driver.find_element_by_id("ddl_block_year"))
                    years_menu.select_by_value(yr)
                    sleep(2.5)
                    quarters_menu = Select(driver.find_element_by_id("ddl_qtr_returns"))
                    quarters_menu.select_by_value(qtr)
                    states_menu = Select(driver.find_element_by_id("DdnListState"))
                    states_menu.select_by_value(state)
                    sleep(2.5)
                    districts_menu = Select(driver.find_element_by_id("DdnListdist"))
                    districts_menu.select_by_value(district)
                    submit_btn = driver.find_element_by_id("Button1")
                    submit_btn.click()

                    # Create directory to store district disclosures if none exists
                    filepath = "./disclosures/" + state +'/' + district
                    os.makedirs(filepath, exist_ok=True)

                    sleep(2)

                except requests.exceptions.ConnectionError as e:
                    logging.exception(f"{yr} q{qtr} state {state} \
                                      district {district} failed: \
                                      Connection error")
                    sleep(10)
                    continue

                except:
                    logging.exception(f"{yr} q{qtr} {state} {district} failed.")
                    sleep(10)
                    continue

                # Compile dict of organization names and FCRA reg numbers
                dyq_orgs={}
                null_returns=set()
                table_rows = driver.find_elements_by_xpath \
                                    ("//table[@id='GridView1']//tr")
                for row in table_rows[1:]:
                    table_data = row.find_elements_by_tag_name('td')
                    org_name = table_data[1].text
                    org_fcra = table_data[2].text
                    amount = table_data[3].text

                    # Save dictionary of district-year-quarter disclosures to scrape
                    dyq_orgs[org_fcra] = org_name

                    # If amount is 0.00, add to set of null returns (don't download!)
                    if amount == "0.00":
                        null_returns.add(org_fcra)

                # Check if each organization is already in the database; if not,
                # update organizations data table
                for org in dyq_orgs.keys():
                    rows = c.execute("SELECT org_id FROM organizations WHERE \
                                     fcra = :key", {'key':org}).fetchall()
                    if len(rows) == 0:
                        c.execute("INSERT INTO organizations (fcra, org_name) \
                                  VALUES (:fcra, :org_name)", {'fcra':org,\
                                  'org_name':dyq_orgs[org]})
                db.commit()

                # Save PDF disclosures
                # TODO: don't download returns with amount 0.00
                for org in dyq_orgs.keys():
                    if org in null_returns:
                        continue
                    else:
                        try_count = 0
                        path = get_file()
                        result = verify_pdf(path)
                        if result == "broken":
                            print("File corrupted, retrying")
                            logging.info(f"Re-downloaded %s", path)
                            while try_count < 3 & result=="broken":
                                get_file()
                        else:
                            continue
    return 0

if __name__ == "main":
    main()
