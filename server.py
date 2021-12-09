import os
import csv
import time
from csv import writer
from flask import Flask, request, abort
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient
from slack_sdk import WebClient
import server_config as my_config
# instantiate Flask class
app = Flask(__name__)
# tell Flask what URL should trigger function

@app.route("/inbound", methods=['POST'])
def inbound():
    # webhook coming from Twilio > Slack
    if request.method == 'POST':
        print(request.form)
        message_body = request.form['Body']
        message_from = request.form['From']
        # replace with checking if message_from exists in phone_book
        chan_name = search_db(file_name='db.csv', entity_type='phone_number', value=message_from)
        if chan_name == "":
            # send message to Slack user if user is unrecognized
            abort(404)
        # add sleep() function for 1 second for API rate limiting
        time.sleep(1)
        client = WebClient(token=my_config.variables["apps"]["slack_Jashs-Slack-App"]["token"])
        formatted_message = message_from+": "+message_body
        # send message to Slack
        response = client.chat_postMessage(is_private=False, channel=chan_name, text=formatted_message)
        return 'success', 200

    else:
        abort(400)

# helper function
# collection of boolean conditions to validate the incoming API request
def validation(func, req):
    if func == "outbound":
        if "bot_id" in req.json["event"]:
            return False
        if req.json["event"]["channel"] == my_config.variables["channels"]["contact-list"]:
            return False
        if "subtype" in req.json["event"]:
            print("in the subtype if statement")
            if req.json["event"]["subtype"] == "bot_message":
                print("in the bot_message if statement")
            # don't send message back to phone if phone sent it originally
                return False
        return True
    else:
        # in future add more functions
        return True

# helper function
# use csv reader to find desired value when inputting another value from row
# return empty string if cannot find value
def search_db(file_name, entity_type, value):
    if entity_type == "channel":
        phone_to_text = ""
        with open(file_name, newline='') as csv_file:
            phone_book_read = csv.reader(csv_file, delimiter=',')
            for row in phone_book_read:
                if value == row[2]:
                    phone_to_text = row[0]
                    break
        return phone_to_text
    elif entity_type == "phone_number":
        channel_name = ""
        with open(file_name, newline='') as csv_file:
            phone_book_read = csv.reader(csv_file, delimiter=',')
            for row in phone_book_read:
                if value == row[0]:
                    channel_name = row[1]
                    break
        return channel_name

@app.route("/outbound", methods = ['POST'])
def outbound():
    # uses Jash's-Slack-App bot/app
    # webhook going from Slack to Twilio
    # don't allow requests from contact-list channel
    if request.json["event"]["type"] == "message":
    	# if doesn't pass validation, terminate and send 400
        if(not(validation(func="outbound", req=request))):
            abort(400)
        else:
            # print(request.json["event"])
            # print(request.json["event"]["text"])
            phone_to_text = search_db(file_name='db.csv', entity_type='channel', value=request.json["event"]["channel"])
            if phone_to_text == "":
                abort(404)
            # use TwilioHTTPClient because the Twilio API client needs to be told how to connect to the proxy server that free accounts use to access the external Internet.
            proxy_client = TwilioHttpClient(proxy={'http': os.environ['http_proxy'], 'https': os.environ['https_proxy']})
            account_sid = my_config.variables["apps"]["twilio"]["account_sid"]
            auth_token = my_config.variables["apps"]["twilio"]["auth_token"]
            client = Client(account_sid, auth_token, http_client=proxy_client)
            # create and send message to Twilio 
            message = client.messages.create(
                     body=request.json["event"]["text"],
                     from_=my_config.variables["apps"]["twilio"]["phone_number"],
                     to=phone_to_text
                 )
            return 'success', 200
        return 'success', 200

@app.route("/onboard", methods = ['POST'])
def onboard():
    # used by our customer to add end users to phone_book.
    # phone_book is used to determine what channel to send slack messages to, who is sending slack message, slack webhook URL
    # message from API call for onboarding
    # uses onboard-enduser Slack bot/app
    # only allow requests from contact-list channel
    if request.json["event"]["channel"] == my_config.variables["channels"]["contact-list"]:
        print("in the onboard endpoint")
        message = request.json["event"]["text"].split(" ")
        chan_name = message[0]
        phone_num = "+"+message[1]
        check_name = search_db(file_name='db.csv', entity_type='phone_number', value=phone_num)
        if check_name != "":
            abort(404)
        client = WebClient(token=my_config.variables["apps"]["slack_onboard-enduser"]["token"])
        response = client.conversations_create(is_private=False, name=chan_name)
        # print(response)
        with open('db.csv', 'a+', newline='') as csvfile_write:
            phone_book_write = writer(csvfile_write)
            phone_book_write.writerow([phone_num,chan_name,response["channel"]["id"]])


    return 'success', 200

if __name__ == '__main__':
    # for multi-threaded do app.run(threaded=True)
    app.run()
