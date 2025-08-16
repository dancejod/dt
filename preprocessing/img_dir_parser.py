from pathlib import Path
from timeit import default_timer as timer
from datetime import timedelta
import os

os.chdir(r"D:\dancejod\dt\preprocessing")
base_dir = Path(r"H:\dp_data\20250622")

directory_list = [
    directory for directory in base_dir.glob("*")
]

start = timer()
print(f"{'[Debug]':<15} Time measurement started")

for dir_path in directory_list:
    try:
        print(f"{'[Processing]':<15} {dir_path}")
        from convert_thermal_dji import run
        run(dir_path, "F")
        #os.system(f'python convert_thermal_dji.py "{dir_path}" F')

    except Exception as e:
        print(f"{'[Error]':<15} {e.args}")
        continue

end = timer()
print(f"{'[Debug]':<15} Elapsed time: {timedelta(seconds=end-start)}")