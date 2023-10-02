import pandas as pd
import os

def main():
    uid_lst = [1,3,4,5,6,7,8,9,10,11,12,13,15,17,18,19,20]

    # get data from each files
    for cnt in range(len(uid_lst)):
        env_df = pd.DataFrame()
        door_df = pd.DataFrame()
        brightness_df = pd.DataFrame()
        plug_df = pd.DataFrame()
        microwave_df = pd.DataFrame()
        chair_df = pd.DataFrame()
        cleaner_df = pd.DataFrame()
        washer_df = pd.DataFrame()
        fridge_df = pd.DataFrame()
        motion_df = pd.DataFrame()
        user = cnt+1

        directory_path = f'./sensor_data/{uid_lst[cnt]}'
        folders = [folder for folder in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, folder))]

        for folder in folders:
            path = f'./sensor_data/{uid_lst[cnt]}/{folder}'
            sensor_files = os.listdir(path)
            for fol in sensor_files:

                if "env" in fol or "temperature" in fol or "Temperature" in fol:
                    env_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames1 = [env_df, env_data]
                    env_df = pd.concat(frames1)
                elif "Door" in fol or "door" in fol:
                    door_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames2 = [door_df, door_data]
                    door_df = pd.concat(frames2)
                elif "Light" in fol or "Brightness" in fol or "light" in fol or "brightness" in fol:
                    brightness_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames3 = [brightness_df, brightness_data]
                    brightness_df = pd.concat(frames3)
                elif "Smart" in fol or "smart" in fol or "tv" in fol or "TV" in fol:
                    plug_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames4 = [plug_df, plug_data]
                    plug_df = pd.concat(frames4)
                elif "Microwave" in fol or "microwave" in fol:
                    microwave_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames5 = [microwave_df, microwave_data]
                    microwave_df = pd.concat(frames5)
                elif "Chair" in fol or "chair" in fol:
                    chair_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames6 = [chair_df, chair_data]
                    chair_df = pd.concat(frames6)
                elif "Cleaner" in fol or "cleaner" in fol:
                    cleaner_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames7 = [cleaner_df, cleaner_data]
                    cleaner_df = pd.concat(frames7)
                elif "Washer" in fol or "washer" in fol:
                    washer_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames8 = [washer_df, washer_data]
                    washer_df = pd.concat(frames8)
                elif "Fridge" in fol or "fridge" in fol:
                    fridge_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames9 = [fridge_df, fridge_data]
                    fridge_df = pd.concat(frames9)
                elif "Motion" in fol or "motion" in fol:
                    motion_data = pd.read_csv(f"{path}/{fol}", encoding="cp949")
                    frames10 = [motion_df, motion_data]
                    motion_df = pd.concat(frames10)

        # Remove duplicates and handle empty DataFrames
        if not brightness_df.empty:
            brightness_df = brightness_df.drop_duplicates(subset=['startTimeZone', 'aggrType', 'endTimeZone', 'resourceId'])
            brightness_df = brightness_df.reset_index(drop=True)
            
        if not plug_df.empty:
            plug_df = plug_df.drop_duplicates(subset=['startTimeZone', 'endTimeZone'])
            plug_df = plug_df.reset_index(drop=True)
      
        if not microwave_df.empty:
            microwave_df = microwave_df.drop_duplicates(subset=['startTimeZone', 'endTimeZone'])
            microwave_df = microwave_df.reset_index(drop=True)
           
        if not env_df.empty:
            env_df = env_df.drop_duplicates(subset=['startTimeZone', 'aggrType', 'endTimeZone', 'resourceId'])
            env_df = env_df.reset_index(drop=True)
     
        if not chair_df.empty:
            chair_df = chair_df.drop_duplicates(subset=['startTimeZone', 'endTimeZone'])
            chair_df = chair_df.reset_index(drop=True)
       
        if not cleaner_df.empty:
            cleaner_df = cleaner_df.drop_duplicates(subset=['startTimeZone', 'endTimeZone'])
            cleaner_df = cleaner_df.reset_index(drop=True)
         
        if not washer_df.empty:
            washer_df = washer_df.drop_duplicates(subset=['startTimeZone', 'endTimeZone'])
            washer_df = washer_df.reset_index(drop=True)
        
        if not fridge_df.empty:
            fridge_df = fridge_df.drop_duplicates(subset=['startTimeZone', 'endTimeZone'])
            fridge_df = fridge_df.reset_index(drop=True)
        
        if not motion_df.empty:
            motion_df = motion_df.drop_duplicates(subset=['startTimeZone', 'endTimeZone'])
            motion_df = motion_df.reset_index(drop=True)
        

        # save files
        door_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/door.csv")
        microwave_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/microwave.csv")
        brightness_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/brightness.csv")
        plug_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/tv.csv")
        env_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/env.csv")
        chair_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/chair.csv")
        cleaner_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/cleaner.csv")
        washer_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/washer.csv")
        fridge_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/fridge.csv")
        motion_df.to_csv(f"./data_aggr/{uid_lst[cnt]}/motion.csv")

        # # merge into one file
        # data_df = pd.DataFrame()

        # # brightness
        # if not brightness_df.empty:
        #     brightness_df = brightness_df[brightness_df['timeStamp'].isna()]
        #     brightness_df = brightness_df.sort_values(by=['startTimeZone'])
        #     data_df['startTime'] = brightness_df['startTimeZone']
        #     data_df['brightness'] = brightness_df['value']
        #     data_df = data_df.reset_index()
        #     data
        #     data_df = data_df.groupby('startTime').mean()
        # else:

        #     data_df['brightness'] = pd.Series(dtype=float)

        # # smart plug
        # if not plug_df.empty:
        #     plug_df = plug_df.sort_values(by=['startTimeZone'])
        #     # plug_df = plug_df[plug_df['value'] > 15]
        #     # plug_df['value'] = 1
        #     plug_df = plug_df.groupby('startTimeZone').sum(numeric_only=True)
        #     data_df['tv'] = plug_df['value']
        # else:
        #     data_df['tv'] = pd.Series(dtype=float)

        # # env data
        # if not env_df.empty:
        #     env_df = env_df.sort_values(by=['startTimeZone'])
        #     temperature_df = env_df[env_df['resourceId'] == '0.1.85']
        #     temperature_df = temperature_df[temperature_df['timeStamp'].isna()]
        #     temperature_df = temperature_df.groupby('startTimeZone').mean(numeric_only=True)
        #     temperature_df['value'] = temperature_df['value'] / 100
        #     data_df['temperature'] = temperature_df['value']

        #     humidity_df = env_df[env_df['resourceId'] == '0.2.85']
        #     humidity_df = humidity_df[humidity_df['timeStamp'].isna()]
        #     humidity_df = humidity_df.groupby('startTimeZone').mean(numeric_only=True)
        #     humidity_df['value'] = humidity_df['value'] / 100
        #     data_df['humidity'] = temperature_df['value']

        #     pressure_df = env_df[env_df['resourceId'] == '0.3.85']
        #     pressure_df = pressure_df[pressure_df['timeStamp'].isna()]
        #     pressure_df = pressure_df.groupby('startTimeZone').mean(numeric_only=True)
        #     data_df['pressure'] = pressure_df['value']
        # else:
        #     data_df['temperature'] = pd.Series(dtype=float)
        #     data_df['humidity'] = pd.Series(dtype=float)
        #     data_df['pressure'] = pd.Series(dtype=float)

        # # chair
        # if not chair_df.empty:
        #     row_sum = lambda row: sum(eval(row).values())
        #     chair_df['value'] = chair_df['value'].apply(row_sum)
        #     chair_df = chair_df.groupby('startTimeZone').sum(numeric_only=True)
        #     data_df['chair'] = chair_df['value']
        # else:
        #     data_df['chair'] = pd.Series(dtype=float)

        # # cleaner
        # if not cleaner_df.empty:
        #     row_sum = lambda row: sum(eval(row).values())
        #     cleaner_df['value'] = cleaner_df['value'].apply(row_sum)
        #     cleaner_df = cleaner_df.groupby('startTimeZone').sum(numeric_only=True)
        #     data_df['cleaner'] = cleaner_df['value']
        # else:
        #     data_df['cleaner'] = pd.Series(dtype=float)

        # # washer
        # if not washer_df.empty:
        #     row_sum = lambda row: sum(eval(row).values())
        #     washer_df['value'] = washer_df['value'].apply(row_sum)
        #     washer_df = washer_df.groupby('startTimeZone').sum(numeric_only=True)
        #     data_df['washer'] = washer_df['value']
        # else:
        #     data_df['washer'] = pd.Series(dtype=float)

        # # fridge
        # if not fridge_df.empty:
        #     row_sum = lambda row: sum(eval(row).values())
        #     fridge_df['value'] = fridge_df['value'].apply(row_sum)
        #     fridge_df = fridge_df.groupby('startTimeZone').sum(numeric_only=True)
        #     data_df['fridge'] = fridge_df['value']
        # else:
        #     data_df['fridge'] = pd.Series(dtype=float)

        # # motion
        # if not motion_df.empty:
        #     row_sum = lambda row: sum(eval(row).values())
        #     motion_df['value'] = motion_df['value'].apply(row_sum)
        #     motion_df = motion_df.groupby('startTimeZone').sum(numeric_only=True)
        #     data_df['motion'] = motion_df['value']
        # else:
        #     data_df['motion'] = pd.Series(dtype=float)

        # # microwave
        # if not microwave_df.empty:
        #     select_higher_value = lambda row: max(eval(row).values())
        #     microwave_df['value'] = microwave_df['value'].apply(select_higher_value)
        #     microwave_df = microwave_df.groupby('startTimeZone').sum(numeric_only=True)
        #     data_df['microwave'] = microwave_df['value']
        # else:
        #     data_df['microwave'] = pd.Series(dtype=float)

        # # door
        # if not door_df.empty:
        #     door_df = pd.read_csv("./data/1/door.csv")
        #     select_higher_value = lambda row: max(eval(row).values())
        #     door_df['value'] = door_df['value'].apply(select_higher_value)
        #     door_df = door_df.groupby('startTimeZone').sum(numeric_only=True)
        #     data_df['door'] = door_df['value']
        # else:
        #     data_df['door'] = pd.Series(dtype=float)

        # print(data_df)
        # data_df.to_csv(f"./data/data_aggr/{user}_data.csv")

if __name__ == "__main__":
    main()