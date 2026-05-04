from roomba import Roomba
from chargingStation import ChargingStation

def is_Roomba(object):
    if isinstance(object, Roomba):
        return True
    return False

def is_Charging(object):
    if isinstance(object, ChargingStation):
        return True
    return False