import argparse
import datetime
from distutils import util
import os
import requests
import json
import threading
import time
import sys
from ConfigParser import ConfigParser
from dateutil.relativedelta import relativedelta

class spinnerThread (threading.Thread):
    
    def __init__(self, text = None, delay=None):
        threading.Thread.__init__(self)
        self.busy = True
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay): 
            self.delay = delay
        if text: 
            self.text = text

    def run(self):
        
        while 1:
            if self.busy:
                sys.stdout.write(self.text + self.spinner_generator.next())
                sys.stdout.flush()
                time.sleep(0.1)
                sys.stdout.write('\r')
                sys.stdout.write('\b')
            else: 
                sys.stdout.write(self.text + "OK")
                sys.stdout.flush()
                break

    def spinning_cursor(self):
        while True:
            for cursor in '|/-\\':
                yield cursor
                
    def stop(self):
        self.busy = False

def computeSLAfromJson(region, json_data, end_date, weekend, sla, args):
    tot_counter = 0
    overall_sum = 0
    
    undef_tot_number = 0
    undef_days = 0
    
    #loop over json returned to check OverallStatus->value_clean and FiHealthStatus->value_clean
    for item in sorted(json_data['measures'], key=lambda x : x["timestamp"]):
    #for item in json_data['measures']:
        overall_value = item['OverallStatus']['value_clean']
        fihealth_value = item['FiHealthStatus']['value_clean']
        
        timestamp = item['timestamp']            
        timestamp_date = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
        if timestamp_date <= end_date:
            timestamp_weekday = timestamp_date.weekday()
            if(weekend or (timestamp_weekday != 5 and timestamp_weekday != 6)):
                tot_counter += 1
                
                value_to_print = "undefined"
                if overall_value != "undefined" or fihealth_value != "undefined":
                    value_to_add = 0.                    
                    if overall_value == "undefined" and fihealth_value != "undefined":
                        undef_tot_number += 1
                        value_to_add = fihealth_value
                    elif overall_value != "undefined" and fihealth_value == "undefined":
                        undef_tot_number += 1
                        value_to_add = overall_value
                    else:
                        value_to_add = ( float(fihealth_value) + float(overall_value) ) / 2
                            
                    overall_sum += float(value_to_add)
                    value_to_print = float(value_to_add)
                else:
                    undef_tot_number += 2
                    undef_days += 1
                    
                if args.log:
                    sys.stdout.write(timestamp+": "+ str(value_to_print) + " (OverallStatus:"+str(overall_value)+";FiHealthStatus:"+str(fihealth_value)+")" + "\n")
            else:
                if args.log:
                    sys.stdout.write(timestamp+": "+"not considered\n")
            if args.log:
                sys.stdout.write("Day of the week: "+str(timestamp_weekday) + "\n")
                sys.stdout.write("-------------\n")

    avg_percentage = 0
    
    if tot_counter>0:
        
        if (tot_counter - undef_days) > 0:
            avg_percentage = overall_sum/(tot_counter - undef_days)
            
        sla_value = str(round(avg_percentage*100,2))+"%"
                
        if undef_tot_number > (tot_counter*undef_percentage/100):
            
            sys.stdout.write("The SLA for "+region+" is not respected: too many undefined ( > "+str(undef_percentage)+"% ) "+str(undef_tot_number)+"/"+str(tot_counter*2)+" ( partial SLA value: "+sla_value+" )"+"\n")
            sys.stdout.flush()
            return
    
    if avg_percentage >= sla:
        sys.stdout.write("The SLA for "+region+" is respected: "+sla_value+"\n")
    else:
        sys.stdout.write("The SLA for "+region+" is not respected: "+sla_value+"\n")

