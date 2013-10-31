#!/usr/bin/env python
# Author:		Jane Curry
# Date			Oct 31st 20123
# Description:		Get all devices under /Application device class that do not have a cRigHost custom property
#                       cRigHost is a list
#                       Output to $ZENHOME/local/appdev_no_cRigHost.out
# Parameters:		
# Updates:		
#
import os
import time
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
zenhome = os.environ['ZENHOME']

outputFile = zenhome + '/local/appdev_no_cRigHost.out'

of = open(outputFile, "w")
localtime = time.asctime( time.localtime(time.time()) )
of.write(localtime + "\n\n")
of.write('Devices under device class /Application that do NOT have a cRigHost custom property set \n\n ')

# Need noopts=True or it barfs with the script options
dmd = ZenScriptBase(connect=True, noopts=True).dmd

# need to check existence of cRigHost as it appears to default to the null string,
#      not an empty list

deviceList=[]
for dev in dmd.Devices.Application.getSubDevices():
    if not dev.cRigHost:
      deviceList.append(dev.id)
#Sort the device on id
deviceList.sort()

for dev in deviceList:
    print ('Device %s has no rig host set' % (dev))
    of.write('Device %s has no rig host set\n' % (dev))
of.close()

