ask-a-tech
==========

Generate Web Help Desk tickets from a Google Spreadsheet

Background
----------

### Problem
[WHD](http://webhelpdesk.com/ "Solarwinds Web Help Desk") (aka "Solarwinds Web Help Desk") makes
creating a ticket
 a simple
task for our employees. Sometimes, however, our employees feel that they have a question that isn't a problem or is too
minor to "bug" tech support. These questions can be like "which word processing programs are available to me," "how many
students are in the District," or "can I access my email from home?"

### Solution
We built a Google Form that collects the employee's username and asks for the non-problem question. The form-response
spreadsheet records the timestamp, username, and the question.

Since the Google Form and WHD are running on two different systems, we need a way to take the Google Form
response and import it into WHD. Ask-a-tech.py script serves as a conduit between our WHD and the Ask-A-Tech Google
Form.

A cronjob on the server runs ask-a-tech.py once every 10 minutes and reads through the default worksheet. If it finds
 any records, it converts those records to JSON and submits them to Web Help Desk via the WHD REST API. Once the
 record is submitted, the record gets moved to the archive worksheet within the form results spreadsheet.

**NOTE:** We are not letting this be an *easier* way to submit tickets when an actual technical problem exists. When
Ask-A-Tech is used by a client for that purpose, the first-level tech we have assigned to Ask-A-Tech tickets replies
back that this appears to be a technical issue and to please submit a ticket. That way, we can track rooms,
buildings, assets, etc.

Requirements
------------
* Python 2.6+ (tested on Python 2.6.6 and 2.7.6)
    * **NOTE:** This has not been used in Python 3+
* Solarwinds Web Help Desk 12+
    * A tech with a [generated API Key](http://www.webhelpdesk.com/api/#auth "How-to generate an API Key in WHD")
* Google Form
    * Google Form requires user login
    * Google Form keeps timestamp
    * Google Form has only one field titled "Question?" (with or without the question mark, upper- or lower-case)
    * An account to use in the script that has "edit" rights to the form response sheet

Instructions
------------
Copy the ask-a-tech.py and config-default.py files to a location on your server. Rename or copy "config-default.py" to
"config.py". Edit "config.py" so that the appropriate fields match your setup.
### Example:
    gapps['email'] = ''
becomes

    gapps['email'] = 'user1@example.com'
and

    whd['apikey'] = ''
becomes

    whd['apikey'] = 'thisIsMyFakeWebHelpDeskAPIKey'
