import json
from os import sep
import threading
import lib.geohashfunctionv1 as hashresolver
import time
import boto3
import geopy
from geopy import distance
import lib.heading as heading
from lib.AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import socket
import lib.targetclassifier as tc
import lib.v2vsafetyapplications as v2vapp
import queue


mypayload={}
mypayload['heading']=''
mqttconnect='disconnected'
hvppr=36767

port1 = 60001                   # Reserve a port for your service.
s1 = socket.socket()             # Create a socket object
host1 = socket.gethostname()     # Get local machine name
s1.bind((host1, port1))            # Bind to the port
s1.listen(5)                     # Now wait for client connection.

conn1, addr1 = s1.accept()     # Establish connection with client.

print('distance','bearing','latency','ttc[sec]','hvspeed','rvspeed','rv_zone','rv_direction','longitudinal_offset','warning',sep='\t')
def customCallback(client, userdata, message):
    messageJson = json.loads(message.payload)
    q=queue.Queue()
    #print(message.topic)
    #print(messageJson)
    
       
    try:
        pointA = geopy.Point(latitude=messageJson['lat'], longitude=messageJson['lon'])
        pointB = geopy.Point(latitude=mypayload['lat'], longitude=mypayload['lon'])
        mydistance = round(distance.distance(pointA,pointB).meters,1)
        bearing = round(heading.get_heading(mypayload['lat'], mypayload['lon'],messageJson['lat'], messageJson['lon']),1)
        latency = round((time.time()*1000) - messageJson['txtime'],1)
        ttc = round(((mydistance/1000)/abs(mypayload['speed']-messageJson['speed']))*3600,1)
        rv_zone=tc.rv_zone_classification(float(mypayload['lat']),float(mypayload['lon']),hvppr,float(mypayload['heading']),float(messageJson['lat']),float(messageJson['lon']))
        rv_direction=tc.rv_direction(float(mypayload['lat']),float(mypayload['lon']),float(mypayload['heading']),hvppr,float(messageJson['lat']),float(messageJson['lon']),float(messageJson['heading']))
        longitudinal_offset=round(tc.lon_offset(float(mypayload['lat']),float(mypayload['lon']),hvppr,float(mypayload['heading']),float(messageJson['lat']),float(messageJson['lon'])),1)
        mywarning=json.loads(v2vapp.v2vsafetywarnings(float(mypayload['lat']),float(mypayload['lon']),float(mypayload['heading']),float(mypayload['speed']),hvppr,float(messageJson['lat']),float(messageJson['lon']),float(messageJson['heading']),float(messageJson['speed'])))
        print(mydistance,bearing,latency,ttc,mypayload['speed'],messageJson['speed'],rv_zone,rv_direction,longitudinal_offset,mywarning['FCW'],sep='\t')
        mydashboard={}
        mydashboard['distance']=mydistance
        mydashboard['latency']=latency
        mydashboard['zone']=rv_zone
        mydashboard['warning']=mywarning
        mydashboard['ttc']=ttc
        mydashboard['status']=mqttconnect
        mydashboard['rv_direction']=rv_direction
        y = json.dumps(mydashboard)
        conn1.send(str.encode(y))
    except:     
        print("N/A")
    
    

def mygps(data,firstpoint,mypayload):
    fieldlist=data.split(",")
    mytime = fieldlist[1]
    mylat = fieldlist[2]
    mylatheading = fieldlist[3]
    mylon = fieldlist[4]
    mylonheading = fieldlist[5]

    mylatdecimal = str(mylat.split(".")[0][:2]) + "." + str(int(int(mylat.split(".")[0][2:]+mylat.split(".")[1])/60))
    mylondecimal = str(mylon.split(".")[0][:3]) + "." + str(int(int(mylon.split(".")[0][3:]+mylon.split(".")[1])/60))

    myhashcode = hashresolver.hashcode(mylatdecimal,mylondecimal)

    if (firstpoint == 0):
        pointA = geopy.Point(latitude=mypayload['lat'], longitude=mypayload['lon'])
        pointB = geopy.Point(latitude=mylatdecimal, longitude=mylondecimal)
        mydistance = distance.distance(pointA,pointB).meters
        mytimedelta = float(mytime) - float(mypayload['timestamp'])
        myspeed = round((mydistance/1000) / (mytimedelta/(3600)),2)
        myheading = round(heading.get_heading(mypayload['lat'], mypayload['lon'],mylatdecimal, mylondecimal),2)
        mypayload={}
        mypayload['timestamp']=mytime
        mypayload['lat']=mylatdecimal
        mypayload['lon']=mylondecimal
        mypayload['heading']=myheading
        mypayload['speed']=myspeed
        mypayload['clientid']= 'TestVehicle A'
        mypayload['hashcode']=myhashcode
        
    if (firstpoint == 1):
        topic = 'hashcode/' + myhashcode
        host = 'ajmnv0gantn3q-ats.iot.me-south-1.amazonaws.com'
        port = 8883
        rootCAPath = './lib/AmazonRootCA1.pem'
        certificatePath = './lib/a142f33636bb3eca7cb173d14dc451c7e4dd8f87d4fd7d604ad857b5fab6d3bd-certificate.pem.crt'
        privateKeyPath = './lib/a142f33636bb3eca7cb173d14dc451c7e4dd8f87d4fd7d604ad857b5fab6d3bd-private.pem.key'
        clientId = 'basicPubSub'
        myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
        myAWSIoTMQTTClient.configureEndpoint(host, port)
        myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
        myAWSIoTMQTTClient.connect()
        myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
        mypayload={}
        mypayload['timestamp']=mytime
        mypayload['lat']=mylatdecimal
        mypayload['lon']=mylondecimal
        global mqttconnect
        mqttconnect='Connected'

    
    firstpoint=0
    return mypayload,firstpoint

s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
port = 60000                    # Reserve a port for your service.

s.connect((host, port))

firstpoint=1
myrecordedtime =time.time()*1000
while True:
    data = str(s.recv(1024))
    #print('data=%s', (data))
    #print('reading NEMA point interval : ',round(time.time()*1000 - myrecordedtime,1))
    myrecordedtime=time.time()*1000
    mypayload , firstpoint = mygps(data,firstpoint,mypayload)
    if len(data)<4:
        break
print('Successfully get the file')
s.close()
print('connection closed')



