import pandas as pd
import subprocess
from datetime import datetime

def round_time(datetime_object):
    minutes_total = datetime_object.hour * 60 + datetime_object.minute
    rounded_minutes = round(minutes_total / 10) * 10
    fixed_hour, fixed_minutes = divmod(rounded_minutes, 60)
    fixed_datetime = datetime_object.replace(hour=fixed_hour, minute=fixed_minutes, second=0)
    return fixed_datetime

def get_weather_conditions(img_path):
    metadata_datetime = subprocess.run(["exiftool.exe", "-DateTimeOriginal", img_path], capture_output=True, text=True)
    dt_str = metadata_datetime.stdout.split(": ", 1)[-1].strip()
    dt_obj = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
    date = dt_str.split()[0].replace(":", "")
    
    weather_file = pd.read_csv(f"..\\data\\ur_meteo_station_measurements\\{date}.csv", sep=";")
    weather_file.drop([0], inplace=True)
    weather_file["Labels:"] = pd.to_datetime(weather_file["Labels:"], format="%d.%m.%Y %H:%M:%S")
    
    approximate_time_of_flight_conditions = weather_file[weather_file['Labels:'].dt.time == round_time(dt_obj).time()]
    approximate_time_of_flight_conditions = approximate_time_of_flight_conditions[[" RVT81 Teplota 2m", " RVT81 Vlhkost 2m"]].astype('float32')
    temperature = approximate_time_of_flight_conditions[" RVT81 Teplota 2m"].values[0]
    humidity = approximate_time_of_flight_conditions[" RVT81 Vlhkost 2m"].values[0]
    
    return temperature, humidity