import hashlib
import string
import random
import os
import json
import time
import pandas as pd
import datetime
import calendar
import logging
import subprocess
import requests

# reading input files
def read_input_files():
    inputs = []
    uid = []
    with open("input.txt", "r") as file:
        strings = file.readlines()
        for string in strings:
            line = string.strip()
            line = line.split(" ")
            inputs.append([line[0], line[1]])
            uid.append(line[2])
    return inputs, uid

# write newly retrieved tokens to input.txt
def write_tokens_to_file(access_token, refresh_token, user, cnt):
    global strings
    strings[cnt] = f'{access_token} {refresh_token} {user}\n'
    with open("input.txt", 'w') as file:
        file.writelines(strings)

# generate signature
def gen_sign(
    access_token: str,
    app_id: str,
    key_id: str,
    nonce: str,
    timestamp: str,
    app_key: str,
):
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

# get device model for using it in API
def get_resource_id(model):
    if model == "lumi.motion.agl02": # motion sensor
        return ["3.1.85"]
    elif model == "lumi.plug.maeu01": # smart plug
        return ["0.12.85", "0.13.85"]
    elif model == "lumi.sensor_ht.agl02": # temperature and humidity sensor
        return ["0.3.85", "0.2.85", "0.1.85"]
    elif model == "lumi.magnet.agl02": # door sensor
        return ["3.1.85"]
    elif model == "lumi.sen_ill.agl01": # brightness sensor
        return ["0.3.85"]
    elif model == "lumi.vibration.aq1": # vibration sensor
        return ["13.1.85"]

# refresh access token
def refresh_access_token(access_token, refresh_token):
    global token_lst, app_id, app_key, key_id

    timestamp = str(int(round(time.time() * 1000)))
    nonce = get_random_string(16)
    sign = gen_sign(access_token, app_id, key_id, nonce, timestamp, app_key)

    refresh_json = {
        "intent": "config.auth.refreshToken",
        "data": {
            "refreshToken": f"{refresh_token}"
        }
    }

    with open("refresh_data.json", "w") as json_file:
        json.dump(refresh_json, json_file)

    try:
        curl = f""" curl -H "Content-Type":"application/json" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @refresh_data.json https://open-cn.aqara.com/v3.0/open/api """
        response = subprocess.check_output(curl, shell=True, encoding='utf-8')
        response_data = json.loads(response)
        print(response_data)
        new_access_token = response_data['result']['accessToken']
        new_refresh_token = response_data['result']['refreshToken']
        time.sleep(2)
        return [new_access_token, new_refresh_token]
    except Exception as e:
        logger.error(f"Error in getting sensor data: {e}")
        return []


# get device data
def get_device_data():
    global token_lst, app_id, app_key, key_id, sensor_lst
    for cnt in range(len(token_lst)):
        access_token = token_lst[cnt][0]
        timestamp = str(int(round(time.time() * 1000)))
        nonce = get_random_string(16)
        sign = gen_sign(access_token, app_id, key_id, nonce, timestamp, app_key)

        device_data = []
        device_df = pd.DataFrame()
        curl = f""" curl -H "Content-Type":"application/json" -H "Accesstoken:{access_token}" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @device_data.json https://open-cn.aqara.com/v3.0/open/api"""

        try:
            response = subprocess.check_output(curl, shell=True, encoding='utf-8')
            response_data = json.loads(response)
            device_data = response_data['result']['data']
        except Exception as e:
            print("Error in getting device data with curl")
            logger.error(f"Error in getting device data with curl: {e}")

        for i in range(len(device_data)):
            device_data[i]['createTime'] =  datetime.datetime.fromtimestamp(device_data[i]['createTime'] / 1000)
            device_data[i]['updateTime'] =  datetime.datetime.fromtimestamp(device_data[i]['updateTime'] / 1000)
            df = pd.DataFrame(device_data[i], index=[i])
            device_df = pd.concat([device_df, df])

        today = datetime.date.today()
        logger.debug(f"Device data: {device_df}")
        try:
            if os.path.isdir(f'./device_data/{today}/'):
                device_df.to_csv(f'./device_data/{today}/{uid_lst[cnt]}_devices.csv')
            else:
                os.makedirs(f'./device_data/{today}/')
                device_df.to_csv(f'./device_data/{today}/{uid_lst[cnt]}_devices.csv')
        except Exception as e:
            print("error")
            logger.error(f"Error in saving device data: {e}")
            
        # update sensor list
        lst = device_df['did'].values.tolist()
        lst2 = device_df['model'].values.tolist()
        names = device_df['deviceName'].values.tolist()
        lst3 = []
        for i in range(len(lst)):
            if lst2[i].strip() != "lumi.gateway.aqcn03":
                lst3.append([lst[i], lst2[i], names[i]])
        sensor_lst.append(lst3)
        time.sleep(3)

