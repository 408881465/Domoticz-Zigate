#!/usr/bin/env python3
# coding: utf-8 -*-
#
# Author: zaraki673 & pipiche38
#
"""
    Module: z_domoticz.py
    Description: All interactions with Domoticz database
"""

import Domoticz
import binascii
import time
import struct
import json

import z_consts


def CreateDomoDevice(self, Devices, NWKID):
    """
    CreateDomoDevice

    Create Domoticz Device accordingly to the Type.

    """

    def getCreatedID(self, Devices, DeviceID, Name):
        """
        getCreateID
        Return DeviceID of the recently created device based  on its creation name.
        """
        # for x in Devices :
        #    if Devices[x].DeviceID == DeviceID and Devices[x].Name.find(Name) >= 0 :
        #        return Devices[x].ID
        return (Devices[x].ID for x in Devices if (Devices[x].DeviceID == DeviceID and Devices[x].Name.find(Name) >= 0))

    def FreeUnit(self, Devices):
        '''
        FreeUnit
        Look for a Free Unit number.
        '''
        FreeUnit = ""
        for x in range(1, 255):
            if x not in Devices:
                Domoticz.Debug("FreeUnit - device " + str(x) + " available")
                return x
        else:
            Domoticz.Debug("FreeUnit - device " + str(len(Devices) + 1))
            return len(Devices) + 1

    # Sanity check before starting the processing 
    if NWKID == '' or NWKID not in self.ListOfDevices:
        Domoticz.Error("CreateDomoDevice - Cannot create a Device without an IEEE or not in ListOfDevice .")
        return

    DeviceID_IEEE = self.ListOfDevices[NWKID]['IEEE']

    # When Type is at Global level, then we create all Type against the 1st EP
    # If Type needs to be associated to EP, then it must be at EP level and nothing at Global level
    GlobalEP = False
    for Ep in self.ListOfDevices[NWKID]['Ep']:
        dType = aType = Type = ''
        # Use 'type' at level EndPoint if existe
        Domoticz.Debug("CreatDomoDevice - Process EP : " + str(Ep))
        if not GlobalEP:  # First time, or we dont't GlobalType
            if 'Type' in self.ListOfDevices[NWKID]['Ep'][Ep]:
                if self.ListOfDevices[NWKID]['Ep'][Ep]['Type'] != "":
                    dType = self.ListOfDevices[NWKID]['Ep'][Ep]['Type']
                    aType = str(dType)
                    Type = aType.split("/")
                    Domoticz.Debug("CreateDomoDevice - Type via ListOfDevice: " + str(Type) + " Ep : " + str(Ep))
            else:
                if self.ListOfDevices[NWKID]['Type'] == {} or self.ListOfDevices[NWKID]['Type'] == '':
                    Type = GetType(self, NWKID, Ep).split("/")
                    Domoticz.Debug("CreateDomoDevice - Type via GetType: " + str(Type) + " Ep : " + str(Ep))
                else:
                    GlobalEP = True
                    if 'Type' in self.ListOfDevices[NWKID]:
                        if self.ListOfDevices[NWKID]['Type'] != '':
                            Type = self.ListOfDevices[NWKID]['Type'].split("/")
                            Domoticz.Debug("CreateDomoDevice - Type : '" + str(Type) + "'")
        else:
            break  # We have created already the Devices (as GlobalEP is set)

        # Check if Type is known
        if Type == '':
            continue

        Domoticz.Debug("CreateDomoDevice - Creating devices based on Type: %s" % Type)

        if 'ClusterType' not in self.ListOfDevices[NWKID]['Ep'][Ep]:
            self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'] = {}

        if "Humi" in Type and "Temp" in Type and "Baro" in Type:
            t = "Temp+Hum+Baro"  # Detecteur temp + Hum + Baro
            unit = FreeUnit(self, Devices)
            Domoticz.Debug("CreateDomoDevice - unit: %s" %unit)
            myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                            Unit=unit, TypeName=t)
            myDev.Create()
            ID = myDev.ID
            if myDev.ID == -1 :
                Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
            else:
                self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

        if "Humi" in Type and "Temp" in Type:
            t = "Temp+Hum"
            unit = FreeUnit(self, Devices)
            myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                            Unit=unit, TypeName=t)
            myDev.Create()
            ID = myDev.ID
            if myDev.ID == -1 :
                Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
            else:
                self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

        if self.ListOfDevices[NWKID]['Model'] == {} or \
                self.ListOfDevices[NWKID][ 'Model'] not in self.DeviceConf:    # If Model is known, then Type must be set correctly
            if ("Switch" in Type) and ("LvlControl" in Type) and ("ColorControl" in Type):
                Type = ['ColorControl']
            elif ("Switch" in Type) and ("LvlControl" in Type):
                Type = ['LvlControl']

        for t in Type:
            Domoticz.Debug(
                "CreateDomoDevice - Device ID : " + str(DeviceID_IEEE) + " Device EP : " + str(Ep) + " Type : " + str(
                    t))
            if t == "Temp":  # Detecteur temp
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, TypeName="Temperature")
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Humi":  # Detecteur hum
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, TypeName="Humidity")
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Baro":  # Detecteur Baro
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, TypeName="Barometer")
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Door":  # capteur ouverture/fermeture xiaomi
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=73, Switchtype=11)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Motion":  # detecteur de presence
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=73, Switchtype=8)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "SwitchAQ2":  # interrupteur multi lvl lumi.sensor_switch.aq2
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                Options = {"LevelActions": "|||", "LevelNames": "1 Click|2 Click|3 Click|4 Click",
                           "LevelOffHidden": "false", "SelectorStyle": "0"}
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=62, Switchtype=18, Options=Options)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "DSwitch":  # interrupteur double sur EP different
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                Options = {"LevelActions": "|||", "LevelNames": "Off|Left Click|Right Click|Both Click",
                           "LevelOffHidden": "true", "SelectorStyle": "0"}
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=62, Switchtype=18, Options=Options)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "DButton":  # interrupteur double sur EP different lumi.sensor_86sw2
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                Options = {"LevelActions": "|||", "LevelNames": "Off|Switch 1|Switch 2|Both_Click",
                           "LevelOffHidden": "true", "SelectorStyle": "1"}
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=62, Switchtype=18, Options=Options)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Smoke":  # detecteur de fumee
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=73, Switchtype=5)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Lux":  # Lux sensors
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=246, Subtype=1, Switchtype=0)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Switch":  # inter sans fils 1 touche 86sw1 xiaomi
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=73, Switchtype=0)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Button":  # inter sans fils 1 touche 86sw1 xiaomi
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=73, Switchtype=9)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Aqara" or t == "XCube":  # Xiaomi Magic Cube
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                Options = {"LevelActions": "|||||||||",
                           "LevelNames": "Off|Shake|Wakeup|Drop|90°|180°|Push|Tap|Rotation",
                           "LevelOffHidden": "true", "SelectorStyle": "0"}
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=62, Switchtype=18, Options=Options)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Vibration":  # Aqara Vibration Sensor v1
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                Options = {"LevelActions": "|||", "LevelNames": "Off|Tilt|Vibrate|Free Fall", \
                           "LevelOffHidden": "false", "SelectorStyle": "0"}
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep), \
                                Unit=unit, Type=244, Subtype=62, Switchtype=18, Options=Options)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Water":  # detecteur d'eau
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=73, Switchtype=0, Image=11)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Plug":  # prise pilote
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=73, Switchtype=0, Image=1)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "LvlControl" and self.ListOfDevices[NWKID][
                'Model'] == "shutter.Profalux":  # Volet Roulant / Shutter / Blinds, let's created blindspercentageinverted devic
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=73, Switchtype=16)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "LvlControl" and self.ListOfDevices[NWKID][
                'Model'] != "shutter.Profalux":  # variateur de luminosite + On/off
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=244, Subtype=73, Switchtype=7)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "ColorControl":  # variateur de couleur/luminosite/on-off
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                # Type 0xF1    pTypeColorSwitch
                # Switchtype 7 STYPE_Dimmer
                # SubType sTypeColor_RGB_W                0x01 // RGB + white, either RGB or white can be lit
                # SubType sTypeColor_White                0x03 // Monochrome white
                # SubType sTypeColor_RGB_CW_WW            0x04 // RGB + cold white + warm white, either RGB or white can be lit
                # SubType sTypeColor_LivCol               0x05
                # SubType sTypeColor_RGB_W_Z              0x06 // Like RGBW, but allows combining RGB and white
                # The test should be done in an other way ( ProfileID for instance )

                # default: SubType sTypeColor_RGB_CW_WW_Z 0x07 // Like RGBWW, # but allows combining RGB and white
                Subtype_ = 7


                if 'ColorInfos' in  self.ListOfDevices[NWKID]:
                    Domoticz.Debug("ColorInfos: %s" %self.ListOfDevices[NWKID]['ColorInfos'])
                    if 'ColorMode' in self.ListOfDevices[NWKID]['ColorInfos']:
                        Domoticz.Debug("ColorMode: %s" %self.ListOfDevices[NWKID]['ColorInfos']['ColorMode'])
                        if self.ListOfDevices[NWKID]['ColorInfos']['ColorMode'] == 2:
                            if 'ZDeviceID' in self.ListOfDevices[NWKID]:
                                if  self.ListOfDevices[NWKID]['ZDeviceID'] == "0210":
                                    #// RGB + cold white + warm white, either RGB or white can be lit
                                    Subtype_ = 4
                                elif self.ListOfDevices[NWKID]['ZDeviceID'] == "0200":
                                    Subtype_ = 7
                                else:
                                    # SubType sTypeColor_CW_WW       0x08 // Cold white + Warm white
                                    Subtype_ = 8        # "Ampoule.LED1545G12.Tradfri":
                        elif  self.ListOfDevices[NWKID]['ColorInfos']['ColorMode'] == 1:
                                                # SubType sTypeColor_RGB         0x02 // RGB
                            Subtype_ = 2        # "Ampoule.LED1624G9.Tradfri":


                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, Type=241, Subtype=Subtype_, Switchtype=7)
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            # Ajout meter
            if t == "Power":  # Will display Watt real time
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, TypeName="Usage")
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Meter":  # Will display kWh
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, TypeName="kWh")
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t

            if t == "Voltage":  # Will display kWh
                self.ListOfDevices[NWKID]['Status'] = "inDB"
                unit = FreeUnit(self, Devices)
                myDev = Domoticz.Device(DeviceID=str(DeviceID_IEEE), Name=str(t) + "-" + str(DeviceID_IEEE) + "-" + str(Ep),
                                Unit=unit, TypeName="Voltage")
                myDev.Create()
                ID = myDev.ID
                if myDev.ID == -1 :
                    Domoticz.Error("Domoticz widget creation failed. %s" %(str(myDev)))
                else:
                    self.ListOfDevices[NWKID]['Ep'][Ep]['ClusterType'][str(ID)] = t