def main():
    
    global script_version
    script_version = "2.0.0"
    
    global undef_percentage
    undef_percentage = 10
    
    # Loads and manages the input arguments
    args = arg_parser()
    
    if args.version:
        sys.stdout.write("SLA script "+script_version+"\n")
        sys.exit(-1)

    sys.stdout.write("\n######################################\n")
    sys.stdout.write("# Thanks for using the SLA computing #\n")
    sys.stdout.write("######################################\n")
    sys.stdout.flush()
    
    # Config file
    if args.config_file is not None:
        config_file = args.config_file
    else:
        config_file = "config.ini"
    
    if args.start_day is None:
        # Setup default temporal period in which to work
        # TODO: sys.stdout.write on logger we are using default dates    
        #end_date = datetime.datetime.now()
        #end_string = (end_date).strftime("%Y-%m-%d")
        
        #start_date = datetime.datetime.strptime(end_date,"%Y-%m-%d") - relativedelta(months=1)
        #start_string = (start_date).strftime("%Y-%m-%d")        
        #TODO consider last entire month
        
        #today = datetime.datetime.now()
        #d = today - relativedelta(months=1)
        #start_date = date(d.year, d.month, 1)
        #datetime.date(2008, 12, 1)
        #date(today.year, today.month, 1) - relativedelta(days=1)
        #datetime.date(2008, 12, 31)
        
        today = datetime.datetime.now()
        d = today - relativedelta(months=1)
        start_date = d.replace(day=1)
        start_string = (start_date).strftime("%Y-%m-%d")  
        end_date = today.replace(day=1) - relativedelta(days=1)
        end_string = (end_date).strftime("%Y-%m-%d")
        
    else:
        # Setup user temporal period in which to work
        # TODO: sys.stdout.write on logger we are using user dates
        start_string = args.start_day
        try:
            start_date = datetime.datetime.strptime(start_string,"%Y-%m-%d")
        except Exception:
            sys.stdout.write("The start date is not valid. Please use the format '2017-06-27'")
            sys.exit(-1)
        
        #end_string = "2017-07-27"  
        end_date = datetime.datetime.now() - relativedelta(days=1)
        end_string = (end_date).strftime("%Y-%m-%d")
        #end_date = datetime.datetime.strptime(end_string,"%Y-%m-%d")
        
        if start_date >= end_date:
            sys.stdout.write("The start date is not valid. Please specify an older date")
            sys.exit(-1)
     
    
    # Read config file
    if not os.path.isfile(config_file):
        sys.stdout.write("Configuration file not found: {}").format(config_file)
        sys.exit(-1)
    try:
        config = ConfigParser()
        config.optionxform = str
        config.read(config_file)
    except Exception as e:
        sys.stdout.write("Problem parsing config file: {}").format(e)
        sys.exit(-1)

    sys.stdout.write("#\n") 
    sys.stdout.write("# The start date is: " + start_string + "\n")
    sys.stdout.write("# The end date is: " + end_string + "\n")
    
    # Get region to work on
    if args.region_id is None:
        regions = [config.get('region','id')]
    elif (args.region_id).lower() == "all":
        regions = json.loads(config.get("all","list"))
        sys.stdout.write("# The regions are: " + ", ".join(regions) + "\n")
    else:
        regions = [args.region_id]
        sys.stdout.write("# The region is: " + regions[0] + "\n")
        
    # Get sla parameter to work with
    try:
        sla = float(config.get('sla','value'))
    except Exception as e:
        sys.stdout.write("The sla value in the config file is not valid. Please specify a valid sla value: 0.95")
        sys.exit(-1)
    
    sys.stdout.write("# The SLA parameter is: " + str(sla*100) + "%\n")
        
    # Check if the week ends need to be considered
    if not args.weekend:
        weekend = False
    else:
        weekend = True#util.strtobool(args.weekend)
     
    considered = "No"
    if weekend:
        considered = "Yes"
    sys.stdout.write("# The week ends will be considered: " + considered + "\n")
    sys.stdout.write("#\n")
    sys.stdout.write("######################################\n")
    sys.stdout.flush()
    
    for region_id in regions:
        #perform request
        url = config.get('monitoring','url')+'/monitoring/regions/'+region_id+'/services'
        spinnerThread1 = spinnerThread("Calling " + url + "... ", 0.1)
        sys.stdout.write("\n")
        sys.stdout.flush()
        spinnerThread1.start()
        
        payload = {'since': start_string, 'aggregate': 'd'}
        response = requests.get(url, params=payload)
        #check json returned
        spinnerThread1.stop()
        time.sleep(0.1)
        sys.stdout.write("\n\n")
        if(response.status_code == 200):
            json_data = response.json()
            #sys.stdout.write(json_data)  
            computeSLAfromJson(region_id, json_data, end_date, weekend, sla, args)    
        else:
            sys.stdout.write("Response status code: " + str(response.status_code) + "\n")
        
        #sys.stdout.write("# REGIONS: " + ", ".join(regions) + "\n")
        sys.stdout.flush()
    
# Argument management
def arg_parser():
    parser = argparse.ArgumentParser(description='SLA computing')
    parser.add_argument("-c", "--config-file", help="-c Config file", required=False)
    parser.add_argument("-s", "--start-day", help="-s 2017-06-27", required=False)
    parser.add_argument("-r", "--region-id", help="-r Spain2", required=False)
    parser.add_argument("-w", "--weekend", help="if specified, the week ends will be considered", required=False, action='store_true')
    parser.add_argument("-l", "--log", help="if specified, prints the SLA for each day", required=False, action='store_true')
    parser.add_argument("-v", "--version", help="if specified, prints the version of the SLA script", required=False, action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    main()