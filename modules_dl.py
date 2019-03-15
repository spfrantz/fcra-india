import logging
from selenium.webdriver.support.ui import Select
import subprocess
import os
import pickle
import requests
import sqlite3
from time import sleep

def get_years(driver):
    '''Retrieve a list of fiscal years available in the FCRA database'''
    years = []
    driver.get('https://fcraonline.nic.in/fc_qtrfrm_report.aspx')
    years_options = driver.find_elements_by_xpath \
                ("//select[@id='ddl_block_year']//option[@value!='0']")
    for option in years_options:
        years.append(option.text)
    print("Years available: ", years)
    return years

def get_quarters(years, driver):
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

def get_state_list(driver):
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

def get_district_lists(states, driver):
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

def initialize_database(db):
    '''Set up an SQLite database'''
    # Districts table
    db.execute("CREATE TABLE IF NOT EXISTS `districts` ( \
    	`dist_id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, \
    	`state_id`	VARCHAR(3) NOT NULL, \
    	`state_name`	VARCHAR(25) NOT NULL, \
    	`state_dist_id`	VARCHAR(4) NOT NULL, \
    	`state_dist_name` VARCHAR(255) NOT NULL)")

    # Organizations table
    db.execute("CREATE TABLE IF NOT EXISTS `organizations` ( \
        `org_id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
        `fcra` VARCHAR(15) NOT NULL, \
        `org_name` VARCHAR(255))")

    # Files table
    db.execute("CREATE TABLE IF NOT EXISTS `files` ( \
	`file_id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
	`fcra`	VARCHAR(10) NOT NULL, \
    `dist_id` INTEGER NOT NULL, \
	`path`	VARCHAR(255) UNIQUE, \
	`year`	VARCHAR(15) NOT NULL, \
	`quarter` VARCHAR(4) NOT NULL, \
    `dldate` DATETIME DEFAULT CURRENT_TIME)")

    # Disclosures table
    db.execute("CREATE TABLE IF NOT EXISTS `disclosures` ( \
	`disc_id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
    `file_id`	INTEGER NOT NULL, \
	`donor_name`	 VARCHAR(255), \
	`donor_type` 	VARCHAR(255), \
	`donor_address`	TEXT, \
	`purposes`	VARCHAR(255), \
	`amount` VARCHAR(20))")

    db.commit()

def populate_district_table(driver, db, c):
    '''Populate database table of states and districts'''
    print("Gathering all districts for all states. This will take a few minutes.")
    states = get_state_list(driver)
    districts = get_district_lists(states, driver)
    counter = 0
    for state in states.keys():
        for district in districts[state].keys():
            c.execute("INSERT INTO districts (state_id, state_name, \
                    state_dist_id, state_dist_name) VALUES (:state_id, \
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
    result = subprocess.run(["./verify_pdf.sh", path], stdout=subprocess.PIPE)
    return result

def get_file(yr, qtr, org, filepath, starturl, db, c, state, district):
    '''Downloads a disclosure'''
    r = requests.get(starturl + org + "R&fin_year=" \
                     + yr +"&quarter=" + qtr)

    # Look up district id
    dist_id, = c.execute("SELECT dist_id FROM districts WHERE \
                         state_id = :state AND state_dist_id = :district", \
                         {'state':state, 'district':district})

    # Create file information in database
    c.execute("INSERT INTO files (fcra, year, quarter, dist_id) VALUES \
              (:fcra, :year, :quarter, :dist_id)", {'fcra':org, 'year':yr, \
              'quarter':qtr, 'dist_id':dist_id})
    db.commit()

    # Get unique file ID to append to filename (unpack tuple)
    file_id, = c.execute("SELECT file_id FROM files WHERE fcra = :org AND \
                        year = :yr AND quarter = :quarter", {'org':org, \
                        'yr':yr, 'quarter':qtr}).fetchone()

    # Download disclosure
    full_path = (filepath + '/D_' + str(file_id) + '_' + org + '_' + yr + '_' \
              + qtr + ".pdf")

    with open(full_path, 'wb') as file:
        file.write(r.content)

    # Associate path with file_id in database
    c.execute("UPDATE files SET path = :full_path WHERE file_id = :file_id", \
              {'file_id':file_id, 'full_path':full_path})
    db.commit()

    print("Wrote file D_" + str(file_id) + '_' + org + '_' + yr + '_' \
              + qtr +".pdf to disk")
    sleep(1)
    return(full_path)


# Download disclosures of selected years, quarters, districts
def download_disclosures(quarters, districts, driver, db, c):
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
                for org in dyq_orgs.keys():
                    try:
                        if org in null_returns:
                            continue
                        else:
                            try_count = 0
                            path = get_file(yr, qtr, org, filepath, starturl, \
                                            db, c, state, district)
                            result = verify_pdf(path)
                            while result == "broken" and try_count < 3:
                                print("File corrupted, retrying")
                                logging.info(f"Re-downloading %s", path)
                                sleep(5)
                                get_file(yr, qtr, org, filepath, starturl, \
                                         db, c, state, district)
                                try_count += 1
                            else:
                                continue
                    except:
                        logging.exception(f"Exception at {org} {yr} {qtr}")

            logging.info(f"Finished {state} {yr} qtr {qtr}")
            print(f"Finished state {state} {yr} qtr {qtr}")

    return 0