def MajDomoDevice(self, Devices, NWKID, Ep, clusterID, value, Color_=''):
    '''
    MajDomoDevice
    Update domoticz device accordingly to Type found in EP and value/Color provided
    '''

    DeviceID_IEEE = self.ListOfDevices[NWKID]['IEEE']
    Domoticz.Debug(
        "MajDomoDevice - Device ID : " + str(DeviceID_IEEE) + " - Device EP : " + str(Ep) + " - Type : " + str(
            clusterID) + " - Value : " + str(value) + " - Hue : " + str(Color_))

    ClusterType = TypeFromCluster(clusterID)
    Domoticz.Debug("MajDomoDevice - Type = " + str(ClusterType))

    x = 0
    for x in Devices:
        if Devices[x].DeviceID == DeviceID_IEEE:
            Domoticz.Debug("MajDomoDevice - NWKID = " + str(NWKID) + " IEEE = " + str(DeviceID_IEEE) + " Unit = " + str(
                Devices[x].ID))

            ID = Devices[x].ID
            DeviceType = ""
            Domoticz.Debug("MajDomoDevice - " + str(self.ListOfDevices[NWKID]['Ep'][Ep]))

            if 'ClusterType' in self.ListOfDevices[NWKID]:
                # We are in the old fasho V. 3.0.x Where ClusterType has been migrated from Domoticz
                Domoticz.Debug("MajDomoDevice - search ClusterType in : " + str(
                    self.ListOfDevices[NWKID]['ClusterType']) + " for : " + str(ID))
                DeviceType = self.ListOfDevices[NWKID]['ClusterType'][str(ID)]
            else:
                # Are we in a situation with one Devices whatever Eps are ?
                # To do that, check there is only 1 ClusterType even if several EPs
                nbClusterType = 0
                ptEP = Ep
                for tmpEp in self.ListOfDevices[NWKID]['Ep']:
                    if 'ClusterType' in self.ListOfDevices[NWKID]['Ep'][tmpEp]:
                        nbClusterType = nbClusterType + 1
                        ptEP_single = tmpEp

                Domoticz.Debug("MajDomoDevice - We have " + str(nbClusterType) + " EPs with ClusterType")

                if nbClusterType == 1:  # All Updates are redirected to the same EP
                    # We must redirect all to the EP where there is a ClusterType
                    # ptEP_single is be the Only  EP where we have found ClusterType
                    for key in self.ListOfDevices[NWKID]['Ep'][ptEP_single]['ClusterType']:
                        if str(ID) == str(key):
                            DeviceType = str(self.ListOfDevices[NWKID]['Ep'][ptEP_single]['ClusterType'][key])

                else:
                    ptEp_multi = Ep
                    Domoticz.Debug("MajDomoDevice - search ClusterType in : " + str(
                        self.ListOfDevices[NWKID]['Ep'][ptEp_multi]) + " for : " + str(ID))
                    if 'ClusterType' in self.ListOfDevices[NWKID]['Ep'][ptEp_multi]:
                        Domoticz.Debug("MajDomoDevice - search ClusterType in : " + str(
                            self.ListOfDevices[NWKID]['Ep'][ptEp_multi]['ClusterType']) + " for : " + str(ID))
                        for key in self.ListOfDevices[NWKID]['Ep'][ptEp_multi]['ClusterType']:
                            if str(ID) == str(key):
                                DeviceType = str(self.ListOfDevices[NWKID]['Ep'][ptEp_multi]['ClusterType'][key])
                    else:
                        Domoticz.Debug("MajDomoDevice - receive an update on an Ep which doesn't have any ClusterType !")
                        Domoticz.Debug("MajDomoDevice - Network Id : " + NWKID + " Ep : " + str(
                            ptEp_multi) + " Expected Cluster is " + str(clusterID))
                        continue
            if DeviceType == "":  # No match with ClusterType
                continue

            Domoticz.Debug("MajDomoDevice - NWKID: %s SwitchType: %s, DeviceType: %s, ClusterType: %s, old_nVal: %s , old_sVal: %s" \
                         % (NWKID, Devices[x].SwitchType, DeviceType, ClusterType, Devices[x].nValue, Devices[x].sValue))

            if self.ListOfDevices[NWKID]['RSSI'] != 0:
                SignalLevel = self.ListOfDevices[NWKID]['RSSI']
            else:
                SignalLevel = 15
            if self.ListOfDevices[NWKID]['Battery'] != '':
                BatteryLevel = self.ListOfDevices[NWKID]['Battery']
            else:
                BatteryLevel = 255

            # Instant Watts. 
            # PowerMeter is for Compatibility , as it was created as a PowerMeter device.
            # if ( DeviceType=="Power" or DeviceType=="PowerMeter") and clusterID == "000c":
            if ('Power' in ClusterType and DeviceType == "Power") or \
                    (clusterID == "000c" and DeviceType == "Power"):  # kWh
                nValue = float(value)
                sValue = value
                Domoticz.Debug("MajDomoDevice Power : " + sValue)
                UpdateDevice_v2(Devices, x, nValue, str(sValue), BatteryLevel, SignalLevel)

                # if DeviceType=="Meter" and clusterID == "000c": # kWh
            if ('Meter' in ClusterType and DeviceType == "Meter") or \
                    (clusterID == "000c" and DeviceType == "Power"):  # kWh
                nValue = float(value)
                sValue = "%s;%s" % (nValue, nValue)
                Domoticz.Debug("MajDomoDevice Meter : " + sValue)
                UpdateDevice_v2(Devices, x, 0, sValue, BatteryLevel, SignalLevel)

            if ClusterType == DeviceType == "Voltage":  # Volts
                nValue = float(value)
                sValue = "%s;%s" % (nValue, nValue)
                Domoticz.Debug("MajDomoDevice Voltage : " + sValue)
                UpdateDevice_v2(Devices, x, 0, sValue, BatteryLevel, SignalLevel)

            if ClusterType == "Temp":  # temperature
                CurrentnValue = Devices[x].nValue
                CurrentsValue = Devices[x].sValue
                if CurrentsValue == '':
                    # First time after device creation
                    CurrentsValue = "0;0;0;0;0"
                SplitData = CurrentsValue.split(";")
                NewNvalue = 0
                NewSvalue = ''
                if DeviceType == "Temp":
                    NewNvalue = value
                    NewSvalue = str(value)
                    UpdateDevice_v2(Devices, x, NewNvalue, str(NewSvalue), BatteryLevel, SignalLevel)

                elif DeviceType == "Temp+Hum":
                    NewNvalue = 0
                    NewSvalue = '%s;%s;%s' % (value, SplitData[1], SplitData[2])
                    UpdateDevice_v2(Devices, x, NewNvalue, str(NewSvalue), BatteryLevel, SignalLevel)

                elif DeviceType == "Temp+Hum+Baro":  # temp+hum+Baro xiaomi
                    NewNvalue = 0
                    NewSvalue = '%s;%s;%s;%s;%s' % (value, SplitData[1], SplitData[2], SplitData[3], SplitData[4])
                    UpdateDevice_v2(Devices, x, NewNvalue, str(NewSvalue), BatteryLevel, SignalLevel)

            if ClusterType == "Humi":  # humidite
                CurrentnValue = Devices[x].nValue
                CurrentsValue = Devices[x].sValue
                if CurrentsValue == '':
                    # First time after device creation
                    CurrentsValue = "0;0;0;0;0"
                SplitData = CurrentsValue.split(";")
                NewNvalue = 0
                NewSvalue = ''
                # Humidity Status
                if value < 40:
                    humiStatus = 2
                elif 40 <= value < 70:
                    humiStatus = 1
                else:
                    humiStatus = 3

                if DeviceType == "Humi":
                    NewNvalue = value
                    NewSvalue = "0"
                    UpdateDevice_v2(Devices, x, NewNvalue, str(NewSvalue), BatteryLevel, SignalLevel)

                elif DeviceType == "Temp+Hum":  # temp+hum xiaomi
                    NewNvalue = 0
                    NewSvalue = '%s;%s;%s' % (SplitData[0], value, humiStatus)
                    UpdateDevice_v2(Devices, x, NewNvalue, str(NewSvalue), BatteryLevel, SignalLevel)

                elif DeviceType == "Temp+Hum+Baro":  # temp+hum+Baro xiaomi
                    NewNvalue = 0
                    NewSvalue = '%s;%s;%s;%s;%s' % (SplitData[0], value, humiStatus, SplitData[3], SplitData[4])
                    UpdateDevice_v2(Devices, x, NewNvalue, str(NewSvalue), BatteryLevel, SignalLevel)

            if ClusterType == "Baro":  # barometre
                CurrentnValue = Devices[x].nValue
                CurrentsValue = Devices[x].sValue
                if CurrentsValue == '':
                    # First time after device creation
                    CurrentsValue = "0;0;0;0;0"
                SplitData = CurrentsValue.split(";")
                NewNvalue = 0
                NewSvalue = ''

                if value < 1000:
                    Bar_forecast = 4
                elif value < 1020:
                    Bar_forecast = 3
                elif value < 1030:
                    Bar_forecast = 2
                else:
                    Bar_forecast = 1

                if DeviceType == "Baro":
                    NewSvalue = '%s;%s' % (value, Bar_forecast)
                    UpdateDevice_v2(Devices, x, NewNvalue, str(NewSvalue), BatteryLevel, SignalLevel)

                elif DeviceType == "Temp+Hum+Baro":
                    NewSvalue = '%s;%s;%s;%s;%s' % (SplitData[0], SplitData[1], SplitData[2], value, Bar_forecast)
                    UpdateDevice_v2(Devices, x, NewNvalue, str(NewSvalue), BatteryLevel, SignalLevel)

            if ClusterType == "Door" and DeviceType == "Door":  # Door / Window
                if value == "01":
                    state = "Open"
                    UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel)
                elif value == "00":
                    state = "Closed"
                    UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel)

            if ClusterType == "Switch":
                if DeviceType == "Plug":
                    if value == "01":
                        UpdateDevice_v2(Devices, x, 1, "On", BatteryLevel, SignalLevel)
                    elif value == "00":
                        state = "Off"
                        UpdateDevice_v2(Devices, x, 0, "Off", BatteryLevel, SignalLevel)
                elif DeviceType == "Door":  # porte / fenetre
                    if value == "01":
                        state = "Open"
                        UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel)
                    elif value == "00":
                        state = "Closed"
                        UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel)
                elif DeviceType == "Switch":  # Switch
                    state = ''
                    if value == "01":
                        state = "On"
                    elif value == "00":
                        state = "Off"
                    UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel)
                elif DeviceType == "Button":  # boutton simple
                    state = ''
                    if int(value) == 1:
                        state = "On"
                        UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel,
                                        ForceUpdate_=True)
                elif DeviceType == "Water":  # detecteur d eau
                    state = ''
                    if value == "01":
                        state = "On"
                        UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel)
                    elif value == "00":
                        state = "Off"
                        UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel)
                elif DeviceType == "Smoke":  # detecteur de fume
                    state = ''
                    if value == "01":
                        state = "On"
                        UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel)
                    elif value == "00":
                        state = "Off"
                        UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel)
                elif DeviceType == "SwitchAQ2":  # multi lvl switch
                    if value in ( '1', '01'):
                        state = "00"
                    elif value in ( '2', '02'):
                        state = "10"
                    elif value in ( '3', '03'):
                        state = "20"
                    elif value in ( '4', '04'):
                        state = "30"
                    else:
                        return  # Simply return and don't process any other values than the above
                    UpdateDevice_v2(Devices, x, int(value), str(state), BatteryLevel, SignalLevel, ForceUpdate_=True)
                elif DeviceType == "DSwitch":
                    # double switch avec EP different 
                    if Ep == "01":
                        if value in ( '1', '0', "01", "00"):
                            state = "10"
                            data = "01"
                            UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel)
                    elif Ep == "02":
                        if value in ( '1', '0', "01", "00"):
                            state = "20"
                            data = "02"
                            UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel)
                    elif Ep == "03":
                        if value in ( '1', '0', "01" ,"00"):
                            state = "30"
                            data = "03"
                            UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel)
                elif DeviceType == "DButton":
                    # double bouttons avec EP different lumi.sensor_86sw2 
                    if Ep == "01":
                        if value in ( '1', '01'):
                            state = "10"
                            data = "01"
                            UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel,
                                            ForceUpdate_=True)
                        else:
                            return  # We just expect 01 , in case of other value nothing to do
                    elif Ep == "02":
                        if value in ( '1', '01'):
                            state = "20"
                            data = "02"
                            UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel,
                                            ForceUpdate_=True)
                        else:
                            return  # We just expect 01 , in case of other value nothing to do
                    elif Ep == "03":
                        if value in ( '1', '01'):
                            state = "30"
                            data = "03"
                            UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel,
                                            ForceUpdate_=True)
                        else:
                            return  # We just expect 01 , in case of other value nothing to do
                elif DeviceType == "LvlControl" or DeviceType == "ColorControl":
                    if Devices[x].SwitchType == 16:
                        if value == "00":
                            UpdateDevice_v2(Devices, x, 0, '0', BatteryLevel, SignalLevel)
                        else:
                            # We are in the case of a Shutter/Blind inverse. If we receieve a Read Attribute telling it is On, great
                            # We only update if the shutter was off before, otherwise we will keep its Level.
                            if Devices[x].nValue == 0 and Devices[x].sValue == 'Off':
                                UpdateDevice_v2(Devices, x, 1, '100', BatteryLevel, SignalLevel)
                    else:
                        if value == "00":
                            UpdateDevice_v2(Devices, x, 0, 'Off', BatteryLevel, SignalLevel)
                        else:
                            UpdateDevice_v2(Devices, x, 1, 'On', BatteryLevel, SignalLevel)

            elif ClusterType == "LvlControl":
                if DeviceType == "LvlControl":
                    # We need to handle the case, where we get an update from a Read Attribute or a Reporting message
                    # We might get a Level, but the device is still Off and we shouldn't make it On .

                    nValue = None
                    sValue = round((int(value, 16) / 255) * 100)
                    if sValue == 0:
                        nValue = 0
                        if Devices[x].SwitchType == 16:
                            UpdateDevice_v2(Devices, x, 0, '0', BatteryLevel, SignalLevel)
                        else:
                            if Devices[x].nValue == 0 and Devices[x].sValue == 'Off':
                                pass
                            else:
                                UpdateDevice_v2(Devices, x, 0, 'Off', BatteryLevel, SignalLevel)
                    elif sValue == 100:
                        nValue = 1
                        if Devices[x].SwitchType == 16:
                            UpdateDevice_v2(Devices, x, 1, '100', BatteryLevel, SignalLevel)
                        else:
                            if Devices[x].nValue == 0 and Devices[x].sValue == 'Off':
                                pass
                            else:
                                UpdateDevice_v2(Devices, x, 1, 'On', BatteryLevel, SignalLevel)
                    else:
                        if Devices[x].SwitchType != 16 and Devices[x].nValue == 0 and Devices[x].sValue == 'Off':
                            pass
                        else:
                            nValue = 2
                            UpdateDevice_v2(Devices, x, str(nValue), str(sValue), BatteryLevel, SignalLevel)

                elif DeviceType == "ColorControl":
                    if Devices[x].nValue == 0 and Devices[x].sValue == 'Off':
                        pass
                    else:
                        nValue = 1
                        sValue = round((int(value, 16) / 255) * 100)
                        UpdateDevice_v2(Devices, x, str(nValue), str(sValue), BatteryLevel, SignalLevel, Color_)

            if ClusterType == DeviceType == "ColorControl":
                nValue = 1
                sValue = round((int(value, 16) / 255) * 100)
                UpdateDevice_v2(Devices, x, str(nValue), str(sValue), BatteryLevel, SignalLevel, Color_)

            if ClusterType == "XCube" and DeviceType == "Aqara" and Ep == "02":  # Magic Cube Acara
                Domoticz.Debug("MajDomoDevice - XCube update device with data = " + str(value))
                UpdateDevice_v2(Devices, x, int(value), str(value), BatteryLevel, SignalLevel)

            if ClusterType == "XCube" and DeviceType == "Aqara" and Ep == "03":  # Magic Cube Acara Rotation
                Domoticz.Debug("MajDomoDevice - XCube update device with data = " + str(value))
                UpdateDevice_v2(Devices, x, int(value), str(value), BatteryLevel, SignalLevel)

            if ClusterType == DeviceType == "XCube" and Ep == "02":  # cube xiaomi
                if value == "0000":  # shake
                    state = "10"
                    data = "01"
                    UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel)
                elif value == "0204" or value == "0200" or value == "0203" or value == "0201" or value == "0202" or value == "0205":  # tap
                    state = "50"
                    data = "05"
                    UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel)
                elif value == "0103" or value == "0100" or value == "0104" or value == "0101" or value == "0102" or value == "0105":  # Slide
                    state = "20"
                    data = "02"
                    UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel)
                elif value == "0003":  # Free Fall
                    state = "70"
                    data = "07"
                    UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel)
                elif "0004" <= value <= "0059":  # 90°
                    state = "30"
                    data = "03"
                    UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel)
                elif value >= "0060":  # 180°
                    state = "90"
                    data = "09"
                    UpdateDevice_v2(Devices, x, int(data), str(state), BatteryLevel, SignalLevel)

            if ClusterType == DeviceType == "Lux":
                UpdateDevice_v2(Devices, x, int(value), str(value), BatteryLevel, SignalLevel)

            if ClusterType == DeviceType == "Motion":
                if value == "01":
                    UpdateDevice_v2(Devices, x, "1", str("On"), BatteryLevel, SignalLevel)
                if value == "00":
                    UpdateDevice_v2(Devices, x, "0", str("Off"), BatteryLevel, SignalLevel)


