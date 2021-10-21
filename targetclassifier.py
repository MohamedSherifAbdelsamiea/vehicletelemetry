import geopy
from geopy import distance
import math, numpy as np
from math import pi
from lib.trianglesolver import solve, degree


def get_bearing(lat1,lon1,lat2,lon2):
    dLon = float(lon2) - float(lon1);
    y = math.sin(dLon) * math.cos(lat2);
    x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon);
    brng = np.rad2deg(math.atan2(y, x));
    if brng < 0: brng+= 360
    return brng

def get_hvppc(lat,lon,hvppr,heading):
    origin = geopy.Point(latitude=lat, longitude=lon)
    dist = geopy.distance.distance(meters=hvppr)
    dest_heading=heading+90
    if dest_heading > 360:
        dest_heading=dest_heading-360
    destination = dist.destination(origin, dest_heading)
    return destination.latitude, destination.longitude

def calcgpsdis(lat1,lon1,lat2,lon2):
    origin = geopy.Point(latitude=lat1, longitude=lon1)
    dest = geopy.Point(latitude=lat2, longitude=lon2)
    return distance.distance(origin,dest).meters
    
def hvppc_angle(hv_hvppc_dist,hvppc_rv_dist,hv_rv_dist):
    a,b,c,A,B,C = solve(a=hv_hvppc_dist, b=hvppc_rv_dist, c=hv_rv_dist)
    return C / degree

def lon_offset(hv_lat,hv_lon,hvppr,hv_heading,rv_lat,rv_lon):
    hvppc_lat,hvppc_lon=get_hvppc(hv_lat,hv_lon,hvppr,hv_heading)
    hv_hvppc_dist=calcgpsdis(hv_lat,hv_lon,hvppc_lat,hvppc_lon)
    hvppc_rv_dist=calcgpsdis(hvppc_lat,hvppc_lon,rv_lat,rv_lon)
    hv_rv_dist=calcgpsdis(hv_lat,hv_lon,rv_lat,rv_lon)
    myhvppc_angle=hvppc_angle(hv_hvppc_dist,hvppc_rv_dist,hv_rv_dist)
    pi=22/7
    arc_length = (pi*hv_hvppc_dist*2) * (myhvppc_angle/360)
    return arc_length

def lat_offset(lat,lon,hvppr,heading,rv_lat,rv_lon):
    hvppc_lat,hvppc_lon=get_hvppc(lat,lon,hvppr,heading)
    hvppc_rv_dist=calcgpsdis(hvppc_lat,hvppc_lon,rv_lat,rv_lon)
    return (hvppr-hvppc_rv_dist)
    

def convertLatLongToXY(hv_lat, hv_lon, rv_lat, rv_lon,hvppr,heading):
    pi=22/7
    hvppc_lat,hvppc_lon=get_hvppc(hv_lat,hv_lon,hvppr,heading)
    hvppc_rv_dist=calcgpsdis(hvppc_lat,hvppc_lon,rv_lat,rv_lon)
    hv_hvppc_dist=calcgpsdis(hv_lat,hv_lon,hvppc_lat,hvppc_lon)
    hv_rv_dist=calcgpsdis(hv_lat,hv_lon,rv_lat,rv_lon)
    C_angle=hvppc_angle(hv_hvppc_dist,hvppc_rv_dist,hv_rv_dist)
    x = math.sin((C_angle*pi)/180)*hvppc_rv_dist
    y= math.cos((C_angle*pi)/180)*hvppc_rv_dist
    hv_rv_bearing=get_bearing(hv_lat,hv_lon,rv_lat,rv_lon)
    check_orientation=hv_rv_bearing-heading
    if check_orientation > -90 and check_orientation < 90:
        rvRelX = x
    else:
        rvRelX = -x
    rvRelY=hv_hvppc_dist-y
    return rvRelX,rvRelY

