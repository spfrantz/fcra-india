# Foreign Contributions Regulation Act (India) Database

Registered organizations in India that receive contributions from foreign individuals, organizations, or governments are required to file quarterly disclosures. These disclosures are made public on organization websites and [in a database](https://fcraonline.nic.in/fc_qtrfrm_report.aspx) administered by the Ministry of Home Affairs (MHA). Unfortunately, the disclosures are published in PDF format and are accessible only through a long series of drop-down menus.

This project aims to make these disclosures more accessible by accomplishing the following objectives:
* Download and parse all disclosures to create a database of recipient organizations and their donors;
* Merge this dataset with [disclosures obtained](http://csip.ashoka.edu.in/estimating-philanthropic-capital-in-india-datasets/) by Ashoka University's Centre for the Study of Impact & Philanthropy under the Right to Information Act;
* Allow users to query the database by year, quarter, state, district, organization, and other characteristics, and to export a downloadable file for analysis;
* Create an interactive visualization of foreign flows to Indian organizations;
* Update the database each quarter.

This repository currently provides the code used to download (`fcra_download.py`) the FCRA disclosures and parse them (`parse_fcra.py`)into an SQLite database. It also includes sample data for West Bengal.

## Technical overview

The project uses `Selenium` to identify and download disclosures. A separate parsing routine uses `tabula-py` to extract data from the files. The output is an SQLite database with three tables:
* States and districts in the MHA database;
* Recipient organizations and their FCRA registration numbers;
* Every receipt disclosed by every organization.

Design and coding of the web interface to allow users to query and visualize the data will begin after all disclosures in the database have been downloaded and parsed.

## Requirements

The `remove_watermarks` function requires one package in addition to those listed in `requirements.txt`: [`pdf-unstamper.jar`](https://github.com/hwding/pdf-unstamper/releases) by [hwding](https://github.com/hwding) should be placed in the same directory as `parse_fcra.py`. The parser is tested with version 0.2.3.

This version requires the Linux/Unix package `pdfinfo` in order to verify the integrity of downloaded disclosures and to retry in the event the file is corrupt.

## Status

The full MHA database through 2019 has been downloaded and parsed. It includes 373,576 donations to 14,825 organizations. Donations have been grouped by donor and top 5000 institutional donors de-duplicated (i.e., donor organizations are often listed under various spellings, which are now standardized). The next steps are to: merge the scraped data with data obtained for earlier years by the Centre for Study of Impact and Philanthropy under the Right to Information Act; de-duplicate the donor names in the new dataset; perform an exploratory data analysis; and release the data to the public.
