# -------------------------------------------------------------------------------
# Name:         sfp_punkspider
# Purpose:      Query the QOMPLX PunkSpider API to see if our target appears.
#
# Author:      Steve Micallef <steve@binarypool.com>
#
# Created:     07/08/2021
# Copyright:   (c) Steve Micallef
# Licence:     GPL
# -------------------------------------------------------------------------------

import hashlib
import json

from spiderfoot import SpiderFootEvent, SpiderFootPlugin


class sfp_punkspider(SpiderFootPlugin):

    meta = {
        'name': "PunkSpider",
        'summary': "Check the QOMPLX punkspider.io service to see if the target is listed as vulnerable.",
        'flags': [""],
        'useCases': ["Footprint", "Investigate", "Passive"],
        'categories': ["Leaks, Dumps and Breaches"],
        'dataSource': {
            'website': "https://punkspider.io/",
            'model': "FREE_NOAUTH_UNLIMITED",
            'logo': "https://punkspider.io/img/logo.svg",
            'description': "The idea behind Punkspider is very simple - we're doing a bunch "
            "of complicated stuff to find insecurities in massive amounts of websites, with "
            "the goal of scanning the entire Internet."
        }
    }
    # Default options
    opts = {
    }

    # Option descriptions
    optdescs = {
    }

    # Be sure to completely clear any class variables in setup()
    # or you run the risk of data persisting between scan runs.

    results = None

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        self.results = self.tempStorage()

        # Clear / reset any other class member variables here
        # or you risk them persisting between threads.

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    def watchedEvents(self):
        return ["INTERNET_NAME"]

    # What events this module produces
    def producedEvents(self):
        ret = ["VULNERABILITY"]

        return ret

    def query(self, qry):
        ret = None
        qryhash = hashlib.md5(qry.encode('utf-8', errors='replace').lower()).hexdigest()
        url = f"https://api.punkspider.org/api/partial-hash/{qryhash}"

        res = self.sf.fetchUrl(url, timeout=30, useragent=self.opts['_useragent'])
        if res['content'] is None:
            self.sf.debug("No content returned from PunkSpider")
            return None

        try:
            ret = json.loads(res['content'])
        except Exception as e:
            self.sf.error(f"Error processing response from PunkSpider: {e}")
            return None
        return ret

    # Handle events sent to this module
    def handleEvent(self, event):
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        self.sf.debug(f"Received event, {eventName}, from {srcModuleName}")

        if eventData in self.results:
            self.sf.debug(f"Skipping {eventData}, already checked.")
            return None

        self.results[eventData] = True

        res = self.query(eventData)
        if not res:
            return None

        for rec in res:
            if 'vulns' not in res[rec]:
                continue

            for vuln in res[rec]['vulns']:
                if res[rec]['vulns'][vuln] == 0:
                    continue
                e = SpiderFootEvent("VULNERABILITY", f"{vuln}: {res[rec]['vulns'][vuln]}", self.__name__, event)
                self.notifyListeners(e)

# End of sfp_punkspider class
