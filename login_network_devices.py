from netmiko import ConnectHandler
import file_control as fc
import json

class ConnHandler:
    def __init__(self):
        self.cred_dict = self.pull_creds()

    def pull_creds(self):
        creds = fc.get_file('cHolder.json', 'json')
        if creds is None:
            username_input = input("USERNAME:")
            userpasswd_input = input("PASSWORD:")
            cdict = {'username': username_input, 'password': userpasswd_input}
            with open('cHolder.json', 'w', encoding='utf-8') as fj:
                json.dump(cdict, fj, ensure_ascii=False, indent=4)
            return cdict
        else:
            cdict = json.load(creds)
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

if __name__ == "__main__":
    ch = ConnHandler()