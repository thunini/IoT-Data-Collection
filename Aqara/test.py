import hashlib
import string
import random
import os
import json
import time
import pandas as pd
import datetime  
import logging

# reading input files
def read_input_files():
    inputs = []
    with open("input.txt", "r") as file:
        strings = file.readlines()
        for string in strings:
            line = string.strip()
            line = line.split(" ")
            inputs.append(line)
    return inputs

# generate signature
def gen_sign(
    access_token: str,
    app_id: str,
    key_id: str,
    nonce: str,
    timestamp: str,
    app_key: str,
):
    """Signature in headers, see https://opendoc.aqara.cn/docs/%E4%BA%91%E5%AF%B9%E6%8E%A5%E5%BC%80%E5%8F%91%E6%89%8B%E5%86%8C/API%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97/Sign%E7%94%9F%E6%88%90%E8%A7%84%E5%88%99.html"""
    s = f"Appid={app_id}&Keyid={key_id}&Nonce={nonce}&Time={timestamp}{app_key}"
    if access_token and len(access_token) > 0:
        s = f"AccessToken={access_token}&{s}"
    s = s.lower()
    sign = hashlib.md5(s.encode("utf-8")).hexdigest()
    return sign

# generate random string for oauth 2.0
def get_random_string(length: int):
    seq = string.ascii_uppercase + string.digits
    return "".join((random.choice(seq) for _ in range(length)))

# get device data
def get_device_data():
    global token_lst, app_id, app_key, key_id

    for cnt in range(len(token_lst)):
        access_token = token_lst[cnt][0]
        refresh_token = token_lst[cnt][1]    
        timestamp = str(int(round(time.time() * 1000)))
        nonce = get_random_string(16)
        sign = gen_sign(access_token, app_id, key_id, nonce, timestamp, app_key)
        curl = f""" curl -H "Content-Type":"application/json" -H "Accesstoken:{access_token}" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @device_data.json https://open-kr.aqara.com/v3.0/open/api """
        response = json.loads(os.popen(curl).read())
        device_data = response['result']['data']
        device_df = pd.DataFrame()

        for i in range(len(device_data)):  
            device_data[i]['createTime'] =  datetime.datetime.fromtimestamp(device_data[i]['createTime'] / 1000)
            device_data[i]['updateTime'] =  datetime.datetime.fromtimestamp(device_data[i]['updateTime'] / 1000)
            df = pd.DataFrame(device_data[i], index=[i])
            device_df = pd.concat([device_df, df])

        print(device_df)
        time.sleep(5)

def get_sensor_data():
    token_lst = read_input_files()
    
    for cnt in range(len(token_lst)):
        access_token = token_lst[cnt][0]
        refresh_token = token_lst[cnt][1]    
        timestamp = str(int(round(time.time() * 1000)))
        nonce = get_random_string(16)
        sign = gen_sign(access_token, app_id, key_id, nonce, timestamp, app_key)
        print(access_token, timestamp, nonce, sign)
        data = []
        # try:
        #     curl = f""" curl -H "Content-Type":"application/json" -H "Accesstoken:{access_token}" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @device_data.json https://open-kr.aqara.com/v3.0/open/api """
        #     response = os.popen(curl).read()
        #     data = json.loads(response)['result']['data']
        # except Exception as e:
        #     print("error")
        #     logging.error(f"Error in getting sensor: {e}")
        curl = f""" curl -H "Content-Type":"application/json" -H "Accesstoken:{access_token}" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @device_data.json https://open-kr.aqara.com/v3.0/open/api """
        response = json.loads(os.popen(curl).read())
        data = response['result']['data']
        
        print(data)
        df = pd.DataFrame()
        df2 = pd.DataFrame()

        for i in reversed(range(len(data))):
            data[i]['timeStamp'] =  datetime.datetime.fromtimestamp(data[i]['timeStamp'] / 1000)
            data[i]['startTimeZone'] =  datetime.datetime.fromtimestamp(data[i]['startTimeZone'] / 1000)
            data[i]['endTimeZone'] =  datetime.datetime.fromtimestamp(data[i]['endTimeZone'] / 1000)
            df = df.append(data[i], ignore_index=True)

        print(df)
        time.sleep(10)
        
# main function
def main():
    global token_lst, app_id, app_key, key_id
    token_lst = read_input_files()
    # Access Mongodb
    # conn = pymongo.MongoClient("mongodb://pymongo:pymongo@server1.iclab.dev:3001/")
    # conn = pymongo.MongoClient()
    # db = conn.get_database("testDB")
    # sleep_data_coll = db.get_collection("sleep_data")
    # device_data_coll = db.get_collection("device_data")

    while True:
        get_device_data()




if __name__ == "__main__":
    logging.basicConfig(filename='aqara_token.log', level=logging.ERROR)
    token_lst = []
    app_id = "1082333016935813120e603a"
    app_key = "cbr154t51kdin7eewqbutbiwdw8k4isy"
    key_id = "K.1082333016981950464"
    main()