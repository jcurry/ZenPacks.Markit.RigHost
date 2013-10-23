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
import re

import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from Products.ZenUtils.Utils import unused
import transaction
from ZODB.transact import transact

from transaction import commit

unused(Globals)

dmd = ZenScriptBase(connect=True, noopts=True).dmd


zenhome = os.environ['ZENHOME']
logfileName = zenhome + '/log/parse_appdev_to_hostdev.log'

logfile = open(logfileName, 'a')
localtime = time.asctime( time.localtime(time.time()) )
logfile.write(localtime + "\n\n")

# ZenPack __init__.py copies some files from the ZP libexec to $ZENHOME/libexec
rmfName = zenhome + '/libexec/appdev_to_hostdev.cfg'
rmf = open(rmfName, 'r')

mysys = re.compile('^(?P<rig>\w+),(?!CERT,)(?P<host>\w+),(?P<app>\w+),')

sync = dmd.zport._p_jar.sync
sync()

# Add a host to a system if that host exists in the Zope database
# Return True if syccessful; returns False if update failed or host didn't exist
# ZODB database updates should be single transactions
@transact
def addHostToSys(host, sys):
    d=dmd.Devices.findDevice(host)
    if d:
        oldsys = d.getSystemNames()
        oldsys.append(sys)
        try:
            logfile.write( 'Updating systems with %s . New system is %s . Host is %s \n' % (sys, oldsys, host))
            d.updateDevice(systemPaths = oldsys)
            commit()
            return True
        except:
            logfile.write( 'Error adding host %s to system %s \n' % (host, sys))
            return False
    return False


# Clean out all systems under /RIGS/MWIRE first
# create a context for the sync function

#@transact
#def delOrgs():
#    dmd.Systems.manage_deleteOrganizer('/Systems/RIGS/MWIRE')
#
#delOrgs()
#
#commit()

# Collect updates in updateList
updateList = []

for line in rmf:
    #logfile.write( 'line is %s \n' % (line))
    s = mysys.match(line)
    if s:
        rig = s.group('rig')
        host = s.group('host')
        app =  s.group('app')
        newsys = '/RIGS/MWIRE/' + rig + '/' + app
        logfile.write( ' Rig is %s, host is %s, app is %s newsys is %s\n' % (rig, host, app, newsys))
        # Create a system under /Systems - /RIGS and/or /RIGS/MWIRE are automatically created if they don't exist
        #
        SysMatch = False
        for d in dmd.Systems.getSubOrganizers():
          logfile.write(' checking suborganizers.  newsys is %s d.getOrganizerName() is %s \n' % ( newsys, d.getOrganizerName()))
          if d.getOrganizerName() == newsys and d.getOrganizerName().startswith('/RIGS/MWIRE/'):    # Found an existing system
            SysMatch = True
            logfile.write(' Found system match.  newsys is %s d.getOrganizerName() is %s \n' % ( newsys, d.getOrganizerName()))
            HostMatch = False
            for h in d.getSubDevices():
              if h.titleOrId() == host:       # found matching host for this existing system
                logfile.write( 'In host match loop - found existing host - host is %s and h.id is %s and system is %s\n' % (host, h.id, newsys))
                HostMatch = True
                break
            # Search exhausted - this host doesn't exist in this system
            # Add host to system
            if not HostMatch:
                #addHostToSys(host, newsys)
                if addHostToSys(host, newsys):
                    updateList.append((host,newsys))
            break            # System already exists - get out of here
        # Search exhausted - no match found so add this new system

        if not SysMatch:
          logfile.write( 'Found a new system %s \n' % (newsys))
          try:
              @transact
              def addOrg():
                  dmd.Systems.manage_addOrganizer(newsys)
                  dmd.Systems.getOrganizer(newsys).description='Added by parse_rig_manager_script at ' + localtime
              addOrg()
              commit()
          except:
              transaction.abort()
              logfile.write("Encountered error. adding system %s\n" % (newsys))
              raise
          # Add host to system
          if addHostToSys(host, newsys):
              updateList.append((host,newsys))


commit()
for host, newsys in updateList:
    print ' Updated host / system is %s / %s \n' % (host, newsys)

