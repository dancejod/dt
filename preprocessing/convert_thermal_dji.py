import os
import glob
import struct
import sys
import shutil
import numpy as np
import weather_params
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
from PIL import Image
from timeit import default_timer as timer
from datetime import timedelta

def run(args):
    SDK_URL = r"https://terra-1-g.djicdn.com/2640963bcd8e45c0a4f0cb9829739d6b/TSDK/v1.5%20(10.0.1-EA220%E7%BA%A2%E5%A4%96%E4%BA%8C%E4%BE%9B%E3%80%8110.0-EP300)/dji_thermal_sdk_v1.5_20240507.zip"
    
    if not os.path.isdir("thermal_sdk"):
        print("[Preparations]: \t Thermal SDK not found, downloading")
        with urlopen(SDK_URL) as response:
            with ZipFile(BytesIO(response.read())) as zfile:
                os.mkdir("thermal_sdk")
                zfile.extractall("thermal_sdk")
                print("[Preparations]: \t Thermal SDK successfully downloaded")
    
    else: print("[Preparations]: \t Thermal SDK already downloaded")
        
    INPUT_DIR = args[1]
    OUTPUT_DIR = r"{INPUT_DIR}\output".format(INPUT_DIR=INPUT_DIR)
    TMP_DIR = r"{INPUT_DIR}\tmp".format(INPUT_DIR=INPUT_DIR)
    
    assert os.path.exists(INPUT_DIR)
    
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    
    os.mkdir(OUTPUT_DIR)
    os.mkdir(TMP_DIR)
    
    img_list = [os.path.basename(x) for x in glob.glob(f"{INPUT_DIR}/*_T.JPG")]
    print(f"[Processing]: \t {len(img_list)} images found")
    
    if args[2]:
        first_img_path = os.path.join(INPUT_DIR, img_list[0])
        flight_temperature, flight_humidity = weather_params.get_weather_conditions(first_img_path)
    else: flight_temperature, flight_humidity = 23, 70
    
    img_cnt = 0
    err_cnt = 0
    start = timer()
    print("[Debug]: \t Time measurement started")
    
    for img in img_list:
        img_cnt+=1
        print(f"[Processing]: \t Image {img_cnt}/{len(img_list)}")
        in_fpath = os.path.join(INPUT_DIR, img)
        tmp_fpath = os.path.join(TMP_DIR, img)
        out_fpath = os.path.join(OUTPUT_DIR, img)
        os.system(f"thermal_sdk\\utility\\bin\windows\\release_x64\\dji_irp.exe -a measure \
                              --measurefmt float32 \
                              --distance 25 \
                              --humidity {flight_humidity} \
                              --emissivity 0.97 \
                              --reflection {flight_temperature} \
                      -s {in_fpath} -o {tmp_fpath}.raw")
                      
        imwidth, imheight = Image.open(in_fpath).size
        
        try:
            with open(f"{tmp_fpath}.raw", "rb") as binimg:
                    data = binimg.read()
                    dformat = '{:d}f'.format(len(data)//4)
                    img_arr = np.array(struct.unpack(dformat, data))
            img_arr = img_arr.reshape(imheight, imwidth)       
            Image.fromarray(img_arr).save(f"{out_fpath}.tiff")
            
            os.system(f"exiftool.exe -tagsfromfile {in_fpath} {out_fpath}.tiff -overwrite_original_in_place")
        
        except BaseException():
            print(f"[Error]: Raw file for {img} does not exist. Skipping")
            err_cnt+=1
            continue
        
    shutil.rmtree(TMP_DIR)
    end = timer()
    print(f"[Debug]: \t Elapsed time: {timedelta(seconds=end-start)}")
    print(f"[Done]: \t Successfuly processed {len(img_list)} images")
    print(f"[Done]: \t {err_cnt} images skipped")

if __name__ == "__main__":
    run(sys.argv)