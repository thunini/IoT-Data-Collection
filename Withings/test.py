# Import Libraries
import json
import os
import pandas as pd
import datetime  
import time
import pymongo
import logging
from multiprocessing import Process

# reading input files
def read_input_files():
    inputs = []
    with open("input.txt", "r") as file:
        strings = file.readlines()
        for string in strings:
            inputs.append(string.strip())
    return inputs

# retrieve access token
def get_access_token(code):
    try:
        command = f"action=requesttoken&grant_type=authorization_code&client_id=a2710e80d27f12767946d35a0fa254e23a1f4a5a395eb5282fd8a15a59a37197&client_secret=c9f2ba094da919bd8c7533177fedffc27b13fdb0a0a39af8ea22d05028735aca&code={code}&redirect_uri=https://wbsapi.withings.net"
        retrieve_access_token = f"""curl -d "{command}" https://wbsapi.withings.net/v2/oauth2"""
        response_data = json.loads(os.popen(retrieve_access_token).read())
        access_token = response_data['body']['access_token']
        refresh_token = response_data['body']['refresh_token']
        return [access_token, refresh_token]
    except Exception as e:
        logging.error(f"Error retrieving access token: {e}")

# refresh access token
def refresh_access_token(refresh_token):
    try:
        refresh_command = f"action=requesttoken&grant_type=refresh_token&client_id=a2710e80d27f12767946d35a0fa254e23a1f4a5a395eb5282fd8a15a59a37197&client_secret=c9f2ba094da919bd8c7533177fedffc27b13fdb0a0a39af8ea22d05028735aca&refresh_token={refresh_token}"
        retrieve_access_token = f"""curl -d "{refresh_command}" https://wbsapi.withings.net/v2/oauth2"""
        response_data = json.loads(os.popen(retrieve_access_token).read())
        access_token = response_data['body']['access_token']
        refresh_token = response_data['body']['refresh_token']
        return [access_token, refresh_token]
    except Exception as e:
        logging.error(f"Error retrieving refresh token: {e}")

# get sleep data by using "getsummary" action API
def get_sleep_data(code, refresh_token):
    if is_first_access:
        token_lst = get_access_token(code)
        is_first_access = False
    else:
        token_lst = refresh_access_token(refresh_token)

    access_token = token_lst[0]
    refresh_token = token_lst[1]   
    action = "getsummary" 

    # Retrieve Data
    curl = f"""curl --header "Authorization: Bearer {access_token}" --data "action={action}&startdateymd={startdate}&enddateymd={enddate}" https://wbsapi.withings.net/v2/sleep """
    response = json.loads(os.popen(curl).read())
    data = response['body']['series']

    # Preprocess Data and Export as CSV
    result = pd.DataFrame()
    df2 = pd.DataFrame()

    for i in range(len(data)):
        data[i]['startdate'] = datetime.datetime.fromtimestamp(data[i]['startdate']).strftime("%Y-%m-%d %H:%M:S.%f")
        data[i]['enddate'] = datetime.datetime.fromtimestamp(data[i]['enddate']).strftime("%Y-%m-%d %H:%M:S.%f")
        data[i]['created'] = datetime.datetime.fromtimestamp(data[i]['created']).strftime("%Y-%m-%d %H:%M:S.%f")
        data[i]['modified'] = datetime.datetime.fromtimestamp(data[i]['modified']).strftime("%Y-%m-%d %H:%M:S.%f")
        df = pd.DataFrame(data[i], index=[i])
        df = df.drop(columns=['id', 'timezone', 'model', 'model_id', 'hash_deviceid', 'data'])
        result = pd.concat([result, df])

    for j in range(len(data)):
        df = pd.DataFrame(data[j]['data'], index=[j])
        df2 = pd.concat([df2, df])

    result = pd.concat([result, df2], axis=1)
    result = result.set_index('date')
    dict_result = result.to_dict()
    # coll.insert_one(dict_result)
    result.to_csv('./withings_sleep_data.csv')
    print(refresh_token)

def get_device_data(refresh_token):
    token_lst = refresh_access_token(refresh_token)
    access_token = token_lst[0]
    refresh_token = token_lst[1]  

    action = "getdevice"
    device_curl = f"""curl --header "Authorization: Bearer {access_token}" --data "action={action}" https://wbsapi.withings.net/v2/user """
    device_response = json.loads(os.popen(device_curl).read())
    device_data = device_response['body']['devices']
    device_df = pd.DataFrame()
    for i in range(len(device_data)):
        device_data[i]['last_session_date'] =  datetime.datetime.fromtimestamp(device_data[i]['last_session_date'])
        df = pd.DataFrame(device_data[i], index=[i])
        device_df = pd.concat([device_df, df])

    device_df.to_csv('./withings_device_data.csv')
    print(refresh_token)
    time.sleep(86400)

# Main Function
def main():
    # API Actions
    inputs = read_input_files()
    # refresh_token = os.environ.get('INITIAL_CODE')
    code = inputs[0]
    startdate = inputs[1]
    enddate = inputs[2]
    is_first_access = True  
    token_lst = []
    access_token = ''
    # refresh_token = inputs[0]

    # Access Mongodb
    conn = pymongo.MongoClient("mongodb://pymongo:pymongo@server1.iclab.dev:3001/")
    db = conn.get_database("testDB")
    coll = db.get_collection("data")

    while True:
        for user in inputs:
            get_sleep_data(code)
            time.sleep(15)
            get_device_data()
            time.sleep(86400)

if __name__ == "__main__":
    logging.basicConfig(filename='withings_token.log', level=logging.ERROR)
    main()
