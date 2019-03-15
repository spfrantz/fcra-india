#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pandas
import sqlite3
import os
import subprocess
from tabula import read_pdf

db = sqlite3.connect("./database/2019-03-fcra.db")
c = db.cursor()

logging.basicConfig(filename="parse_fcra.log", level=logging.INFO, \
                    format="%(asctime)s:%(levelname)s:%(message)s")

def main():
    '''Parses FCRA PDF disclosures and writes them to an SQLite database'''
    logging.info("Started")
    
    # remove_watermarks("./disclosures/")
    
    pdfs = set()
    for root, dirs, files in os.walk('./disclosures/'):
        for name in files:
                if name.endswith('.pdf'):
                    path = os.path.abspath(os.path.join(root, name))
                    pdfs.add(path)
                    print("Found ", path)
    for file in pdfs:
        try:           
            data, fcra, year, quarter, file_id = parse_disclosure(file)
            print("Parsed ", file)
            if data is None:
                print("No disclosures in ", file)
                logging.info(f"No disclosures in {file}")
                continue
            else:
                write_data(data, fcra, year, quarter, file_id)
                print("Wrote ", file)
        except:
            logging.exception(f"Failure at {file}")
            
    logging.info("Finished")
    return 0

def remove_watermarks(path):
    '''
    Removes the Ministry of Home Affairs watermark from disclosures
    in the specified path. Uses pdf-unstamper by hwding:
        
        https://github.com/hwding/pdf-unstamper
    '''
    # File-by-file (slow!)
#    subprocess.call(["java", "-jar", "./parser/pdf-unstamper.jar", "-d", "-i", path, \
#                     "-k", "Ministry of Home Affairs"])
    
    # Recursively (fast!)
    subprocess.call(["java", "-jar", "./parser/pdf-unstamper.jar", "-d", "-r", \
                     "-I", path, "-k", "Ministry of Home Affairs"])
    
def parse_disclosure(disclosure):
    '''Extracts data from disclosure PDF and returns a pandas dataframe'''
    try:
        data = read_pdf(disclosure, spreadsheet=True, \
                        columns=(49.57,132.1,214.52,298.1,380.65,462.4), \
                        pages="all", pandas_options={'header':None})
    except:
        logging.exception(f"Parser failed on {disclosure}")
        return None, None, None, None
    
    # Get FCRA, year, quarter from filename
    if data is None:
        print("No data in table ", disclosure)
        return None, None, None, None
    
    filename_data = disclosure.strip('pdf').split('_')
    file_id = filename_data[1]
    fcra = filename_data[2]
    year = filename_data[3]
    quarter=filename_data[4]
    
    # Check that the dataframe has 6 columns and at least 1 row
    length, width = data.shape

    if width != 6:
        logging.warning(f"Invalid table for {disclosure}")
        return None, None, None, None
    
    if length == 0:
        logging.warning(f"Invalid table for {disclosure}")
        return None, None, None, None
    
    # Clean the data by removing header rows and special characters
    data = data.replace({'\r':' '}, regex=True)
    
    # Surely not the best way...
    bool1 = data[4].str.contains('Purpose')
    bool2 = data[5].str.contains('Amount')
    
    for i in range(len(bool1)):
        if bool1[i] == True or bool2[i] == True:
            data = data.drop(i)
    
    return(data, fcra, year, quarter, file_id)

def write_data(disc_df, fcra, year, quarter, file_id):
    '''Takes a pandas dataframe and writes it to SQLite disclosures table'''
    for index, row in disc_df.iterrows():
        c.execute("INSERT INTO disclosures (donor_name, donor_type, \
                    donor_address, purposes, amount, file_id) VALUES \
                    (:donor_name, :donor_type, :donor_address, :purposes, \
                    :amount, :file_id)", {'donor_name':row[1], \
                    'donor_type':row[2], 'donor_address':row[3], \
                    'purposes':row[4], 'amount':row[5], 'file_id':file_id})
        db.commit()
    return 0

if __name__ == "main":
    main()


