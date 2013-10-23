#!/usr/bin/env python
# Author:               Jane Curry
# Date:                 Sep 19th 2013
# Updated:
# Description:          Takes rig name and host name and changes prodState for all devices and apps in the host specified 
#                       Use RigHost custom property on /Application devices to find containing device(s)
#                       Note an app may run on more than one host
#
# Rig name supplied as param 1 - must exist and be non-null
# Host name supplied as param 2 - must exist and may be All
# App name supplied as param 3 - must exist and may be All
# State to change to is param 4 - where 300 and 1000 are legal

import sys
import time
import os

import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from Products.ZenUtils.Utils import unused
from transaction import commit

from subprocess import Popen,PIPE

unused(Globals)

dmd = ZenScriptBase(connect=True, noopts=True).dmd


zenhome = os.environ['ZENHOME']
logfileName = zenhome + '/log/rig_host_change.log'

logfile = open(logfileName, 'a')
localtime = time.asctime( time.localtime(time.time()) )
logfile.write(localtime + "\n\n")

# Null values will be set to the string 'All'
try:
    rigname = sys.argv[1]
    hostname = sys.argv[2]
    appname = sys.argv[3]
    state = sys.argv[4]
except:
    logfile.write(' Error - need 4 arguments for this script \n')

def genErrorEvent(message):
    ZENOSS_SERVER = 'mon-uat-hub.mserv.local'
    zensendevent_basecmd = zenhome + '/bin/zensendevent'
    zensendevent_params = ' -d ' + ZENOSS_SERVER + ' -s Error -c /Rig/Error ' + message
    cmd = zensendevent_basecmd + zensendevent_params
    logfile.write(' In genErrorEvent - cmd is %s \n' % (cmd))
    try:
        Popen(cmd, shell=True, stdout=PIPE,stderr=PIPE)
    except:
        logfile.write(' Error generating zensendevent error event \n')


def change_prodState(host, state):
    ''' host is a device object
        state is either '300' for maintenance' or '1000' for production
    '''


    logfile.write(' Time: %s Before change host.id is %s, host.preMWProductionState is %s, host.productionState is %s \n' % (localtime, host.id, host.preMWProductionState, host.productionState))
    if state == '300':
        if host.productionState > 300:
            host.preMWProductionState = host.productionState
            commit()
            # setProdState seems to set both prod state, not just productionState
            host.productionState = int(state)      # set productionState to maintenance (300)
            commit()
            logfile.write( 'Time: %s  After change host.id is %s, host.preMWProductionState is %s, host.productionState is %s \n' % (localtime, host.id, host.preMWProductionState, host.productionState))

    elif state == '1000':
        if host.productionState >= 300:
            host.productionState = host.preMWProductionState
            commit()
            logfile.write( ' Time: %s After change host.id is %s, host.preMWProductionState is %s, host.productionState is %s \n' % (localtime, host.id, host.preMWProductionState, host.productionState))

def getSystemFromRigAndApp(rigname, appname):
    ''' 
        Take strings representing rigname and appname and return the correct system that represents this combination
    '''

    matchSystem = '/RIGS/MWIRE/' + rigname + '/' + appname
    for s in dmd.Systems.getOrganizerNames():
        logfile.write(' In getSystemFromRigAndApp - matchSystem is %s and s is %s \n ' % (matchSystem, s))
        if s == matchSystem:
            return  dmd.Systems.getOrganizer(s)
    return False

