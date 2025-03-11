from pathlib import Path
from timeit import default_timer as timer
from datetime import timedelta
import os

base_dir = Path(r"D:\dancejod_dp\dji_data")

directory_list = [
    directory for directory in base_dir.rglob("*")
    if ("upske-daniela-termal-honza" in str(directory)
        and "output" not in str(directory)
        and "tmp" not in str(directory))
]

start = timer()
print(f"{'[Debug]':<15} Time measurement started")

for dir_path in directory_list:
    try:
        print(f"{'[Processing]':<15} {dir_path}")
        os.system(f'python convert_thermal_dji.py "{dir_path}" T')

    except Exception as e:
        print(f"{'[Error]':<15} {e.args}")
        continue

end = timer()
print(f"{'[Debug]':<15} Elapsed time: {timedelta(seconds=end-start)}")