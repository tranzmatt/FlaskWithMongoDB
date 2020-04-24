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

@app.route("/list")
def lists ():
    #Display the all Tasks
    devices_l = devices.find()
    a1="active"
    return render_template('index.html',a1=a1,devices=devices_l,t=title,h=heading)

@app.route("/")
@app.route("/uncompleted")
def tasks ():
    #Display the Uncompleted Tasks
    devices_l = devices.find({"done":"no"})
    a2="active"
    return render_template('index.html',a2=a2,devices=devices_l,t=title,h=heading)


@app.route("/completed")
def completed ():
    #Display the Completed Tasks
    devices_l = devices.find({"done":"yes"})
    a3="active"
    return render_template('index.html',a3=a3,devices=devices_l,t=title,h=heading)

@app.route("/done")
def done ():
    #Done-or-not ICON
    id=request.values.get("_id")
    task=devices.find({"_id":ObjectId(id)})
    if(task[0]["done"]=="yes"):
        devices.update({"_id":ObjectId(id)}, {"$set": {"done":"no"}})
    else:
        devices.update({"_id":ObjectId(id)}, {"$set": {"done":"yes"}})
    redir=redirect_url()    

    return redirect(redir)

@app.route("/action", methods=['POST'])
def action ():
    #Adding a Task
    name=request.values.get("name")
    desc=request.values.get("desc")
    date=request.values.get("date")
    pr=request.values.get("pr")
    devices.insert({ "name":name, "desc":desc, "date":date, "pr":pr, "done":"no"})
    return redirect("/list")

@app.route("/remove")
def remove ():
    #Deleting a Task with various references
    key=request.values.get("_id")
    devices.remove({"_id":ObjectId(key)})
    return redirect("/")

@app.route("/update")
def update ():
    id=request.values.get("_id")
    task=devices.find({"_id":ObjectId(id)})
    return render_template('update.html',tasks=task,h=heading,t=title)

@app.route("/action3", methods=['POST'])
def action3 ():
    #Updating a Task with various references
    name=request.values.get("name")
    desc=request.values.get("desc")
    date=request.values.get("date")
    pr=request.values.get("pr")
    id=request.values.get("_id")
    devices.update({"_id":ObjectId(id)}, {'$set':{ "name":name, "desc":desc, "date":date, "pr":pr }})
    return redirect("/")

def date_to_epoch(the_datetime_t):
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
    
    print('Running search')
    
    d = dict((db, [collection for collection in client[db].list_collection_names()]) for db in client.list_database_names())
    print(json.dumps(d))
    
    the_mac=request.values.get("macaddr")
    afterepoch = 0
    beforeepoch = time.time()
    aftertime_t = None
    beforetime_t = None
    
    afterdatetime_t = request.values.get("afterdatetime")
    beforedatetime_t = request.values.get("beforedatetime")

    print("_T AFTER: ",afterdatetime_t,": BEFORE : ",beforedatetime_t)
    
    # 2020-04-23T19:30
    
    beforeepoch_t = date_to_epoch(beforedatetime_t)
    afterepoch_t = date_to_epoch(afterdatetime_t)


    '''
    afterdate_t=request.values.get("afterdate")
    aftertime_t=request.values.get("aftertime")

    beforedate_t=request.values.get("beforedate")
    beforetime_t=request.values.get("beforetime")

    print("AFTER: ",afterdate_t,":: ",aftertime_t," BEFORE: ",beforedate_t,":: ",beforetime_t)

    #afterepoch_utc = local_datetime.astimezone(afterepoch_t.utc)   
    print(afterepoch_out,"-->",beforeepoch_out)
    '''
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

    print(mac_query)

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
