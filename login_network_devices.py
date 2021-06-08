from netmiko import ConnectHandler
from ftd_api.ftd_client import FTDClient
import file_control as fc
import json

class ConnHandler:
    def __init__(self,type_:str):
        self.cred_dict = self.pull_creds(type_)

    def pull_creds(self,type_):
        try:
            creds = fc.get_file('cHolder.json', 'json')
            cdict = json.load(creds)
            typedata = cdict[type_]
            return typedata
        except:
            username_input = input("USERNAME:")
            userpasswd_input = input("PASSWORD:")
            cdict = {type_: {'username': username_input, 'password': userpasswd_input}}
            with open('cHolder.json', 'a+', encoding='utf-8') as fj:
                json.dump(cdict, fj, ensure_ascii=False, indent=4)
            return cdict

    def login_ios_def(self,ip_addess,uname,passwd):
        ios_device_details = {
            'device_type': 'cisco_ios',
            'host': ip_addess,
            'username': uname,
            'password': passwd
        }
        ios_device = ConnectHandler(**ios_device_details)
        return ios_device

    def login_fpr_def(self,ip_address,uname,passwd,port:int = 443):
        try:
            client = FTDClient(address=ip_address,port=port,username=uname,password=passwd)
            client.login()
            return client
        except Exception as err:
            print(f'ERROR: {err}')
            raise


if __name__ == "__main__":
    ch = ConnHandler('test9')