def ResetDevice(self, Devices, ClusterType, HbCount):
    '''
        Reset all Devices from the ClusterType Motion after 30s
    '''

    x = 0
    for x in Devices:
        if Devices[x].nValue == 0 and Devices[x].sValue == "Off":
            # No need to spend time as it is already in the state we want, go to next device
            continue

        LUpdate = Devices[x].LastUpdate
        _tmpDeviceID_IEEE = Devices[x].DeviceID
        LUpdate = time.mktime(time.strptime(LUpdate, "%Y-%m-%d %H:%M:%S"))
        current = time.time()
        # Look for the corresponding ClusterType
        if _tmpDeviceID_IEEE in self.IEEE2NWK:
            NWKID = self.IEEE2NWK[_tmpDeviceID_IEEE]

            if NWKID not in self.ListOfDevices:
                Domoticz.Error("ResetDevice " + str(NWKID) + " not found in " + str(self.ListOfDevices))
                continue

            ID = Devices[x].ID
            DeviceType = ''
            for tmpEp in self.ListOfDevices[NWKID]['Ep']:
                if 'ClusterType' in self.ListOfDevices[NWKID]['Ep'][tmpEp]:
                    if str(ID) in self.ListOfDevices[NWKID]['Ep'][tmpEp]['ClusterType']:
                        DeviceType = self.ListOfDevices[NWKID]['Ep'][tmpEp]['ClusterType'][str(ID)]
            if DeviceType == '':
                if 'ClusterType' in self.ListOfDevices[NWKID]:
                    if str(ID) in self.ListOfDevices[NWKID]['ClusterType']:
                        DeviceType = self.ListOfDevices[NWKID]['ClusterType'][str(ID)]
            # Takes the opportunity to update RSSI and Battery
            SignalLevel = ''
            BatteryLevel = ''
            if self.ListOfDevices[NWKID].get('RSSI'):
                SignalLevel = self.ListOfDevices[NWKID]['RSSI']
            if self.ListOfDevices[NWKID].get('Battery'):
                BatteryLevel = self.ListOfDevices[NWKID]['Battery']

            if (current - LUpdate) > 30 and DeviceType == "Motion":
                Domoticz.Log("Last update of the devices " + str(x) + " was : " + str(LUpdate) + " current is : " + str(
                    current) + " this was : " + str(current - LUpdate) + " secondes ago")
                UpdateDevice_v2(Devices, x, 0, "Off", BatteryLevel, SignalLevel, SuppTrigger_=True)
    return


