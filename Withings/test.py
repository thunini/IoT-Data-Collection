import json
import os
import pandas as pd
import datetime  
import time
import logging

# reading input files
def read_input_files():
    global strings
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

# write newly retrieved tokens 
def write_tokens_to_file(access_token, refresh_token, user, cnt):
    global strings
    strings[cnt] = f'{access_token} {refresh_token} {user}\n'
    with open("input.txt", 'w') as file:
        file.writelines(strings)

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
        logging.error(f"Error retrieving access token: {e}, response: {response_data}")

# refresh access token
def refresh_access_token(refresh_token):
    try:
        refresh_command = f"action=requesttoken&grant_type=refresh_token&client_id=a2710e80d27f12767946d35a0fa254e23a1f4a5a395eb5282fd8a15a59a37197&client_secret=c9f2ba094da919bd8c7533177fedffc27b13fdb0a0a39af8ea22d05028735aca&refresh_token={refresh_token}"
        print("----------------- Refreshing Access Token -------------------------")
        retrieve_access_token = f"""curl -d "{refresh_command}" https://wbsapi.withings.net/v2/oauth2"""
        response_data = json.loads(os.popen(retrieve_access_token).read())
        access_token = response_data['body']['access_token']
        refresh_token = response_data['body']['refresh_token']
        return [access_token, refresh_token]
    except Exception as e:
        logging.error(f"Error retrieving refresh token: {e}, response: {response_data}")

# get sleep data by using "getsummary" action API
def get_sleep_data():
    global token_lst, uid_lst
    for cnt in range(len(token_lst)):
        access_token = token_lst[cnt][0]
        refresh_token = token_lst[cnt][1]   
        updated_token_lst = refresh_access_token(refresh_token)
        action = "getsummary" 
        enddate = datetime.date(2023, 8, 28)
        startdate = enddate - datetime.timedelta(days=7)
        enddate, startdate = enddate.strftime('%Y-%m-%d'), startdate.strftime('%Y-%m-%d')
        access_token = updated_token_lst[0]
        refresh_token = updated_token_lst[1]
        token_lst[cnt][0], token_lst[cnt][1] = updated_token_lst[0], updated_token_lst[1]
        write_tokens_to_file(token_lst[cnt][0], token_lst[cnt][1], uid_lst[cnt], cnt)

        # Retrieve Data
        print("----------------- Getting Sleep Data -------------------------")
        try:
            curl = f"""curl --header "Authorization: Bearer {access_token}" --data "action={action}&startdateymd={startdate}&enddateymd={enddate}" https://wbsapi.withings.net/v2/sleep """
            response = json.loads(os.popen(curl).read())
            data = response['body']['series']
        except Exception as e:
            print("error")
            logging.error(f"Error in retrieving sleep data: {e}, uid: {cnt+1}")

        # check if data is empty (no sleep data recorded)
        if data == []:
            empty_data = {"date": [f"{enddate}_{cnt+1}"], "startdate": ["none"], "enddate": ["none"]}
            result = pd.DataFrame(empty_data)

            try:
                if os.path.isdir(f'./sleep_data/{enddate}/'):
                    filename = f'./sleep_data/{enddate}/withings_sleep_data_{uid_lst[cnt]}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv'
                    result.to_csv(filename)
                    logging.debug(f"sleep data file saved: uid {uid_lst[cnt]}")
                else:
                    os.makedirs(f'./sleep_data/{enddate}/')
                    filename = f'./sleep_data/{enddate}/withings_sleep_data_{uid_lst[cnt]}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv'
                    result.to_csv(filename)
                    logging.debug(f"sleep data file saved uid {uid_lst[cnt]}")
            except Exception as e:
                print("error")
                logging.error(f"Error in saving empty sleep data: {e}, uid: {uid_lst[cnt]}")

        else:
            # Preprocess Data and Export as CSV
            result = pd.DataFrame()
            df2 = pd.DataFrame()

            for i in range(len(data)):
                data[i]['startdate'] = datetime.datetime.fromtimestamp(data[i]['startdate']).strftime("%Y-%m-%d %H:%M:S.%f")
                data[i]['enddate'] = datetime.datetime.fromtimestamp(data[i]['enddate']).strftime("%Y-%m-%d %H:%M:S.%f")
                data[i]['created'] = datetime.datetime.fromtimestamp(data[i]['created']).strftime("%Y-%m-%d %H:%M:S.%f")
                data[i]['modified'] = datetime.datetime.fromtimestamp(data[i]['modified']).strftime("%Y-%m-%d %H:%M:S.%f")
                data[i]['date'] = data[i]['date']
                df = pd.DataFrame(data[i], index=[i])
                df = df.drop(columns=['id', 'timezone', 'model', 'model_id', 'hash_deviceid', 'data'])
                result = pd.concat([result, df])

            for j in range(len(data)):
                df = pd.DataFrame(data[j]['data'], index=[j])
                df2 = pd.concat([df2, df])

            result = pd.concat([result, df2], axis=1)


            try:
                if os.path.isdir(f'./sleep_data/{enddate}/'):
                    filename = f'./sleep_data/{enddate}/withings_sleep_data_{uid_lst[cnt]}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv'
                    result.to_csv(filename)
                    logging.debug(f"sleep data file saved uid {uid_lst[cnt]}")
                else:
                    os.makedirs(f'./sleep_data/{enddate}/')
                    filename = f'./sleep_data/{enddate}/withings_sleep_data_{uid_lst[cnt]}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv'
                    result.to_csv(filename)
                    logging.debug(f"sleep data file saved uid {uid_lst[cnt]}")
            except Exception as e:
                print("error")
                logging.error(f"Error in saving sleep data: {e}, uid: {uid_lst[cnt]}")

        time.sleep(7)

