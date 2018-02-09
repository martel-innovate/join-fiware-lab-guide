# FIWARE Lab Nodes SLA

[![License](https://img.shields.io/badge/license-Apache%20License,%20Version%202.0-green.svg)](http://www.apache.org/licenses/LICENSE-2.0)

- [General description](#general-description)
- [Deployment and run](#deployment-and-run)
- [Additional features](#additional-features)
    - [Specify custom start date](#specify-custom-start-date)
    - [Specify custom region](#specify-custom-region)
    - [Include week ends](#include-week-ends)
- [Notes](#notes)

---

## General description

The nodes taking part to FIWARE Lab have to assure a certain level of quality 
defined through a Service Level Agreement (SLA). One of the conditions that 
must be satisfied is the services availability on the node that must be above 
the 95% threshold.  
A set of OpenStack services, called FIWARE Lab node services, runs on each of 
the FIWARE Lab nodes. The measurement of the availability of those services is 
managed through the use of the FIWARE Lab monitoring system tool. This FIWARE 
Lab monitoring system collects all the monitoring measurements from each FIWARE 
Lab node. These informations are centrally stored, aggregated and available 
through the FIWARE monitoring API for both real-time raw data and aggregated 
historical data.
  
FIWARE Lab Admins rely on the above pipeline to calculate the FIWARE Lab node 
overall service availability analysing the uptime status of: 

- The OpenStack services (Computing, Networking, Storage and Authentication) 
  using the [Monasca agent component installed on each FIWARE Lab 
  node](https://github.com/SmartInfrastructures/ceilometer-plugin-fiware#monasca-agent)
- The FIWARE Lab node Sanity Check using [FIWARE Lab 
  Health](https://fi-health.lab.fiware.org/)

In particular the hourly, daily and monthly averaged uptime of such services is 
stored in the historical monitoring database as a unique OverallStatus metric. 
The monthly value should not be lower than 95%, in order to respect the given 
SLA. 

This Python application is used to compute the averaged uptime of the services 
of each region by calling the API 
[Services4Region](https://federationmonitoring.docs.apiary.io/#reference/service/services4region)
of the FIWARE monitoring APIs.

The application can be run by each node by setting some optional arguments and 
a configuration file:

1) optional arguments:
    - -h, --help: shows the help message and exit
    - -c CONFIG_FILE, --config-file CONFIG_FILE: sets a configuration file 
      different from the default one
    - -s START_DAY, --start-day START_DAY: sets the start date of the 
      computation (must be before the 2017-07-27). If not set, the 
      previous month is considered.
    - -r REGION_ID, --region-id REGION_ID: sets the region to analyse. Setting 
      "ALL", all regions will be analysed
    - -w, --weekend: if specified, the week ends will be considered
    - -l, --log: if specified, prints the averaged uptime of the services for 
      each day
    - -v, --version: if specified, prints the version of this SLA script
2) configuration file:

```bash
- [monitoring]
url = http://130.206.84.4:11027
- [region]
id = region-id
- [sla]
value = 0.95
- [all]
list = ["PiraeusU", "SophiaAntipolis2", "Spain2", "Crete", "Volos", "Lannion4", "Budapest2", "Zurich2", "Brittany", "Vicenza", "Senegal", "Genoa", "Mexico"]
```

## Deployment and run

The application is intended to be run both by each single region and centrally 
by an admin for all the regions.

1) Create a virtualenv

   ```bash
   mkvirtualenv computingSLA
   ```

2) Install the dependencies

   ```bash
   pip install -r requirements.txt
   ```

3) Run the script in the virtualenv

   ```bash
   python slaComputing.py
   ```

## Additional features

### Specify custom start date

It is possible to specify a custom start date if you do not need the services' 
averaged uptime of the last month (default behaviour). 

This can be done using `--start-day, -s` as argument to the command line. 
Expected date format is `2017-01-01`.

### Specify custom region

It is possible to specify a custom single region (or all regions) on which to 
elaborate data. 

This can be done using `--region-id, -r` as argument to the command line. 
Expected region-id could be the region-id or the "ALL" keyword.

### Include week ends

It is possible to *include* the weekends in the computation.

This can be done using `--weekend, -w` as argument to the command line.

## Notes

The script does not consider the "unknown data" for a specific node, if this 
one is less than 33%.