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

# get device model for using it in API
def get_resource_id(model):
    if model == "lumi.motion.agl02": # motion sensor
        return ["3.1.85"]
    elif model == "lumi.plug.maeu01": # smart plug
        return ["0.13.85"]
    elif model == "lumi.sensor_ht.agl02": # temperature and humidity sensor
        return ["0.3.85", "0.2.85", "0.1.85"]
    elif model == "lumi.magnet.agl02": # door sensor
        return ["3.1.85"]
    elif model == "lumi.sen_ill.agl01": # brightness sensor
        return ["0.3.85"]
    elif model == "lumi.vibration.aq1": # vibration sensor
        return ["13.1.85", "14.1.85"]

# get device data
def get_device_data():
    global token_lst, app_id, app_key, key_id, sensor_lst

    for cnt in range(len(token_lst)):
        access_token = token_lst[cnt][0]
        refresh_token = token_lst[cnt][1]  
        timestamp = str(int(round(time.time() * 1000)))
        nonce = get_random_string(16)
        sign = gen_sign(access_token, app_id, key_id, nonce, timestamp, app_key)
        curl = f""" curl -H "Content-Type":"application/json" -H "Accesstoken:{access_token}" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @device_data.json https://open-cn.aqara.com/v3.0/open/api"""
        print("------------------------ Getting Device Data ---------------------------")
        response = json.loads(os.popen(curl).read())
        device_data = response['result']['data']
        device_df = pd.DataFrame()

        for i in range(len(device_data)):  
            device_data[i]['createTime'] =  datetime.datetime.fromtimestamp(device_data[i]['createTime'] / 1000)
            device_data[i]['updateTime'] =  datetime.datetime.fromtimestamp(device_data[i]['updateTime'] / 1000)
            df = pd.DataFrame(device_data[i], index=[i])
            device_df = pd.concat([device_df, df])

        # today = datetime.date(2023, 5, 9)
        today = datetime.date.today()
        logger.debug(f"Device data: {device_df}")

        try:
            if os.path.isdir(f'./device_data/{today}/'):
                device_df.to_csv(f'./device_data/{today}/Aqara_device_data{cnt+1}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv')
            else:
                os.makedirs(f'./device_data/{today}/')
                device_df.to_csv(f'./device_data/{today}/Aqara_device_data{cnt+1}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv')
        except Exception as e:
            print("error")
            logger.error(f"Error in saving device data: {e}")
        
        # update sensor list
        lst = device_df['did'].values.tolist()
        lst2 = device_df['model'].values.tolist()
        names = device_df['deviceName'].values.tolist()
        lst3 = []
        for i in range(len(lst)):
            if lst2[i] != "lumi.gateway.aqcn03" and lst2[i] != "lumi.sensor_ht.agl02":
                lst3.append([lst[i], lst2[i], names[i]])
        sensor_lst.append(lst3)
        time.sleep(5)

# get sensor data
def get_sensor_data():
    global sensor_lst

    for cnt in range(len(token_lst)):
        access_token = token_lst[cnt][0]
        refresh_token = token_lst[cnt][1]    
        today = datetime.date(2023, 5, 12)
        for i in range(11):
            next_date = today +  datetime.timedelta(3)
            print(today)
            print(next_date)

            for sensors in sensor_lst:
                for sensor in sensors:
                    print(sensor)
                    # yesterday = today - datetime.timedelta(days=3)
                    timestamp = str(int(round(time.time() * 1000)))
                    nonce = get_random_string(16)
                    sign = gen_sign(access_token, app_id, key_id, nonce, timestamp, app_key)
                    data = []
                    json_data = { "intent": "fetch.resource.statistics",
                        "data": {
                            "resources": {
                                "subjectId": f"{sensor[0]}",
                                "resourceIds": get_resource_id(sensor[1])
                            },
                            "startTime": f"{calendar.timegm(today.timetuple()) * 1000 -  32400000}",
                            "endTime": f"{calendar.timegm(next_date.timetuple()) * 1000 -  32400000}",
                            "dimension": "30m",
                            "size": 300
                        }
                    }
                    with open("sensor_data.json", "w") as json_file:
                        json.dump(json_data, json_file)

                    try:
                        curl = f""" curl -H "Content-Type":"application/json" -H "Accesstoken:{access_token}" -H "Appid:{app_id}" -H "Keyid:{key_id}" -H "Nonce:{nonce}" -H "Time:{timestamp}" -H "sign:{sign}" --data @sensor_data.json https://open-cn.aqara.com/v3.0/open/api """
                        print("------------------------ Getting Sensor Data ---------------------------")
                        response = os.popen(curl).read()
                        data = json.loads(response)['result']['data']
                    except Exception as e:
                        print("error")
                        logger.error(f"Error in getting sensor: {e}")

                    df = pd.DataFrame()
                    result = pd.DataFrame()

                    if data != None:
                        for i in reversed(range(len(data))):
                            if data[i]['timeStamp'] != None:
                                data[i]['timeStamp'] =  datetime.datetime.fromtimestamp(data[i]['timeStamp'] / 1000)
                                data[i]['timeStamp'] =  data[i]['timeStamp'].strftime("%m/%d/%Y, %H:%M:%S")

                            data[i]['startTimeZone'] =  datetime.datetime.fromtimestamp(data[i]['startTimeZone'] / 1000)
                            data[i]['startTimeZone'] =  data[i]['startTimeZone'].strftime("%m/%d/%Y, %H:%M:%S")
                            data[i]['endTimeZone'] =  datetime.datetime.fromtimestamp(data[i]['endTimeZone'] / 1000)
                            data[i]['endTimeZone'] =  data[i]['endTimeZone'].strftime("%m/%d/%Y, %H:%M:%S")
                            df = pd.DataFrame(data[i], index=[i])
                            result = pd.concat([result, df])

                        try:
                            if os.path.isdir(f'./sensor_data/{uid_lst[cnt]}/{today}'):
                                filename = f'./sensor_data/{uid_lst[cnt]}/{today}/{sensor[2]}_{sensor[0]}.csv'
                                result.to_csv(filename)
                                print(f"file saved {filename}")
                            else:
                                os.makedirs(f'./sensor_data/{uid_lst[cnt]}/{today}')
                                filename = f'./sensor_data/{uid_lst[cnt]}/{today}/{sensor[2]}_{sensor[0]}.csv'
                                result.to_csv(filename)
                                print(f"file saved {filename}")
                        except Exception as e:
                            print("Error in saving sensor data")
                            logger.error(f"Error in saving sensor data: {e}")
                    time.sleep(6)
            
            # go to next date
            today = next_date
            # today = next_date + datetime.timedelta(1)


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
    # Access Mongodb
    # conn = pymongo.MongoClient("mongodb://pymongo:pymongo@server1.iclab.dev:3001/")
    # db = conn.get_database("testDB")
    # sensor_data_coll = db.get_collection("aqara_sensor_data")
    # device_data_coll = db.get_collection("aqara_device_data")

    while True:
        sensor_lst = []
        get_device_data()
        time.sleep(5)
        for i in range(len(sensor_lst)):
            sensor_lst[i].pop(0)
        get_sensor_data()
        break


if __name__ == "__main__":
    main()