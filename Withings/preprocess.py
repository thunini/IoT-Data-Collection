import json
import os
import pandas as pd
import datetime  
import time

# Function for merging sleep data
def merge_data(uid_lst):
    # Iterate through all users
    for cnt in range(len(uid_lst)):
        directory_path = f'./sleep_data/{uid_lst[cnt]}'
        folders = [folder for folder in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, folder))]
        df = pd.DataFrame()

        # Iterate through all folers inside each user directory
        for folder in folders:
            path = f'./sleep_data/{uid_lst[cnt]}/{folder}'
            sensor_files = os.listdir(path)

            for fol in sensor_files:
                data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                frames1 = [df, data]
                df = pd.concat(frames1)
        
        df = df.sort_values(by='startdate')
        df = df.drop('Unnamed: 0', axis=1)
        df.to_csv(f"./sleep_data/UID{uid_lst[cnt]}.csv")




# Main function
def main():
    uid_lst = [1,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
    merge_data(uid_lst)

    

if __name__ == "__main__":
    main()
