import datetime
import calendar
import time

today = datetime.date(2023, 9, 1)  # Include time information

for i in range(9):
    next_date = today +  datetime.timedelta(3)
    for j in range(2):
        today = today +  datetime.timedelta(1)

        print(today)
        print(next_date)
    today = next_date

    
