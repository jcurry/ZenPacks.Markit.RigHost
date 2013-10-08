#!/usr/bin/env python
# Author:		Jane Curry
# Date			Sept 24th 20123
# Description:		Get all devices with the custom property cRigHost
#                       cRigHost is a list
#                       Output to $ZENHOME/local/cRigHost.out
# Parameters:		
# Updates:		
#
import os
import time
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
zenhome = os.environ['ZENHOME']

outputFile = zenhome + '/local/cRigHost.out'

of = open(outputFile, "w")
localtime = time.asctime( time.localtime(time.time()) )
of.write(localtime + "\n\n")

# Need noopts=True or it barfs with the script options
dmd = ZenScriptBase(connect=True, noopts=True).dmd

deviceList=[]
for dev in dmd.Devices.getSubDevices():
    if dev.cRigHost:
      deviceList.append((dev.id, dev.cRigHost))
#Sort the device on id
deviceList.sort()

for dev, rigHost in deviceList:
    print ('Device %s has rig host(s) %s ' % (dev,rigHost))
    of.write('Device %s has rig host(s) %s \n' % (dev,rigHost))
of.close()

