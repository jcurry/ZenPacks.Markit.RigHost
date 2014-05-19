#!/bin/bash
# Author:               Jane Curry, Skills 1st Ltd, jane.curry@skills-1st.co.uk
# Date:                 February 4th, 2014
# Update history:       
#
# Copy server.cfg from msrvadm00 and backup previous version
# Source file is  /export/system/OV/service/server.cfg on msrvadm00
# Destination file is  /opt/zenoss/libexec/rig_manager_server.cfg on Zenoss server
# This script assumes that public-key ssh is setup between the 2 systems for the zenoss user
# The existing version is copied to /opt/zenoss/libexec/rig_manager_server.cfg.date
#
# This script must be run as the zenoss user
#
#set -x
# Source the zenoss environment
. ~zenoss/.bashrc
# get date
date_suffix=`date +%Y%m%d%H%M%S`
source_host=msrvadm00
#source_host=lotschy.skills-1st.co.uk
#source_user=zenplug
source_user=zenoss

cp /opt/zenoss/libexec/rig_manager_server.cfg /opt/zenoss/libexec/rig_manager_server.cfg.$date_suffix
#if [ $(scp $source_user@$source_host:/export/system/OV/service/server.cfg /opt/zenoss/libexec/rig_manager_server.cfg) -ne 0 ]
scp $source_user@$source_host:/export/system/OV/service/server.cfg /opt/zenoss/libexec/rig_manager_server.cfg
if [ $? -ne 0 ]
then
    exit 1
else
    exit 0
fi
