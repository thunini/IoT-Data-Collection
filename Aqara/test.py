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
    global token_lst, app_id, app_key, key_id, sensor_lst

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

        today = datetime.date.today()
        try:
            if os.path.isdir(f'./device_data/{today}/'):
                device_df.to_csv(f'./device_data/{today}/Aqara_device_data{cnt}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv')
            else:
                os.makedirs(f'./device_data/{today}/')
                device_df.to_csv(f'./device_data/{today}/Aqara_device_data{cnt}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv')
        except Exception as e:
            print("error")
            logging.error(f"Error in saving device data: {e}")
        
        # update sensor list
        lst = device_df['did'].values.tolist()
        sensor_lst.append(lst)
        time.sleep(10)

# get sensor data
def get_sensor_data():
    for cnt in range(len(token_lst)):
        access_token = token_lst[cnt][0]
        refresh_token = token_lst[cnt][1]    
        
        for sensors in sensor_lst:
            for sensor in sensors:
                print(sensor)
                timestamp = str(int(round(time.time() * 1000)))
                nonce = get_random_string(16)
                sign = gen_sign(access_token, app_id, key_id, nonce, timestamp, app_key)
                data = []
                json_data = { "intent": "fetch.resource.statistics",
                    "data": {
                        "resources": {
                            "subjectId": f"{sensor}"
                        },
                        "startTime": "1680912000000",
                        "dimension": "30m"
                    }
                }
                with open("sensor_data.json", "w") as json_file:
                    json.dump(json_data, json_file)

                try:
                    curl = f""" curl -H "Content-Type":"application/json" -H "Accesstoken:{access_token}" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @sensor_data.json https://open-kr.aqara.com/v3.0/open/api """
                    response = os.popen(curl).read()
                    data = json.loads(response)['result']['data']
                except Exception as e:
                    print("error")
                    logging.error(f"Error in getting sensor: {e}")

                df = pd.DataFrame()
                result = pd.DataFrame()
                print(data)

                if data != None:
                    for i in reversed(range(len(data))):
                        data[i]['timeStamp'] =  datetime.datetime.fromtimestamp(data[i]['timeStamp'] / 1000)
                        data[i]['startTimeZone'] =  datetime.datetime.fromtimestamp(data[i]['startTimeZone'] / 1000)
                        data[i]['endTimeZone'] =  datetime.datetime.fromtimestamp(data[i]['endTimeZone'] / 1000)
                        df = pd.DataFrame(data[i], index=[i])
                        result = pd.concat([result, df])

                    today = datetime.date.today()
                    try:
                        if os.path.isdir(f'./sensor_data/{today}/'):
                            filename = f'./sensor_data/{today}/Aqara_sensor_data{cnt}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv'
                            result.to_csv(filename)
                            print("file saved")
                        else:
                            os.makedirs(f'./sensor_data/{today}/')
                            filename = f'./sensor_data/{today}/Aqara_sensor_data{cnt}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv'
                            result.to_csv(filename)
                            print("file saved")
                    except Exception as e:
                        print("error")
                        logging.error(f"Error in saving sleep data: {e}")
                time.sleep(10)
        
# main function
def main():
    global token_lst, app_id, app_key, key_id, sensor_lst
    token_lst = read_input_files()
    # Access Mongodb
    # conn = pymongo.MongoClient("mongodb://pymongo:pymongo@server1.iclab.dev:3001/")
    # conn = pymongo.MongoClient()
    # db = conn.get_database("testDB")
    # sleep_data_coll = db.get_collection("sleep_data")
    # device_data_coll = db.get_collection("device_data")

    while True:
        get_device_data()
        time.sleep(5)
        for i in range(len(sensor_lst)):
            sensor_lst[i].pop(0)

        time.sleep(10)
        get_sensor_data()




if __name__ == "__main__":
    logging.basicConfig(filename='aqara_token.log', level=logging.ERROR)
    token_lst = []
    sensor_lst = []
    app_id = "1082333016935813120e603a"
    app_key = "cbr154t51kdin7eewqbutbiwdw8k4isy"
    key_id = "K.1082333016981950464"
    main()