# retrieve the device data
def get_device_data():
    global token_lst
    for cnt in range(len(token_lst)):
        print(cnt)
        access_token = token_lst[cnt][0]
        refresh_token = token_lst[cnt][1]    
        updated_token_lst = refresh_access_token(refresh_token)
        access_token = updated_token_lst[0]
        refresh_token = updated_token_lst[1]
        today = datetime.date.today()
        token_lst[cnt][0], token_lst[cnt][1] = updated_token_lst[0], updated_token_lst[1]
        action = "getdevice"

        # get device data from the withings server
        try:
            device_curl = f"""curl --header "Authorization: Bearer {access_token}" --data "action={action}" https://wbsapi.withings.net/v2/user """
            device_response = json.loads(os.popen(device_curl).read())
            device_data = device_response['body']['devices']
        except Exception as e:
            print("error")
            logging.error(f"Error in retrieving device data: {e}, uid: {cnt+1}")
        
        # save device data
        try:
            device_df = pd.DataFrame()
            for i in range(len(device_data)):
                device_data[i]['last_session_date'] =  datetime.datetime.fromtimestamp(device_data[i]['last_session_date'])
                df = pd.DataFrame(device_data[i], index=[i])
                device_df = pd.concat([device_df, df])
            
            # setting for inserting it in mongodb
            users = []
            for k in range(len(device_df.index)):
                users.append(f"user{cnt+1}")
            device_df = device_df.set_index(pd.Series(users))
            device_df = device_df.set_index('deviceid')
            try:
                if os.path.isdir(f'./device_data/{today}/'):
                    device_df.to_csv(f'./device_data/{today}/withings_device_data_{cnt+1}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv')
                    logging.debug(f"device data file saved: uid {cnt+1}")
                else:
                    os.makedirs(f'./device_data/{today}/')
                    device_df.to_csv(f'./device_data/{today}/withings_device_data_{cnt+1}_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv')
                    logging.debug(f"device data file saved: uid {cnt+1}")
            except Exception as e:
                print("error")
                logging.error(f"Error in saving device data: {e}, uid: {cnt+1}")
        except Exception as e:
            print("error")
            logging.error(f"Error in retrieving device data (empty device information): {e}, uid: {cnt+1}")

        time.sleep(7)

# main Function
def main():
    global token_lst, uid_lst
    token_lst, uid_lst = read_input_files()

    while True:
        get_sleep_data()
        time.sleep(3)
        get_device_data()
        time.sleep(3)
        break
    # time.sleep(86400)

if __name__ == "__main__":
    logging.basicConfig(
        filename='withings.log',
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
        level=logging.DEBUG)

    token_lst = []
    main()
