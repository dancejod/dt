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
    SDK_URL = r"https://terra-1-g.djicdn.com/2640963bcd8e45c0a4f0cb9829739d6b/TSDK/v1.6(10.1.8-H30T)/dji_thermal_sdk_v1.6_20240927.zip"
    
    if not os.path.isdir("thermal_sdk"):
        print("[Preparations]: \t Thermal SDK not found, downloading")
        with urlopen(SDK_URL) as response:
            with ZipFile(BytesIO(response.read())) as zfile:
                os.mkdir("thermal_sdk")
                zfile.extractall("thermal_sdk")
                print("[Preparations]: \t Thermal SDK successfully downloaded")
    
    else: print("[Preparations]: \t Thermal SDK already downloaded")
        
    input_dir = args[1]
    output_dir = r"{INPUT_DIR}\output".format(INPUT_DIR=input_dir)
    tmp_dir = r"{INPUT_DIR}\tmp".format(INPUT_DIR=input_dir)
    
    assert os.path.exists(input_dir)
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    
    os.mkdir(output_dir)
    os.mkdir(tmp_dir)
    
    img_list = [os.path.basename(x) for x in glob.glob(f"{input_dir}/*_T.JPG")]
    print(f"[Processing]: \t {len(img_list)} images found")
    
    if args[2] == "T":
        first_img_path = os.path.join(input_dir, img_list[0])
        flight_temperature, flight_humidity = weather_params.get_weather_conditions(first_img_path)
    else: flight_temperature, flight_humidity = 23, 70
    
    img_cnt = 0
    err_cnt = 0
    start = timer()
    print("[Debug]: \t Time measurement started")
    
    for img in img_list:
        img_cnt+=1
        img = os.path.splitext(img)[0]
        print(f"[Processing]: \t Image {img_cnt}/{len(img_list)}")
        in_fpath = os.path.join(input_dir, img+".JPG")
        tmp_fpath = os.path.join(tmp_dir, img)
        out_fpath = os.path.join(output_dir, img)
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
                    bindata = binimg.read()
                    dformat = '{:d}f'.format(len(bindata)//4)
                    img_arr = np.array(struct.unpack(dformat, bindata))
            img_arr = img_arr.reshape(imheight, imwidth)       
            Image.fromarray(img_arr).save(f"{out_fpath}.tiff")
            
            os.system(f"exiftool.exe -tagsfromfile {in_fpath} {out_fpath}.tiff -overwrite_original_in_place")
        
        except Exception as e:
            print(e.args)
            print(f"[Error]: Raw file for {img}.JPG does not exist. Skipping")
            err_cnt+=1
            continue
        
    shutil.rmtree(tmp_dir)
    end = timer()
    err_rat = err_cnt/img_cnt*100
    print(f"[Debug]: \t Elapsed time: {timedelta(seconds=end-start)}")
    print(f"[Done]: \t Successfully processed {len(img_list) - err_cnt} images")
    print(f"[Done]: \t {err_cnt} images skipped ({err_rat:.2f} %)")

if __name__ == "__main__":
    run(sys.argv)