# Foreign Contributions Regulation Act (India) Database

Registered organizations in India that receive contributions from foreign individuals, organizations, or governments are required to file quarterly disclosures. These disclosures are made public on organization websites and [in a database](https://fcraonline.nic.in/fc_qtrfrm_report.aspx) administered by the Ministry of Home Affairs (MHA). Unfortunately, the disclosures are published in PDF format and are accessible only through a long series of drop-down menus.

This project aims to make these disclosures more accessible by accomplishing the following objectives:
* Download and parse all disclosures to create a database of recipient organizations and their donors;
* Allow users to query the database by year, quarter, state, district, organization, and other characteristics, and to export a downloadable file for analysis;
* Create an interactive visualization of foreign flows to Indian organizations;
* Update the database each quarter.

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

The core routines for downloading (`fcra_download.py`) and parsing (`parse_fcra.py`) disclosures are working reliably. Example data from West Bengal is included in the `disclosures` and `database` folders of the repository.

## TODO
Issues to resolve before scraping the full database:
* Better connection error handling;
* Where `time.sleep()` is used to allow dynamic page elements to load, `implicitly_wait()` might be a better solution;
* Improved logging.

## References

TODO
