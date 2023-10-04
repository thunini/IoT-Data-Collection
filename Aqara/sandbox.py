import datetime

today = datetime.datetime(2023, 9, 27, 0, 0)  # Initialize as 2023-09-27 00:00
next_date = datetime.datetime(2023, 9, 29, 0, 0)

next_date = today + datetime.timedelta(hours=12)
for i in range(3):
    print(today.strftime('%Y-%m-%d %H:%M'))
    print(next_date.strftime('%Y-%m-%d %H:%M'))


    print("helo")


    today = today + datetime.timedelta(hours=12)
    next_date = next_date + datetime.timedelta(hours=12)