def rv_zone_classification(hv_lat,hv_lon,hvppr,heading,rv_lat,rv_lon):
    lanewidth = 3.7
    rvRelX,rvRelY=convertLatLongToXY(hv_lat, hv_lon, rv_lat, rv_lon,hvppr,heading)
    lat_offset_tmp=lat_offset(hv_lat,hv_lon,hvppr,heading,rv_lat,rv_lon)
    zone=''
    if rvRelX > 0:
        if hvppr > 0:
            if lat_offset_tmp <= -2.5 * lanewidth:
                zone = "Ahead Far Far Left"
            elif (lat_offset_tmp > (-2.5 * lanewidth) and lat_offset_tmp <= (-1.5 * lanewidth)):
                zone = "Ahead Far Left"
            elif lat_offset_tmp > -1.5 * lanewidth and  lat_offset_tmp <= -0.5 * lanewidth:
                zone = "Ahead Left"
            elif lat_offset_tmp >= -0.5 * lanewidth and lat_offset_tmp <= 0.5 * lanewidth:
                zone = "Ahead"
            elif lat_offset_tmp >= 0.5 * lanewidth and lat_offset_tmp < 1.5 * lanewidth:
                zone = "Ahead Right"
            elif lat_offset_tmp >= 1.5 * lanewidth and lat_offset_tmp < 2.5 * lanewidth:
                zone = "Ahead Far Right"
            elif lat_offset_tmp >= 2.5 * lanewidth:
                zone = "Ahead Far Far Right"
        else:
            if lat_offset_tmp <= -2.5 * lanewidth:
                zone = "Ahead Far Far Right"
            elif lat_offset_tmp > -2.5 * lanewidth and lat_offset_tmp <= -1.5 * lanewidth:
                zone="Ahead Far Right"
            elif lat_offset_tmp > -1.5 * lanewidth and lat_offset_tmp <= -0.5 * lanewidth:
                zone = "Ahead Right"
            elif lat_offset_tmp >= -0.5 * lanewidth and lat_offset_tmp <= 0.5 * lanewidth:
                zone = "Ahead"
            elif lat_offset_tmp >= 0.5 * lanewidth and lat_offset_tmp < 1.5 * lanewidth:
                zone = "Ahead Left"
            elif lat_offset_tmp >= 1.5 * lanewidth and lat_offset_tmp < 2.5 * lanewidth:
                zone = "Ahead Far Left"
            elif lat_offset_tmp >= 2.5 * lanewidth:
                zone = "Ahead Far Far Left"
    else:
        if hvppr > 0:
            if lat_offset_tmp <= -2.5 * lanewidth:
                zone = "Behind Far Far Left"
            elif lat_offset_tmp > -2.5 * lanewidth and lat_offset_tmp <= -1.5 * lanewidth:
                zone = "Behind Far Left"
            elif lat_offset_tmp > -1.5 * lanewidth and lat_offset_tmp <= -0.5 * lanewidth:
                zone = "Behind Left"
            elif lat_offset_tmp >= -0.5 * lanewidth and lat_offset_tmp <= 0.5 * lanewidth:
                zone = "Behind"
            elif lat_offset_tmp >= 0.5 * lanewidth and lat_offset_tmp < 1.5 * lanewidth:
                zone = "Behind Right"
            elif lat_offset_tmp >= 1.5 * lanewidth and lat_offset_tmp < 2.5 * lanewidth:
                zone = "Behind Far Right"
            elif lat_offset_tmp >= 2.5 * lanewidth:
                zone = "Behind Far Far Right"
        else:
            if lat_offset_tmp <= -2.5 * lanewidth:
                zone = "Behind Far Far Right"
            elif lat_offset_tmp > -2.5 * lanewidth and lat_offset_tmp <= -1.5 * lanewidth:
                zone = "Behind Far Right"
            elif lat_offset_tmp > -1.5 * lanewidth and lat_offset_tmp <= -0.5 * lanewidth:
                zone = "Behind Right"
            elif lat_offset_tmp >= -0.5 * lanewidth and lat_offset_tmp <= 0.5 * lanewidth:
                zone = "Behind"
            elif lat_offset_tmp >= 0.5 * lanewidth and lat_offset_tmp < 1.5 * lanewidth:
                zone = "Behind Left"
            elif lat_offset_tmp >= 1.5 * lanewidth and lat_offset_tmp < 2.5 * lanewidth:
                zone = "Behind Far Left"
            elif lat_offset_tmp >= 2.5 * lanewidth:
                zone = "Behind Far Far Left"
    return zone

def rv_direction(hv_lat,hv_lon,hv_heading,hvppr,rv_lat,rv_lon,rv_heading):
    hvppc_lat,hvppc_lon=get_hvppc(hv_lat,hv_lon,hvppr,hv_heading)
    hv_hvppc_dist=calcgpsdis(hv_lat,hv_lon,hvppc_lat,hvppc_lon)
    hvppc_rv_dist=calcgpsdis(hvppc_lat,hvppc_lon,rv_lat,rv_lon)
    hv_rv_dist=calcgpsdis(hv_lat,hv_lon,rv_lat,rv_lon)
    alpha=hvppc_angle(hv_hvppc_dist,hvppc_rv_dist,hv_rv_dist)
    delta=hv_heading-rv_heading-alpha
    if delta >= -25 and delta <= 25:
        direction = "Equidirectional"
    elif delta > 25 and delta < 155:
        direction = "Intersecting right"
    elif (delta >= 155 and delta <= 180) or (delta >= -180 and delta <= -155):
        direction = "Reverse"
    elif delta > -155 and delta < -25:
        direction = "Intersecting left"
    return direction
                 