# read device data from pre-downloaded excel
def get_device_data_from_excel():
    global token_lst, app_id, app_key, key_id, sensor_lst
    for cnt in range(len(token_lst)):
        device_df = pd.read_csv(f'device_data/{uid_lst[cnt]}_devices.csv')
        lst = device_df['did'].values.tolist()
        lst2 = device_df['model'].values.tolist()
        names = device_df['deviceName'].values.tolist()
        lst3 = []
        for i in range(len(lst)):
            if lst2[i].strip() != "lumi.gateway.aqcn03":
                lst3.append([lst[i], lst2[i], names[i]])
        sensor_lst.append(lst3)

# get data history for data types that exceed size 300 by iteration
def get_data_history_iter(access_token, sensor, cnt, today, today_date, iter, hour):
    next_date = today + datetime.timedelta(hours=hour)
    for count in range(iter):
        timestamp = str(int(round(time.time() * 1000)))
        nonce = get_random_string(16)
        sign = gen_sign(access_token, app_id, key_id, nonce, timestamp, app_key)
        data = []
        today_timestamp = calendar.timegm(today.timetuple()) * 1000
        next_date_timestamp = calendar.timegm(next_date.timetuple()) * 1000

        json_data = { "intent": "fetch.resource.history",
            "data": {
                "subjectId": f"{sensor[0]}",
                "resourceIds": get_resource_id(sensor[1]),
                "startTime": f"{today_timestamp - 32400000}",
                "endTime": f"{next_date_timestamp - 32400000}",
                "size": 300
            }
        }
        today = next_date
        next_date = today + datetime.timedelta(hours=12)
        with open("sensor_data.json", "w") as json_file:
            json.dump(json_data, json_file)
        try:
            curl = f""" curl -H "Content-Type":"application/json" -H "Accesstoken:{access_token}" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @sensor_data.json https://open-cn.aqara.com/v3.0/open/api """
            print("------------------------ Getting Sensor Data ---------------------------")
            response = subprocess.check_output(curl, shell=True, encoding='utf-8')
            response_data = json.loads(response)
            data = response_data['result']['data']
        except Exception as e:
            print("Error in getting sensor data")
            logger.error(f"Error in getting sensor data: {e}")
        df = pd.DataFrame()
        result = pd.DataFrame()
        if data != None:
            for i in reversed(range(len(data))):
                if data[i]['timeStamp'] != None:
                    data[i]['timeStamp'] =  datetime.datetime.fromtimestamp(data[i]['timeStamp'] / 1000)
                    data[i]['timeStamp'] =  data[i]['timeStamp'].strftime("%m/%d/%Y, %H:%M:%S")
                df = pd.DataFrame(data[i], index=[i])
                result = pd.concat([result, df])
            try:
                if os.path.isdir(f'./sensor_data/{uid_lst[cnt]}/{today_date}'):
                    filename = f'./sensor_data/{uid_lst[cnt]}/{today_date}/{sensor[2]}_{sensor[0]}_{count}.csv'
                    result.to_csv(filename)
                    print(f"file saved {filename}")
                else:
                    os.makedirs(f'./sensor_data/{uid_lst[cnt]}/{today_date}')
                    filename = f'./sensor_data/{uid_lst[cnt]}/{today_date}/{sensor[2]}_{sensor[0]}_{count}.csv'
                    result.to_csv(filename)
                    print(f"file saved {filename}")
            except Exception as e:
                print("Error in saving sensor data")
                logger.error(f"Error in saving sensor data: {e}")
        
        time.sleep(4)

