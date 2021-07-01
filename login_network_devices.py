from netmiko import ConnectHandler
from ftd_api.ftd_client import FTDClient
from tqdm import trange
import file_control as fc
import json
import time
import re
from sys import exit

class ConnHandler:
    """
    This classs handles logging in and getting the credentials for various types of device.
    when calling the call you must specify the type of the device your using so it read the
    cred_file correctly if not it will store the new creds so it you dont have to insert it
    on every go
    """

    def __init__(self,type_:str):
        self.cred_dict = self.pull_creds(type_)

    def validate_ip(self,ip):
        valid_ip_check = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
        if (re.search(valid_ip_check, ip)):
            return
        else:
            raise Exception('LFD_LND:NOT A VALID IPV4 ADDRESS')

    def pull_creds(self,type_,rmdata=False):

        def _internal_pull_creds_01(cdict):
            for k in cdict['secret_stuff']:
                if list(k.keys())[0] == type_:
                    return k[type_]
                else:
                    raise Exception

        def _internal_pull_creds_02(cdict):
            cdump = self._pull_cred_helper(type_)
            cdict['secret_stuff'].append(cdump)
            with open('cHolder.json', 'w', encoding='utf-8') as fj:
                json.dump(cdict, fj, ensure_ascii=False, indent=4)
                return cdump[type_]
        try:
            creds = fc.get_file('cHolder.json', 'json')
            cdict = json.load(creds)
            if rmdata:
                for k in cdict['secret_stuff']:
                    if list(k.keys())[0] == type_:
                        del cdict['secret_stuff'][cdict['secret_stuff'].index(k)]
                        return _internal_pull_creds_02(cdict)
            else:
                try:
                    return _internal_pull_creds_01(cdict)
                except:
                    return _internal_pull_creds_02(cdict)
        except:
            cdict = {'secret_stuff':[]}
            return _internal_pull_creds_02(cdict)


    def _pull_cred_helper(self,type_):
        username_input = input("USERNAME:")
        userpasswd_input = input("PASSWORD:")
        cdict = {type_: {'username': username_input, 'password': userpasswd_input}}
        return cdict


    def login_ios_def(self,ip_address,uname,passwd):
        try:
            self.validate_ip(ip_address)
        except Exception as e:
            print(f'{e} \nEXITING')
            exit()

        ios_device_details = {
            'device_type': 'cisco_ios',
            'host': ip_address,
            'username': uname,
            'password': passwd
        }
        ios_device = ConnectHandler(**ios_device_details)
        return ios_device

    def login_fpr_def(self,ip_address,uname,passwd,port:int = 443):
        try:
            self.validate_ip(ip_address)
        except Exception as e:
            print(f'{e} \nEXITING')
            exit()

        logged_on = False
        while not logged_on:
                client = FTDClient(address=ip_address,port=port,username=uname,password=passwd)
                try:
                    client.login_custom(session_length=60*5)
                    logged_on = True
                    return client
                except Exception as e:
                    error = str(e)
                    if 'wait' in error:
                        print(f'LFD_LND:{"#"*50} Please wait 1 Minute... too many login failures {"#"*50}')
                        for i in trange(60):
                            time.sleep(1)
                    elif 'user' in error:
                        print(f'LFD_LND: {"#"*50} Incorrect username and password {"#"*50}')
                        self.pull_creds(type_='fpr',rmdata=True)
