import os
import datetime
import pandas as pd

dt_now = datetime.datetime.now().strftime('%Y%m%d%H%M')

# open the file that has all the ips that need to be logged into
def ingest_list_of_ipaddrs(file):
    list_of_IPs = []
    file = open(file,"r")
    for line in file:
        stripped = line.rstrip()
        list_of_IPs.append(stripped)
    return list_of_IPs


def folder_create(**kwargs):
    if kwargs.get("folder_path"):
        path = os.getcwd()
        wd_for_logs = path + '/{}'.format(kwargs.get("folder_path"))
        if os.path.exists(wd_for_logs):
            return wd_for_logs
        else:
            os.makedirs(wd_for_logs)
            return wd_for_logs
    else:
        wd_for_logs = os.path.expanduser("~") + r"\Desktop\DK_LOGFILES"
        os.path.exists(wd_for_logs)
        return wd_for_logs

# if we have a bunch of scripts that need to have a word or line from them run this
def remove_item_from_txt(dirPath,removeite,overwrite = False):
    _, _, filenames = next(os.walk(dirPath))
    for file in filenames:
        try:
            saveOutput = []
            with open(f'{dirPath}/{file}','r') as ofile:
                for dat in ofile.readlines():
                    if removeite not in dat:
                        saveOutput.append(dat)

            if overwrite:
                with open(f'{dirPath}/{file}', 'w') as ofile:
                    for line in saveOutput:
                        ofile.write(line)
                    print(f'DONE WITH {file}')
            else:
                with open(f'{dirPath}/NEW_{file}', 'w') as ofile:
                    for line in saveOutput:
                        ofile.write(line)
                    print(f'DONE WITH {file}')
        except Exception as e:
            print(f'ERROR WITH FILE {file}.... ERROR{e}')
            continue

def combine_files_into_one(col,dirname,fileData = None,auto =True,**additionalFiles):
    colData = []
    for file in os.listdir(dirname):
        if auto:
            if file.endswith('csv'):
                file = pd.read_csv('{}/{}'.format(dirname,file))
                file.columns = [colmn.lower() for colmn in file.columns]
                for ind in file.index:
                    colData.append(file[col][ind])
            # not built out yet
            elif file.endswith('txt'):
                pass
        else:
            if file.endswith('csv'):
                pass
            elif file.endswith('txt'):
                with open(fileData,'r') as origFile:
                    origFile = origFile.readlines()

                for files in additionalFiles.values():
                    with open(files,'r') as files:
                        pass
    output_dir = folder_create(folder_path="cfio_information")
    outputPD = pd.DataFrame(colData)
    host_filename = f"{output_dir}/combine_DATA_{dt_now}.csv"
    outputPD.to_csv(host_filename, index=False)

def get_file(file:str,type):
    check = os.path.exists(file)
    if check and file.endswith(type):
        retfile = open(file)
        return retfile
    else:
        return None


