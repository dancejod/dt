import os
import struct
import sys
import shutil
import numpy as np
import weather_params
import rasterio as rio
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
from pathlib import Path
from PIL import Image
from timeit import default_timer as timer
from datetime import timedelta
from tqdm import tqdm

def run(args):
    SDK_URL = r"https://terra-1-g.djicdn.com/2640963bcd8e45c0a4f0cb9829739d6b/TSDK/v1.6(10.1.8-H30T)/dji_thermal_sdk_v1.6_20240927.zip"
    sdk_path = Path("thermal_sdk")

    if not sdk_path.exists():
        print("[Preparations]: \t Thermal SDK not found, downloading")
        with urlopen(SDK_URL) as response:
            with ZipFile(BytesIO(response.read())) as zfile:
                sdk_path.mkdir(parents=True, exist_ok=True)
                zfile.extractall(sdk_path)
                print("[Preparations]: \t Thermal SDK successfully downloaded")
    
    else: print("[Preparations]: \t Thermal SDK already downloaded")
        
    input_dir = Path(args[1])
    output_dir = input_dir / "output"
    tmp_dir = input_dir / "tmp"
    
    assert input_dir.exists(), f"Input directory '{input_dir}' does not exist"
    
    shutil.rmtree(output_dir, ignore_errors=True)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    output_dir.mkdir()
    tmp_dir.mkdir()
    
    img_list = sorted(input_dir.glob("*_T.JPG"))
    print(f"[Processing]: \t {len(img_list)} images found")
    
    if args[2] == "T":
        first_img_path = os.path.join(input_dir, img_list[0])
        flight_temperature, flight_humidity = weather_params.get_weather_conditions(first_img_path)
    else: flight_temperature, flight_humidity = 23, 70
    
    img_cnt, err_cnt = 0, 0
    start = timer()
    print("[Debug]: \t Time measurement started")
    
    for img in tqdm(img_list, desc="Processing images", unit="img"):
        img_cnt+=1
        img_name = img.stem
        in_fpath = img
        tmp_fpath = tmp_dir / img_name
        out_fpath = output_dir / f"{img_name}.tiff"
        os.system(f"thermal_sdk\\utility\\bin\windows\\release_x64\\dji_irp.exe -a measure \
                              --measurefmt float32 \
                              --distance 25 \
                              --humidity {flight_humidity} \
                              --emissivity 1 \
                              --reflection {flight_temperature} \
                      -s {in_fpath} -o {tmp_fpath}.raw")
        
        try:
            imwidth, imheight = Image.open(in_fpath).size

            with open(f"{tmp_fpath}.raw", "rb") as binimg:
                    bindata = binimg.read()
                    dformat = '{:d}f'.format(len(bindata)//4)
                    img_arr = np.array(struct.unpack(dformat, bindata))

            img_arr = img_arr.reshape(imheight, imwidth)      
            
            with rio.open(
                out_fpath, "w",
                driver="GTiff",
                dtype= rio.float32,
                height=img_arr.shape[0],
                width=img_arr.shape[1],
                count=1) as out:

                out.write(img_arr, 1)
            
            os.system(f"exiftool.exe -tagsfromfile {in_fpath} -all:all {out_fpath} -overwrite_original")
        
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