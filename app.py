from flask import Flask, render_template,request,redirect,url_for # For flask implementation
from bson import ObjectId # For ObjectId to work
from pymongo import MongoClient
import os
import time
import json
import time
from datetime import datetime
import pytz # $ pip install pytz
from tzlocal import get_localzone

app = Flask(__name__)

title = "Kismet/MonggDB MAC Search"
heading = "MAC Search"
local_tz = get_localzone()
time_format = "%Y-%m-%d %H:%M:%S"

client = MongoClient("mongodb://192.168.1.243:27017") #host uri
db = client["HEO_DB"]  #Select the database
devices = db["kismetDot11"] #Select the collection name

def redirect_url():
    return request.args.get('next') or \
           request.referrer or \
           url_for('index')

@app.route("/")
def tasks ():
    #Display the Uncompleted Tasks
    devices_l = devices.find({"done":"no"})
    a2="active"
    return render_template('index.html',a2=a2,devices=devices_l,t=title,h=heading)

def date_to_epoch(the_datetime_t):
    if not the_datetime_t:
        return(None)
    try:
        the_datetime_out = datetime(*[int(v) for v in the_datetime_t.replace('T', '-').replace(':', '-').split('-')])
        the_naive = datetime.strptime (str(the_datetime_out), time_format)
        the_local = local_tz.localize(the_naive, is_dst=None)
        the_utc = the_local.astimezone(pytz.utc)
        the_epoch_t = the_utc.strftime("%s")
        print("_OUT: ",the_datetime_out)
        print("_NAIVE: ",the_naive)
        print("_UTC: ",the_utc)
        print("_EPOCH: ",the_epoch_t)
        return(the_epoch_t)
    except Exception as e:
        print("Error converting to Epoch: ",e)
        return(None)

@app.route("/search", methods=['GET'])
def search():
    #Searching a Task with various references
    
    the_mac=request.values.get("macaddr")
    afterepoch = 0
    beforeepoch = time.time()

    afterepoch_t = date_to_epoch(request.values.get("beforedatetime"))    
    beforeepoch_t = date_to_epoch(request.values.get("afterdatetime"))

    try:
        afterepoch=int(afterepoch_t)
    except Exception as e:
        print(request.values.get("afterepoch"),": ",e,"  Default to 0")
        
    try:
        beforeepoch=int(beforeepoch_t)
    except Exception as e:
        print(request.values.get("beforeepoch"),": ",e,"  Default to time()")
        
    mac_query =  { "Data.kismet_device_base_last_time" : { "$gt":afterepoch, "$lt":beforeepoch } }
        
    if (the_mac):
        mac_query.update ( { "Data.kismet_device_base_macaddr" : { "$regex": str(the_mac) }  }  ) 

    devices_l = devices.find(mac_query)

    mac_list = []
    
    for mac in devices_l:
        #print(mac)
        mac_entry = {}
        lastepoch = int(mac["Data"]["kismet_device_base_last_time"])
        lastdatetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(lastepoch))
        mac_entry = { 
            "bssid" : "-",
            "channel" : mac["Data"]["kismet_device_base_channel"] , 
            "commonname" : mac["Data"]["kismet_device_base_commonname"],
            "encrypt" : mac["Data"]["kismet_device_base_crypt"] , 
            "lastseen" : lastdatetime,
            "macaddr" : mac["Data"]["kismet_device_base_macaddr"] , 
            "manuf" : mac["Data"]["kismet_device_base_manuf"],
            "phyname" : mac["Data"]["kismet_device_base_phyname"],
            "signal" : mac["Data"]["kismet_common_signal_last_signal"] , 
            "type" : mac["Data"]["kismet_device_base_type"],
        }
        
        dot11_device = mac["Data"]["dot11_device"]
        if isinstance(dot11_device, dict):
            if "dot11_device_last_bssid" in dot11_device.keys():
                mac_entry["bssid"] = dot11_device["dot11_device_last_bssid"]
                
        if (mac["Data"]["kismet_device_base_channel"] == "FHSS"):
            mac_entry["type"]

        mac_list.append(mac_entry)

    return render_template('searchlist.html',devices=mac_list,t=title,h=heading)

if __name__ == "__main__":
    app.run()
