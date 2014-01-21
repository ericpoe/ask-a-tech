#! /usr/bin/python

"""
Ask-a-Tech came about because we had staff not inform us of technical issues because they thought the issues were not
ticket-worthy or they didn't want to bother IT with their "silly" question. Instead, they would call or email one
of us. This gave us no way to track these minor issues or gauge trends.

Ask-a-Tech was built as a Google Form that requires the user to sign-in in order to use it. It tracks the timestamp,
username, and the question they have.

This script is designed to take the question from the Google form and use it to create a ticket in Web Help
Desk.

Steps taken:
1. Check response spreadsheet in Google Drive
2. Loop through each row in the main worksheet
    a. Pull data from row
    b. Generate Web Help Desk JSON
    c. Submit JSON to Web Help Desk
    d. Copy data to archival worksheet in spreadsheet
    e. Delete data from main worksheet in spreadsheet
3. Log errors to "ask-a-tech-server.log"

The script's login credentials for Google Drive, spreadsheet identifiers, and Web Help Desk information are identified
in config.py

APIs used:
    gdata-python-client v3
    Solarwinds Web Help Desk API (REST)

See:
    http://www.webhelpdesk.com/api/
    http://gdata-python-client.googlecode.com/hg/pydocs/gdata.spreadsheet.html
    https://code.google.com/p/gdata-python-client/source/browse/samples/spreadsheets/spreadsheetExample.py
    http://mrwoof.tumblr.com/post/1004514567/using-google-python-api-to-get-rows-from-a-google

"""

__author__ = 'eric poe'
__date__ = '2014-01-21'

import socket
import logging
import urllib2
import json

import gdata.service
import gdata.spreadsheet
import gdata.spreadsheet.service
import gdata.spreadsheet.text_db

import config  # from config.py


class AskATech():
    def run(self):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            filename='ask-a-tech_error.log')
        self.getGoogleEntries()

    def getGoogleEntries(self):
        """
        This code assumes you have a spreadsheet that looks something like this:

        Timestamp  		    |	Username            	|	Question?
        1/13/2014 12:15:00  |	user1@usd230.org		|   Lorem ipsum dolor sit amet?
        1/15/2014 14:25:35	|	user2@usd230.org		|	Nunc libero nulla, scelerisque sed facilisis vel?

        Google Spreadsheets normalizes the column names for the purposes of the API by stripping all non-alphanumerics
        and lower-casing, hence the column names used in the code as "timestamp", "username", and "question".
        """

        # ## Log in to Google Docs
        # # Set up login credentials
        gd_client = gdata.spreadsheet.service.SpreadsheetsService()
        gd_client.email = config.gapps['email']
        gd_client.password = config.gapps['password']
        gd_client.source = config.gapps['project_name']
        try:
        # log in
            gd_client.ProgrammaticLogin()
        except gdata.service.BadAuthentication, e:
            logging.error('Authentication error: ' + str(e))
            return False
        except socket.sslerror, e:
            logging.error('Spreadsheet socket.sslerror: ' + str(e))
            return False
        except socket.error, e:
            logging.error('ProgrammaticLogin socket.error: ' + str(e))

        ## Fetch the spreadsheet data
        try:
            feed = gd_client.GetListFeed(config.sheet['key'], config.sheet['sheet'])
        except gdata.service.RequestError, e:
            logging.error('Spreadsheet gdata.service.RequestError: ' + str(e))
            return False
        except socket.sslerror, e:
            logging.error('Spreadsheet socket.sslerror: ' + str(e))
            return False
        except socket.error, e:
            logging.error('Spreadsheet socket error: ' + str(e))
            return False

        ## Process the spreadsheet
        self.processRows(gd_client, config.sheet['key'], feed, config.sheet['archive'])

    def processRows(self, gd_client, key, feed, arch_wksht_id):
        ## Iterate over the rows
        for row_entry in feed.entry:
            # to get the column data out, you use the text_db.Record class, then use the dict record.content
            record = gdata.spreadsheet.text_db.Record(row_entry=row_entry)
            data = self.generateJson(record.content['username'], record.content['question'])
            # print data
            self.submitJsonToWhd(data)
            if not self.moveRecord(gd_client, record, key, arch_wksht_id):
                logging.error("Error: record not moved.")
                return False

    def generateJson(self, address_from, text):
        subject = "Ask-A-Tech"
        user = address_from[: address_from.find("@")]  # find the user name before the first "@" symbol

        msg = {
            'emailClient': 'false',
            'subject': subject,
            'detail': text,
            'problemtype': {
                'type': 'ProblemType',
                'id': config.whd['json']['ProblemType']},
            'isPrivate': 'false',
            'sendEmail': 'false',
            'location': {
                'type': 'Location',
                'id': config.whd['json']['Location']},
            'room': 'Network',
            'clientReporter': {
                'type': 'Client',
                'id': user},
            'statustype': {
                'type': 'StatusType',
                'id': config.whd['json']['StatusType']},
            'prioritytype': {
                'type': 'PriorityType',
                'id': config.whd['json']['PriorityType']}
        }
        data = json.dumps(msg)

        return data

    def submitJsonToWhd(self,jsonMsg):
        WhdUrl = 'https://{0}/helpdesk/WebObjects/Helpdesk.woa/ra/Tickets?apiKey={1}'.format(config.whd['host'],
                                                                                             config.whd['apikey'])
        headers = {'content-type': 'application/json'}

        req = urllib2.Request(WhdUrl, jsonMsg, headers)
        try:
            urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            logging.error("HTTP Error: " + str(e))
            return False
        except urllib2.URLError, e:
            logging.error("URLError: " + str(e))
            return False

        return True

    def moveRecord(self, gd_client, record, spreadsheet_key, target_worksheet_id):
        # Write the record to the archival worksheet
        try:
            gd_client.InsertRow(record.content, spreadsheet_key, target_worksheet_id)
        except gdata.service.Error, e:  # I'm not sure if this would catch any InsertRow errors or not
            logging.error("Spreadsheet Record Insert Error: " + str(e))
            return False

        try:
            gd_client.DeleteRow(record.entry)
        except gdata.service.Error, e:  # I'm not sure if this would catch any InsertRow errors or not
            logging.error("Spreadsheet Record Delete Error: " + str(e))
            return False

        return True

if __name__ == "__main__":
    AskATech().run()