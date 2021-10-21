import lib.targetclassifier as tc
import json

def v2vsafetywarnings(hv_lat,hv_lon,hv_heading,hv_speed,hvppr,rv_lat,rv_lon,rv_heading,rv_speed):
    # intializing Json
    warnings = {}
    warnings['FCW']="Not Implemented"
    warnings['EEBL']="Not Implemented"
    warnings['IMA']="Not Implemented"
    warnings['DNPW']="Not Implemented"
    warnings['BSW']="Not Implemented"
    warnings['LCW']="Not Implemented"
    warnings['LTA']="Not Implemented"
    warnings['CLW']="Not Implemented"
    
    # Forward Collision Warning (FCW)
    # start of Application
    fcw_warning = "FALSE"
    k_ttc_thres=4
    rv_zone=tc.rv_zone_classification(hv_lat,hv_lon,hvppr,hv_heading,rv_lat,rv_lon)
    rv_direction=tc.rv_direction(hv_lat,hv_lon,hv_heading,hvppr,rv_lat,rv_lon,rv_heading)
    longitudinal_offset=tc.lon_offset(hv_lat,hv_lon,hvppr,hv_heading,rv_lat,rv_lon)
    if rv_zone=="Ahead" and rv_direction=="Equidirectional":
        if hv_speed>rv_speed:
            ttc= ((longitudinal_offset/1000)/(hv_speed-rv_speed))*3600
            if ttc < k_ttc_thres:
                fcw_warning = "Forward Collision Warning"
    # end of Application
    # construct json message
    warnings['FCW']=fcw_warning
    warningsJson = json.dumps(warnings)
    return warningsJson
    