if rigname:
    if hostname != 'All':
        d=dmd.Devices.findDevice(hostname)   # Check that the hostname device exists
        if d:               # Check that the host device actually exists
            # Check that device d is in rig rigname
            for s in dmd.Systems.RIGS.MWIRE.getSubOrganizers():
                if s.id == rigname:
                # Get all the hosts in rigname
                    for d1 in s.getSubDevices():
                        if d1.id == hostname:           # We have a legal rigname containing the host hostname
                            # If App name not supplied & Host name is, check all Apps for matching host name in cRigHost custom property (which is a list)
                            # This means command format is rig host start | stop
                            logfile.write('Rig Host format - rig = %s and host = %s \n' % (rigname, hostname)) 
                            if appname == 'All':
                                # deal with the host device first
                                change_prodState(d, state)
                                # Now do any apps associated with this device
                                for a in dmd.Devices.Application.getSubDevices():
                                    if hostname in a.cRigHost:
                                        change_prodState(a, state)
                                sys.exit(0)
                            else:
                                # This is the rig host app start | stop format
                                logfile.write('Rig Host App format - rig = %s and host = %s  and app is %s \n' % (rigname, hostname, appname)) 
                                s = getSystemFromRigAndApp(rigname, appname)
                                logfile.write('System is %s \n' % (s))
                                if s:           # We have a legal System 
                                    for a in s.getSubDevices():
                                            if a.getDeviceClassPath().startswith('/Application'):      #Application device
                                                if hostname in a.cRigHost:              #and the application device cRigHost includes hostname
                                                    change_prodState(a, state)
                                    sys.exit(0)
                                else:
                                    # if we don't have a legal system combination then sys.exit(1)
                                    genErrorEvent('Error - rigname %s / hostname %s / appname %s combination does not deliver a valid System  \n' % ( rigname, hostname, appname))
                                    sys.exit('Error - rigname %s / hostname %s / appname %s combination does not deliver a valid System  \n' % ( rigname, hostname, appname))
                    # If we get here then we have a rig / hostname pair that Zenoss doesn't know about
                    genErrorEvent('Error - rigname %s / hostname %s combination does not deliver a valid System  \n' % ( rigname, hostname))
                    sys.exit('Error - rigname %s / hostname %s combination does not deliver a valid System  \n' % ( rigname, hostname))
        else:   # hostname is supplied but device d does not exist
            logfile.write('Error - hostname %s is supplied but device does not exist \n' % ( hostname)) 
            genErrorEvent('Error - hostname %s is supplied but device does not exist \n' % ( hostname))
            sys.exit('Error - hostname %s is supplied but device does not exist \n' % ( hostname))

    elif appname != 'All':
        # This is the rig appname start | stop variant - need to check the cRigHost of appname for all  app devices in this System
        logfile.write('Rig App format - rig = %s and app = %s \n' % (rigname, appname)) 
        s = getSystemFromRigAndApp(rigname, appname)
        if s:
            for a in s.getSubDevices():
                # The application device must be a member of the System where system is eg. Rig1/TMS
                # TODO: Check with Georges that this is valid
                # An app in several rigs will only be changed in this particular rig/app combination
                if a.getDeviceClassPath().startswith('/Application'):
                    change_prodState(a, state)
            sys.exit(0)
        else:           #rigname / appname combination does not deliver a valid System
            logfile.write('Error - rigname %s / appname %s combination does not deliver a valid System  \n' % ( rigname, appname)) 
            genErrorEvent('Error - rigname %s / appname %s combination does not deliver a valid System  \n' % ( rigname, appname))
            sys.exit('Error - rigname %s / appname %s combination does not deliver a valid System  \n' % ( rigname, appname))

    else:
        # This is the simple rig start / stop
        logfile.write('Rig format - rig = %s \n' % (rigname)) 
        for s in dmd.Systems.RIGS.MWIRE.getSubOrganizers():
        # Get all the hosts in rigname
            if s.id == rigname:
                for d in s.getSubDevices():
                    change_prodState(d, state)
                    # TODO: Check with Georges - should we follow cRigHost anyway?????
                    # Now do any apps associated with this device
                    #  This isn't necessary the devices should be part of the System anyway - no need to follow cRigHost link
                    for a in dmd.Devices.Application.getSubDevices():
                        if d.id in a.cRigHost:
                            change_prodState(a, state)
                sys.exit(0)
        # If we get here then we didn't find the rigname
        genErrorEvent('Error - rigname doesnt exist as valid system' )
        sys.exit('Error - rigname doesnt exist as valid system' )
else:
    # Error
    logfile.write('Error - no rigname supplied \n' ) 
    genErrorEvent('Error - no rigname supplied' )
    sys.exit('Error - no rigname supplied' )
