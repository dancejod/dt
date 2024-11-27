import os
from timeit import default_timer as timer
from datetime import timedelta

directory_list = []

for root, dirs, files in os.walk("D:\dancejod_dp\dji_data", topdown=False):
    for name in dirs:
        directory_list.append(os.path.join(root, name))

directory_list[:] = [directory for directory in directory_list
                     if "upske-daniela-termal-honza" in directory
                     and "\output" not in directory
                     and r"\tmp" not in directory]
start = timer()
print("[Debug]: \t Time measurement started")
for dir in directory_list:
    try:
        os.system(f"python convert_thermal_dji.py {dir} T")

    except Exception as e:
        print(e.args)
        continue

end = timer()
print(f"[Debug]: \t Elapsed time: {timedelta(seconds=end-start)}")