def UpdateDevice_v2(Devices, Unit, nValue, sValue, BatteryLvl, SignalLvl, Color_='', SuppTrigger_=False,
                    ForceUpdate_=False):
    Domoticz.Debug(
        "UpdateDevice_v2 for : " + str(Unit) + " Battery Level = " + str(BatteryLvl) + " Signal Level = " + str(
            SignalLvl))
    if isinstance(SignalLvl, int):
        rssi = round((SignalLvl * 12) / 255)
        Domoticz.Debug("UpdateDevice_v2 for : " + str(Unit) + " RSSI = " + str(rssi))
    else:
        rssi = 12

    if not isinstance(BatteryLvl, int) or BatteryLvl == '':
        BatteryLvl = 255

    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if (Unit in Devices):
        if (Devices[Unit].nValue != int(nValue)) or (Devices[Unit].sValue != sValue) or (
                Color_ !='' and Devices[Unit].Color != Color_) or ForceUpdate_:
            Domoticz.Log("Update v2 Values " + str(nValue) + ":'" + str(sValue) + ":" + str(Color_) + "' (" + Devices[
                Unit].Name + ")")
            if Color_:
                Devices[Unit].Update(nValue=int(nValue), sValue=str(sValue), Color=Color_, SignalLevel=int(rssi),
                                     BatteryLevel=int(BatteryLvl))
            else:
                # SO far, SuppressTrigger is not enforced due to the fact that Domoticz doesn't behave correctly.
                # Issue will be reported to Domoticz as if SuppressTriggers is set to True, then there is no update of the Database at all!
                # Devices[Unit].Update(nValue=int(nValue), sValue=str(sValue) , SignalLevel=int(rssi), BatteryLevel=int(BatteryLvl), SuppressTriggers=SuppTrigger_ )
                Devices[Unit].Update(nValue=int(nValue), sValue=str(sValue), SignalLevel=int(rssi),
                                     BatteryLevel=int(BatteryLvl))

        elif (Devices[Unit].BatteryLevel != BatteryLvl and BatteryLvl != 255) or (
                Devices[Unit].SignalLevel != rssi):  # In that case we do update, but do not trigger any notification.
            Devices[Unit].Update(nValue=int(nValue), sValue=str(sValue), SignalLevel=int(rssi),
                                 BatteryLevel=int(BatteryLvl), SuppressTriggers=True)
    return


