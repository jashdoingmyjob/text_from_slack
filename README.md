# text_from_slack

## Introduction
**text_from_slack** is a python program that allows Slack users to send messages to phone users by leveraging Twilio's API. Twilio assigns the Slack user a phone number which will serve as a conduit for messages going to and from Slack. 

## Components
- **server.py**: This file is the program's API. You can think of this file as the "mail room" of **text_from_slack**, as it is responsible for directing messages to the appropriate API.
