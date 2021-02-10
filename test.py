#!/home/piotr/PycharmProjects/repositories-tool/venv/bin/python
import os
import glob

# path = os.getcwd()
# files = glob.glob(f"{path}/resource-service/**/*.java", recursive=True)
# print(files)
current_directory = os.getcwd()
_, dirs, _ = next(os.walk(current_directory))
for i in dirs:
    print(os.path.join(current_directory, i))
