#!/usr/bin/env python
# Author:		Jane Curry
# Date			Jan 24th 2014
# Description:		for all devices with non-null cRigHost, set cRigHost to empty list
#                       cRigHost is a list
#                       Output to $ZENHOME/local/clear_all_cRigHost.out
# Parameters:		
# Updates:		
#
import os
import time
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from transaction import commit

zenhome = os.environ['ZENHOME']

outputFile = zenhome + '/local/clear_all_cRigHost.out'

of = open(outputFile, "w")
localtime = time.asctime( time.localtime(time.time()) )
of.write(localtime + "\n\n")

# Need noopts=True or it barfs with the script options
dmd = ZenScriptBase(connect=True, noopts=True).dmd

deviceList=[]
for dev in dmd.Devices.getSubDevices():
    if dev.cRigHost:
        print ('Device %s has rig host(s) %s . Resetting to empty list. \n' % (dev,dev.cRigHost))
        of.write('Device %s has rig host(s) %s . Resetting to empty list. \n' % (dev,dev.cRigHost))
        dev.setZenProperty('cRigHost', [])
        commit()

of.close()

