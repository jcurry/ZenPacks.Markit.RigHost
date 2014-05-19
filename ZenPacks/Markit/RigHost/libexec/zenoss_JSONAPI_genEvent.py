#!/usr/bin/env python
#
# Author:               Jane Curry
# Date                  October 7th, 2013
# Description:          Generates Zenoss event using JSON API
#                       Lines at top may need modifying for Zenoss server, port and https
#                       Requires parameters for device, severity, evclasskey and summary where summary in format
#                          User=jane Rig=Rig3 Host=testdb33 App=DBS stop
# Updates:              October 21st 2013
#                       Modified user parameter to gather info directly from environment if ommited from summary string
#                       January 24th 2014
#                       Sample commands added
#
# Sample commands:      ./zenoss_JSONAPI_genEvent.py --evclasskey=Rig --summary='Rig=Production Host=prodapp16 App=TMS stop' --severity=Warning
#                       ./zenoss_JSONAPI_genEvent.py --evclasskey=Rig --summary='Rig=Production Host=prodapp16 App=TMS start' --severity=Info
#                       ./zenoss_JSONAPI_genEvent.py --evclasskey=Rig --summary='Rig=Production Host=prodapp15 App=TMS stop' --severity=Warning
#                                - should create a /Rig/Error event as prodapp15 does not exist
#                       ./zenoss_JSONAPI_genEvent.py --evclasskey=Rig --summary='Rig=Production stop' --severity=Warning
#                       ./zenoss_JSONAPI_genEvent.py --evclasskey=Rig --summary='Rig=Production start' --severity=Info
#                       ./zenoss_JSONAPI_genEvent.py --evclasskey=Rig --summary='Rig=Rig3 Host=testdb33 stop' --severity=Warning
#                       ./zenoss_JSONAPI_genEvent.py --evclasskey=Rig --summary='Rig=Rig3 Host=testdb33 start' --severity=Info


import json
import urllib
import urllib2
import os
import sys
from optparse import OptionParser

#ZENOSS_INSTANCE = 'http://ZENOSS-SERVER:8080'
# Change the next line(s) to suit your environment
#
ZENOSS_SERVER="mon_hub.mserv.local"
#ZENOSS_SERVER="zen42.class.example.org"
#ZENOSS_SERVER="mon-uat-hub.mserv.local"
#ZENOSS_PORT="8080"
ZENOSS_PORT=""

if ZENOSS_PORT:
    ZENOSS_INSTANCE = 'https://' + ZENOSS_SERVER + ':' + ZENOSS_PORT
else:
    ZENOSS_INSTANCE = 'https://' + ZENOSS_SERVER

ZENOSS_USERNAME = 'MonAPI'
ZENOSS_PASSWORD = 'monapipwd'

ROUTERS = { 'EventsRouter': 'evconsole',}

class sendEventsWithJSON():
    def __init__(self, debug=False):
        """
        Initialize the API connection, log in, and store authentication cookie
        """
        try:
            # Use the HTTPCookieProcessor as urllib2 does not save cookies by default
            self.urlOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
            if debug: self.urlOpener.add_handler(urllib2.HTTPHandler(debuglevel=1))
            self.reqCount = 1

            # Contruct POST params and submit login.
            loginParams = urllib.urlencode(dict(
                            __ac_name = ZENOSS_USERNAME,
                            __ac_password = ZENOSS_PASSWORD,
                            submitted = 'true',
                            came_from = ZENOSS_INSTANCE + '/zport/dmd'))
            self.urlOpener.open(ZENOSS_INSTANCE + '/zport/acl_users/cookieAuthHelper/login',
                                loginParams)
        except:
            print 'Failed to open communications connection'
            sys.exit(1)

    def _router_request(self, router, method, data=[]):
        if router not in ROUTERS:
            raise Exception('Router "' + router + '" not available.')

        # Contruct a standard URL request for API calls
        req = urllib2.Request(ZENOSS_INSTANCE + '/zport/dmd/' +
                              ROUTERS[router] + '_router')

        # NOTE: Content-type MUST be set to 'application/json' for these requests
        req.add_header('Content-type', 'application/json; charset=utf-8')

        # Convert the request parameters into JSON
        reqData = json.dumps([dict(
                    action=router,
                    method=method,
                    data=data,
                    type='rpc',
                    tid=self.reqCount)])

        # Increment the request count ('tid'). More important if sending multiple
        # calls in a single request
        self.reqCount += 1

        # Submit the request and convert the returned JSON to objects
        return json.loads(self.urlOpener.open(req, reqData).read())


    def add_event(self, summary, device, component, severity, evclasskey, evclass=None):
        """ Use EventsRouter action (Class) and query method found
            in JSON API docs on Zenoss website:
            Parameters:

            summary (string) - New event's summary
            device (string) - Device uid to use for new event
            component (string) - Component uid to use for new event
            severity (string) - Severity of new event. Can be one of the following: Critical, Error, Warning, Info, Debug, or Clear
            evclasskey (string) - The Event Class Key to assign to this event
            evclass (string) - Event class for the new event
            Returns:
                {u'uuid': u'81c2c30c-694d-47c3-95de-10d62a2f372d', u'tid': 1, u'result': {u'msg': u'Created event', u'success': True}, u'action': u'EventsRouter', u'type': u'rpc', u'method': u'add_event'}

        """
        data = {}
        data['summary'] = summary
        data['device'] = device
        data['component'] = component
        data['severity'] = severity
        data['evclasskey'] = evclasskey
        data['evclass'] = evclass

        #return self._router_request('EventsRouter', 'add_event', [data])['result']
        return self._router_request('EventsRouter', 'add_event', [data])




if __name__ == "__main__":
    usage = 'python %prog --summary=summary --device=device --component=component --severity=severity --evclasskey=evclasskey --evclass=evclass'

    parser = OptionParser(usage)
    parser.add_option("--summary", dest='summary',
                        help='eg. \'User=jane Rig=Rig3 Host=testdb33 App=DBS stop. If user ommitted then $USER is used\'')
    parser.add_option("--device", dest='device',
                        help='eg. --device=\'zen42.class.example.org\'')
    parser.add_option("--component", dest='component',
                        help='eg. --component=\'Test Component\'')
    parser.add_option("--severity", dest='severity',
                        help='severity text values eg. severity=\'Warning\'')
    parser.add_option("--evclasskey", dest='evclasskey',
                        help='eg. --evclasskey=\'Rig\'')
    parser.add_option("--evclass", dest='evclass',
                        help='eg. --evclass=\'/Skills\' (though you may not want to specify a class')

    (options, args) = parser.parse_args()

    # options is an object - we want the dictionary value of it
    # Some of the options need a little munging...

    option_dict = vars(options)
    if option_dict['severity'] not in ('Critical', 'Error', 'Warning', 'Info', 'Debug', 'Clear'):
        raise Exception('Severity "' + option_dict['severity'] +'" is not valid.')

    if not option_dict['device']:
        device = os.getenv('HOSTNAME')
    else:
        device = option_dict['device']

    summary = option_dict['summary']
    if summary.find('User') == -1:
        username = os.getenv('USER')
        summary = 'User=' + username + ' ' + summary


    events = sendEventsWithJSON()
    newEvent = events.add_event(summary, device, options.component, options.severity, options.evclasskey, options.evclass)
    print(newEvent)
    try:
        if newEvent['result']['msg'].find('Created event') != -1:
            os._exit(0)
        else:
            os._exit('Failed - no created event in message')
    except:
        os._exit('Failed in try clause - event not well formed')