def GetType(self, Addr, Ep):
    Type = ""
    Domoticz.Debug("GetType - Model " + str(self.ListOfDevices[Addr]['Model']) + " Profile ID : " + str(
        self.ListOfDevices[Addr]['ProfileID']) + " ZDeviceID : " + str(self.ListOfDevices[Addr]['ZDeviceID']))

    if self.ListOfDevices[Addr]['Model'] != {} and \
            self.ListOfDevices[Addr][ 'Model'] in self.DeviceConf and \
            Ep in self.DeviceConf[self.ListOfDevices[Addr]['Model']]['Ep']:  
        # verifie si le model a ete detecte et est connu dans le fichier DeviceConf.txt

        if 'Type' in self.DeviceConf[self.ListOfDevices[Addr]['Model']]['Ep'][Ep]:
            if self.DeviceConf[self.ListOfDevices[Addr]['Model']]['Ep'][Ep]['Type'] != "":
                Domoticz.Log("GetType - Found Type in DeviceConf : " + str(
                    self.DeviceConf[self.ListOfDevices[Addr]['Model']]['Ep'][Ep]['Type']))
                Type = self.DeviceConf[self.ListOfDevices[Addr]['Model']]['Ep'][Ep]['Type']
                Type = str(Type)
        else:
            Domoticz.Log("GetType - Found Type in DeviceConf : " + str(
                self.DeviceConf[self.ListOfDevices[Addr]['Model']]['Type']))
            Type = self.DeviceConf[self.ListOfDevices[Addr]['Model']]['Type']
    else:
        Domoticz.Debug("GetType - Model not found in DeviceConf : " + str(
            self.ListOfDevices[Addr]['Model']) + " Let's go for Cluster search")
        Type = ""
        for cluster in self.ListOfDevices[Addr]['Ep'][Ep]:
            Domoticz.Debug("GetType - check Type for Cluster : " + str(cluster))
            if Type != "" and Type[:1] != "/":
                Type += "/"
            Type += TypeFromCluster(cluster)
            Domoticz.Debug("GetType - Type will be set to : " + str(Type))

        # Type+=Type
        # Ne serait-il pas plus simple de faire un .split( '/' ), puis un join ('/')
        # car j'ai un peu de problème sur cette serie de replace. 
        # ensuite j'ai vu également des Type avec un / à la fin !!!!!
        # Par exemple :  'Type': 'Switch/LvlControl/',
        Type = Type.replace("/////", "/")
        Type = Type.replace("////", "/")
        Type = Type.replace("///", "/")
        Type = Type.replace("//", "/")
        if Type[:-1] == "/":
            Type = Type[:-1]
        if Type[0:] == "/":
            Type = Type[1:]
        if Type != "":
            self.ListOfDevices[Addr]['Type'] = Type
            Domoticz.Debug("GetType - Type is now set to : " + str(Type))
    return Type


def TypeFromCluster(cluster):
    if cluster == "0006":
        TypeFromCluster = "Switch"
    elif cluster == "0008":
        TypeFromCluster = "LvlControl"
    elif cluster == "000c":
        TypeFromCluster = "XCube"
    elif cluster == "0012":
        TypeFromCluster = "XCube"
    elif cluster == "0101":
        TypeFromCluster = "Vibration"
    elif cluster == "0300":
        TypeFromCluster = "ColorControl"
    elif cluster == "0400":
        TypeFromCluster = "Lux"
    elif cluster == "0402":
        TypeFromCluster = "Temp"
    elif cluster == "0403":
        TypeFromCluster = "Baro"
    elif cluster == "0405":
        TypeFromCluster = "Humi"
    elif cluster == "0406":
        TypeFromCluster = "Motion"
    elif cluster == "0702":
        TypeFromCluster = "Power/Meter"
    elif cluster == "0500":
        TypeFromCluster = "Door"
    elif cluster == "0001":
        TypeFromCluster = "Voltage"
    else:
        TypeFromCluster = ""
    return TypeFromCluster
