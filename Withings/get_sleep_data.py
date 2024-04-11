import json
import os
import pandas as pd
import datetime  
import time
import logging

# Function for reading input files
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

# Function for writing newly retrieved access tokens
def write_tokens_to_file(access_token, refresh_token, user, cnt):
    global strings
    strings[cnt] = f'{access_token} {refresh_token} {user}\n'
    with open("input.txt", 'w') as file:
        file.writelines(strings)

# Function for retrieving access tokens
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

# Function for refreshing access token
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

# Function for getting sleep data by using "getsummary" action API
def get_sleep_data():
    global token_lst, uid_lst
    for cnt in range(len(token_lst)):
        # Get access tokens
        access_token = token_lst[cnt][0]
        refresh_token = token_lst[cnt][1]   
        updated_token_lst = refresh_access_token(refresh_token)
        access_token = updated_token_lst[0]
        refresh_token = updated_token_lst[1]
        token_lst[cnt][0], token_lst[cnt][1] = updated_token_lst[0], updated_token_lst[1]
        write_tokens_to_file(token_lst[cnt][0], token_lst[cnt][1], uid_lst[cnt], cnt)

        # Variables for API header
        action = "getsummary" 
        enddate = datetime.date(2024, 1, 21)
        startdate = datetime.date(2023, 8, 1)
        # enddate = datetime.date(2023, 6, 21)
        # startdate = datetime.date(2023, 5, 1)
        enddate, startdate = enddate.strftime('%Y-%m-%d'), startdate.strftime('%Y-%m-%d')
        data_fields = "nb_rem_episodes,sleep_efficiency,sleep_latency,total_sleep_time,total_timeinbed,wakeup_latency,waso,asleepduration,hr_average,hr_max,hr_min,lightsleepduration,night_events,out_of_bed_count,remsleepduration,rr_average,rr_max,rr_min,sleep_score,snoring,snoringepisodecount,wakeupcount,wakeupduration"

        # Retrieve Data
        print("----------------- Getting Sleep Data -------------------------")
        try:
            curl = f"""curl --header "Authorization: Bearer {access_token}" --data "action={action}&startdateymd={startdate}&enddateymd={enddate}&data_fields={data_fields}" https://wbsapi.withings.net/v2/sleep """
            response = json.loads(os.popen(curl).read())
            data = response['body']['series']
        except Exception as e:
            print("error")
            logging.error(f"Error in retrieving sleep data: {e}, uid: {cnt+1}")

        # Check if data is empty (no sleep data recorded)
        if data == []:
            empty_data = {"date": [f"{enddate}_{cnt+1}"], "startdate": ["none"], "enddate": ["none"]}
            result = pd.DataFrame(empty_data)
            # Save empty dataframe
            try:
                if os.path.isdir(f'./sleep_data/{uid_lst[cnt]}/{enddate}/'):
                    filename = f'./sleep_data/{uid_lst[cnt]}/{enddate}/withings_sleep_data_{uid_lst[cnt]}.csv'
                    result.to_csv(filename)
                    logging.debug(f"Empty sleep data file saved: uid {uid_lst[cnt]}")
                else:
                    os.makedirs(f'./sleep_data/{uid_lst[cnt]}/{enddate}/')
                    filename = f'./sleep_data/{uid_lst[cnt]}/{enddate}/withings_sleep_data_{uid_lst[cnt]}.csv'
                    result.to_csv(filename)
                    logging.debug(f"Empty sleep data file saved uid {uid_lst[cnt]}")
            except Exception as e:
                print("error")
                logging.error(f"Error in saving empty sleep data: {e}, uid: {uid_lst[cnt]}")

        else:
            # Preprocess Data and Export as CSV
            result = pd.DataFrame()
            df2 = pd.DataFrame()

            for i in range(len(data)):
                data[i]['startdate'] = datetime.datetime.fromtimestamp(data[i]['startdate']).strftime("%Y-%m-%d %H:%M:%S")
                data[i]['enddate'] = datetime.datetime.fromtimestamp(data[i]['enddate']).strftime("%Y-%m-%d %H:%M:%S")
                data[i]['created'] = datetime.datetime.fromtimestamp(data[i]['created']).strftime("%Y-%m-%d %H:%M:%S")
                data[i]['modified'] = datetime.datetime.fromtimestamp(data[i]['modified']).strftime("%Y-%m-%d %H:%M:%S")
                data[i]['date'] = data[i]['date']
                df = pd.DataFrame(data[i], index=[i])
                df = df.drop(columns=['data'])
                result = pd.concat([result, df])

            for j in range(len(data)):
                df = pd.DataFrame(data[j]['data'], index=[j])
                df2 = pd.concat([df2, df])

            result = pd.concat([result, df2], axis=1)


            try:
                if os.path.isdir(f'./sleep_data/{uid_lst[cnt]}/{enddate}/'):
                    filename = f'./sleep_data/{uid_lst[cnt]}/{enddate}/withings_sleep_data_{uid_lst[cnt]}.csv'
                    result.to_csv(filename)
                    logging.debug(f"Sleep data file saved uid {uid_lst[cnt]}")
                else:
                    os.makedirs(f'./sleep_data/{uid_lst[cnt]}/{enddate}/')
                    filename = f'./sleep_data/{uid_lst[cnt]}/{enddate}/withings_sleep_data_{uid_lst[cnt]}.csv'
                    result.to_csv(filename)
                    logging.debug(f"Sleep data file saved uid {uid_lst[cnt]}")
            except Exception as e:
                print("error")
                logging.error(f"Error in saving sleep data: {e}, uid: {uid_lst[cnt]}")

        time.sleep(3)

# Function for retrieving the device data
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

        # Get device data from the withings server
        try:
            device_curl = f"""curl --header "Authorization: Bearer {access_token}" --data "action={action}" https://wbsapi.withings.net/v2/user """
            device_response = json.loads(os.popen(device_curl).read())
            device_data = device_response['body']['devices']
        except Exception as e:
            print("error")
            logging.error(f"Error in retrieving device data: {e}, uid: {cnt+1}")
        
        # Save device data
        try:
            device_df = pd.DataFrame()
            for i in range(len(device_data)):
                device_data[i]['last_session_date'] =  datetime.datetime.fromtimestamp(device_data[i]['last_session_date'])
                df = pd.DataFrame(device_data[i], index=[i])
                device_df = pd.concat([device_df, df])
            

            try:
                if os.path.isdir(f'./device_data/{today}/'):
                    device_df.to_csv(f'./device_data/{today}/withings_device_data_{cnt+1}.csv')
                    logging.debug(f"device data file saved: uid {cnt+1}")
                else:
                    os.makedirs(f'./device_data/{today}/')
                    device_df.to_csv(f'./device_data/{today}/withings_device_data_{cnt+1}.csv')
                    logging.debug(f"device data file saved: uid {cnt+1}")
            except Exception as e:
                print("error")
                logging.error(f"Error in saving device data: {e}, uid: {cnt+1}")
        except Exception as e:
            print("error")
            logging.error(f"Error in retrieving device data (empty device information): {e}, uid: {cnt+1}")

        time.sleep(3)

# Main function
def main():
    global token_lst, uid_lst

    # Set up logging 
    logging.basicConfig(
        filename='withings.log',
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
        level=logging.DEBUG
    )
    
    # Read token list
    token_lst = []
    token_lst, uid_lst = read_input_files()

    get_sleep_data()
    # get_device_data()

if __name__ == "__main__":
    main()