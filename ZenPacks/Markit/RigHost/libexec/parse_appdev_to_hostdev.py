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
            #   that the GUI does not see the property.  Always use the setZenProperty method

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
    d = dmd.Devices.findDevice(appdev)
    if d:
        for s in dmd.Systems.getSubOrganizers():
            if s.getOrganizerName() == targetSys:
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
    else:
        logfile.write( ' Device %s does not exist in Zope database \n ' % (appdev))


for line in rmf:
    #logfile.write( 'line is %s \n' % (line))
    # Examples

    #classPath,id,productionState,Appside,Rig,AppCat,Host,,for

    # line1='/Application/EGUS,fiaegus.markit.com,Active,Buyside,Production,,,,appcat'
    # line2='/Application/INTEROP/QA/ICE,interop.qa.ice,Active,MarkitWire,,JBOSS,,,'
    # line3='/Application/SSL_Certificate_Checks,creditcentre.markitserv.com.443,Not Monitored,n/a,Production,,,,'
    # line4='/Application/Process_Monitors/MTM,mtm_webapp_server_5_prod,Active,Buyside,Production,,mtmprodappa1,,'
    # line5='/MarkitDatabases,GC_Application_Server,Active,MarkitWire,n/a,DBS,n/a,,'
    # line6='/MarkitDatabases,PRD00GTW,Active,MarkitWire,Production,DBS,instance only are bound a host,,'
    # line7='/Application/MarkitWire/TMS/TMS_Pulse,TMS_Pulse_prodapp16,Active,MarkitWire,Production,TMS,prodapp16,,'
    #
    # We always get 9 fields. Some may be null or n/a
    #
    # Updated Jan 23rd, 2014 - now get 7 fields - no longer get ,,<for> on the end
    #
    # classPath,id,productionState,Appside,Rig,AppCat,Host

    if not line.startswith('#'):
        splitline=line.split(',')
        #if len(splitline) == 9:
        if len(splitline) == 7:
            appdev = splitline[1].strip()
            hostdev = splitline[6].strip()
            #
            logfile.write( ' App device is %s and host dev is %s \n' % (appdev, hostdev))
            appside = splitline[3].strip()
            rig = splitline[4].strip()
            appcat = splitline[5].strip()                       #appcat is what we know as the app name eg. TMS, DBS, ..
            appclass = splitline[0].strip()
            # Jan 23rd, 2014 - dont need the following as appcat provides the leaf-node system name

            #appclass = splitline[0].strip()
            #appclassname = appclass.split('/')[-1]              # the application name is the last part of the device class eg. EU, TMS, ...
            ##appclassname = appclass.split('/')
            # Get a list of all the unique leaf-node system names (apps from the point-of-view of Systems)
            #legalSysList = []
            #for s in dmd.Systems.RIGS.MWIRE.getSubOrganizers():
            #    if not s.getSubOrganizers():
            #        if not s.id in legalSysList:
            #            legalSysList.append(s.id)
            # Try to get appname from the app device class  - not perfect .....
            #appname = ''
            #for s in legalSysList:
            #    if appclass.find(s) != -1:
            #        appname = s
            #        break
            #logfile.write( ' App name is %s \n ' % (appname))
             

            a=dmd.Devices.findDevice(appdev)
            if a:
                if hostdev and hostdev != 'n/a' and hostdev.find(' ') == -1:
                    setRigHost(appdev, hostdev)                 # RigHost property successfully set or was already correct
                if appclass.startswith('/Application'):
                    if appside == 'MarkitWire':
                        if rig:                                 #If rig not supplied then we definately won't find a system
                            # The EU app from the server file is known as WEB by the Rig Manager group
                            if appcat == 'EU':
                                appcat = 'WEB'
                            targetSys = '/RIGS/MWIRE/' + rig + '/' + appcat
                            logfile.write( 'Target system is %s for app device %s \n ' % (targetSys, appdev))
                            setSysForHost(appdev, targetSys)
                        else:
                            logfile.write( 'No rig field supplied')
                    else:
                        logfile.write( 'appside is not MarkitWire - appside %s not currently implemented \n ' % (appside))
                else:
                    logfile.write( 'Device %s in class %s - nothing done as class doesnt start with /Application \n' % (appdev, appclass))

                

