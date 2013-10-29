#!/usr/bin/env python
# Author:               Jane Curry
# Date:                 Oct 21st 2013
# Updated:
# Description:          Parses the appdev_to_hostdev.cfg file in $ZENHOME/libexec
#                       Checks that appdev and host dev esist in Zenoss and
#                       sets the custom property cRigHost for the appdev to the hostdev
#

import time
import os

import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from Products.ZenUtils.Utils import unused
from transaction import commit
#from ZODB.transact import transact


unused(Globals)

dmd = ZenScriptBase(connect=True, noopts=True).dmd


zenhome = os.environ['ZENHOME']
logfileName = zenhome + '/log/parse_appdev_to_hostdev.log'

logfile = open(logfileName, 'a')
localtime = time.asctime( time.localtime(time.time()) )
logfile.write('\n' + localtime + "\n\n")

rmfName = zenhome + '/libexec/appdev_to_hostdev.cfg'
rmf = open(rmfName, 'r')

sync = dmd.zport._p_jar.sync
sync()

#@transact
def setRigHost(appdev, hostdev):
    a=dmd.Devices.findDevice(appdev)
    if a:
        h = dmd.Devices.findDevice(hostdev)
        if h:
            # Do we need to allow for multiple host devices? Yes?
            # So should we append to the existing cRigHost list?
            # If so, what deletes old entries?
            # need to check existence of a.cRigHost as it appears to default to the null string,
            #      not an empty list
            # NOTE: Do NOT set properties directly (eg a.cRigHost = ['fred'] - this will cause havoc such
            #   that the GUI does not see the property.  Always use the setZenProperrty method

            if a.cRigHost:
                if not hostdev in a.cRigHost:
                    newRigHost = a.cRigHost
                    newRigHost.append(hostdev)
                    a.setZenProperty('cRigHost',newRigHost)
                else:
                    logfile.write( ' In setRigHost. App device %s already has RigHost property including %s \n ' % (appdev, hostdev))
            else:
                a.setZenProperty('cRigHost', [hostdev])

            commit()
            logfile.write( ' In setRigHost. App device %s now has host dev %s added. cRigHost now set to %s \n' % (appdev, hostdev, a.cRigHost))
            return True
        else:    
            logfile.write( ' In setRigHost. Host device %s does not exist in Zenoss database. \n' % (hostdev))
            return False
    else:
        logfile.write( ' In setRigHost. App device %s does not exist in Zenoss database. \n' % (appdev))
        return False

def setSysForHost(appdev, targetSys):
    # Do we need to append this system to an existing system list or do we overwrite any existing systems?  Append?
    # If append, how do we clean out unwanted systems?

    foundSys = False
    for s in dmd.Systems.getSubOrganizers():
        if s.getOrganizerName() == targetSys:
            d = dmd.Devices.findDevice(appdev)
            currSys = d.getSystemNames()
            logfile.write('In setSysForHost.  targetSys is %s and currSys is %s \n ' % (targetSys, currSys))
            if not targetSys in currSys:                # Check whether targetSys already in system list
                currSys.append(targetSys)
                d.setSystems(currSys)
                logfile.write( ' In setSysForHost. Setting system for device %s to %s \n ' % (appdev, currSys))
                #d.setSystems(currSys.append(targetSys))
                commit()
            else:
                logfile.write( ' In setSysForHost. Device %s is already a member of System %s \n ' % (appdev, targetSys))

            foundSys = True
            break

    if not foundSys:
        logfile.write( ' In setSysForHost. Target system %s does not exist \n ' % (targetSys))


for line in rmf:
    #logfile.write( 'line is %s \n' % (line))
    # Examples
    # line1='/Application/EGUS,fiaegus.markit.com,Active,Buyside,Production,'
    # line2='/Application/INTEROP/QA/ICE,interop.qa.ice,Active,MarkitWire,,'
    # line3='/Application/SSL_Certificate_Checks,creditcentre.markitserv.com.443,Not Monitored,n/a,Production,'
    # line4= '/Application/Process_Monitors/MTM,mtm_webapp_server_5_prod,Active,Buyside,Production,mtmprodappa1'
    # line5='/MarkitDatabases,GC_Application_Server,Active,MarkitWire,n/a,n/a'
    # line6='/MarkitDatabases,PRD00GTW,Active,MarkitWire,Production,instance only are bound a host'
    #
    # We always get 6 fields. Some may be null or n/a

    if not line.startswith('#'):
        splitline=line.split(',')
        if len(splitline) == 6:
            appdev = splitline[1].strip()
            hostdev = splitline[5].strip()
            #
            logfile.write( ' App device is %s and host dev is %s \n' % (appdev, hostdev))
            appside = splitline[3].strip()
            rig = splitline[4].strip()
            appclass = splitline[0].strip()
            #appclassname = appclass.split('/')[-1]              # the application name is the last part of the device class eg. EU, TMS, ...
            #appclassname = appclass.split('/')
            # Get a list of all the unique leaf-node system names (apps from the point-of-view of Systems)
            legalSysList = []
            for s in dmd.Systems.RIGS.MWIRE.getSubOrganizers():
                if not s.getSubOrganizers():
                    if not s.id in legalSysList:
                        legalSysList.append(s.id)
            appname = ''
            for s in legalSysList:
                if appclass.find(s) != -1:
                    appname = s
                    break
            logfile.write( ' App name is %s \n ' % (appname))
             

            if appdev and hostdev and hostdev != 'n/a' and hostdev.find(' ') == -1:
                if setRigHost(appdev, hostdev):                 # RigHost property successfully set or was already correct
                    if appside == 'MarkitWire':
                        if rig:                                 #If rig not supplied then we definately won't find a system
                            #targetSys = '/RIGS/MWIRE/' + rig + '/' + appclassname
                            targetSys = '/RIGS/MWIRE/' + rig + '/' + appname
                            logfile.write( 'Target system is %s for app device %s \n ' % (targetSys, appdev))
                            setSysForHost(appdev, targetSys)
                        else:
                            logfile.write( 'No rig field supplied')
                    else:
                        logfile.write( 'appside is not MarkitWire - appside %s not currently implemented \n ' % (appside))

                

