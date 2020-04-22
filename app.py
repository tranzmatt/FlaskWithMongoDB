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

client = MongoClient("mongodb://192.168.100.243:27017") #host uri
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

@app.route("/search", methods=['GET'])
def search():
    #Searching a Task with various references
    
    print('Running search')
    
    d = dict((db, [collection for collection in client[db].list_collection_names()]) for db in client.list_database_names())
    print(json.dumps(d))
    
    the_mac=request.values.get("macaddr")
    afterepoch = 0
    beforeepoch = time.time()
    
    ts = time.time()
    utc_now, now = datetime.utcfromtimestamp(ts), datetime.fromtimestamp(ts)
    
    print(utc_now,now)
    
    afterepoch_t=int(request.values.get("afterepoch"))
    beforeepoch=int(request.values.get("beforeepoch"))
    try:
        afterepoch_t=int(request.values.get("afterepoch"))
    except Exception as e:
        print(request.values.get("afterepoch"),": ",e,"  Default to 0")
        
    try:
        beforeepoch=int(request.values.get("beforeepoch"))
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
        mac_entry = { 
            "bssid" : "-",
            "channel" : mac["Data"]["kismet_device_base_channel"] , 
            "commonname" : mac["Data"]["kismet_device_base_commonname"],
            "encrypt" : mac["Data"]["kismet_device_base_crypt"] , 
            "lastseen" : mac["Data"]["kismet_device_base_last_time"] , 
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