# get sensor data
def get_sensor_data(year, month, day):
    global sensor_lst
    for cnt in range(len(token_lst)):
        access_token = token_lst[cnt][0]
        refresh_token = token_lst[cnt][1]
        today_date = datetime.date(year, month, day) - datetime.timedelta(2)
        for sensor in sensor_lst[cnt]:

            today = datetime.datetime(year, month, day, 0, 0) - datetime.timedelta(2)
            next_date = datetime.datetime(year, month, day, 0, 0)
            
            # cut endtime - start time to 12 hours for env and 4 hours for smart plug
            if sensor[1] == "lumi.sen_ill.agl01":
                get_data_history_iter(access_token, sensor, cnt, today, today_date, 3, 12)
            elif sensor[1] == "lumi.plug.maeu01":
                get_data_history_iter(access_token, sensor, cnt, today, today_date, 9, 4)
            else:
                timestamp = str(int(round(time.time() * 1000)))
                nonce = get_random_string(16)
                sign = gen_sign(access_token, app_id, key_id, nonce, timestamp, app_key)
                data = []
                json_data = { "intent": "fetch.resource.history",
                    "data": {
                        "subjectId": f"{sensor[0]}",
                        "resourceIds": get_resource_id(sensor[1]),
                        "startTime": f"{calendar.timegm(today.timetuple()) * 1000 -  32400000}",
                        "endTime": f"{calendar.timegm(next_date.timetuple()) * 1000 -  32400000}",
                        "size": 300
                    }
                }
                with open("sensor_data.json", "w") as json_file:
                    json.dump(json_data, json_file)
                try:
                    curl = f""" curl -H "Content-Type":"application/json" -H "Accesstoken:{access_token}" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @sensor_data.json https://open-cn.aqara.com/v3.0/open/api """
                    response = subprocess.check_output(curl, shell=True, encoding='utf-8')
                    response_data = json.loads(response)
                    data = response_data['result']['data']
                except Exception as e:
                    print("Error in getting sensor data")
                    logger.error(f"Error in getting sensor data: {e}")
                df = pd.DataFrame()
                result = pd.DataFrame()
                if data != None:
                    for i in reversed(range(len(data))):
                        if data[i]['timeStamp'] != None:
                            data[i]['timeStamp'] =  datetime.datetime.fromtimestamp(data[i]['timeStamp'] / 1000)
                            data[i]['timeStamp'] =  data[i]['timeStamp'].strftime("%m/%d/%Y, %H:%M:%S")
                        df = pd.DataFrame(data[i], index=[i])
                        result = pd.concat([result, df])
                    try:
                        if os.path.isdir(f'./sensor_data/{uid_lst[cnt]}/{today_date}'):
                            filename = f'./sensor_data/{uid_lst[cnt]}/{today_date}/{sensor[2]}_{sensor[0]}.csv'
                            result.to_csv(filename)
                            print(f"file saved {filename}")
                        else:
                            os.makedirs(f'./sensor_data/{uid_lst[cnt]}/{today_date}')
                            filename = f'./sensor_data/{uid_lst[cnt]}/{today_date}/{sensor[2]}_{sensor[0]}.csv'
                            result.to_csv(filename)
                            print(f"file saved {filename}")
                    except Exception as e:
                        print("Error in saving sensor data")
                        logger.error(f"Error in saving sensor data: {e}")
            time.sleep(4)

        # go to next UID
        cnt += 1
        
# main function
def main():
    global token_lst, app_id, app_key, key_id, sensor_lst, logger, uid_lst
    timestamp = datetime.datetime.now()
    logging.basicConfig(
        filename=f'logs/aqara.log_{timestamp}',
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
        level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    token_lst = []
    sensor_lst = []
    app_id = "1082333016935813120e603a"
    app_key = "9b4otxco3vq06z0c6fqfb30da1mt05l1"
    key_id = "K.1082333016981950466"
    token_lst, uid_lst = read_input_files()
    year = int(input("Enter year: "))
    month = int(input("Enter month: "))
    day = int(input("Enter day: "))

    # for user in range(len(token_lst)):
    #     [new_access_token, new_refresh_token] = refresh_access_token(token_lst[user][0], token_lst[user][1])
    #     token_lst.append([new_access_token, new_refresh_token])
    #     write_tokens_to_file(new_access_token, new_refresh_token, uid_lst[user], user)

    

    while True:
        sensor_lst = []
        # get_device_data()
        get_device_data_from_excel()
        time.sleep(1)
        get_sensor_data(year, month, day)
        # send Slack notification
        # curl = """ curl -X POST -H 'Content-type: application/json' --data '{"text":"Finished collecting Aqara sensor data"}' https://hooks.slack.com/services/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 """
        # subprocess.check_output(curl, shell=True, encoding='utf-8')
        break

if __name__ == "__main__":
    main()