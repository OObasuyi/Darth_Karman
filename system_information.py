import datetime
import file_control
from login_network_devices import ConnHandler as ch

dt_now = datetime.datetime.now().strftime('%Y%m%d%H%M')

class IosSi:

    def cred_hand(self):
        self.connhandle = ch()
        cred_hold = self.connhandle.get_you_pee()
        self.uname = cred_hold.get('username')
        self.passwd = cred_hold.get('password')

    def hostname_sys_info(self,ip):
        hostname = self.connhandle.login_ios_def(ip,self.uname,self.passwd).send_command("sh run | i ^hostname")
        hostname = hostname.lstrip()
        return hostname

    def vty_timer_info(self,ip_list):
        for ip in file_control.ingest_list_of_ipaddrs(ip_list):
            vty_timer = login_network_devices.login_ios_def(ip,uname,passwd).send_command("more nvram:startup-config | i exec-timeout")
            return vty_timer

    def change_vty_to_0_0(self, ip_list,timer):
        shorten_vty_timeout_config = ["line vty 0 15","exec-timeout {}".format(timer)]
        for ip in file_control.ingest_list_of_ipaddrs(ip_list):
            output = login_network_devices.login_ios_def(ip,uname,passwd).send_config_set(shorten_vty_timeout_config)
            print(output)
            login_network_devices.login_ios_def(ip,uname,passwd).disconnect()

    def revert_to_old_config(self, ip_list,file_name,user,passwd):
        en_archiving = ["archive", "path flash:", "maximum 1"]
        with open(ip_list,'r') as device_list:
            for ip in device_list:
                login_network_devices.login_ios_def(ip,uname,passwd).send_config_set(en_archiving)
                ios_connect = ConnectHandler(device_type='cisco_ios', host=ip, username=user, password=passwd)
                output = ios_connect.send_command_timing('configure replace flash:{} list revert trigger error'.format(file_name))
                if 'Enter Y if you are sure' in output:
                    output += ios_connect.send_command_timing("yes")
                    hstnme = self.hostname_sys_info(ip)
                    print("#####################ROLLING BACK CONFIG FOR {}#####################\n".format(hstnme))
                    print(output)

    def config_manipulator(self, username,password,**kwargs):
        confg_copy = []
        output_dir = file_control.folder_create(folder_path = "configuration save data")
        with open(kwargs.get("ip_list_file")) as device_list:
            for ip in device_list:
                cmd_send = login_network_devices.login_ios_def(ip,uname,passwd).send_command(kwargs.get("config_cmmd"))
                hostname = self.hostname_sys_info(ip)
                list_cmd = list(cmd_send.split("\n"))
                for line01 in list_cmd:
                    if line01.startswith("Building"):pass
                    elif line01.startswith("Current configuration :"):pass
                    elif line01.startswith("!"):pass
                    else: confg_copy.append(line01)

                if kwargs.get("is_output_file_needed"):
                    con_filename = r"{}\{}_{}_{}.txt".format(output_dir,hostname, kwargs.get("appended_file_name"), dt_now)
                    with open(con_filename, "w+") as conf_file:
                        for line02 in confg_copy:
                            new_line_insert = line02 + "\n"
                            conf_file.write(new_line_insert)
                        print("#####################CONFIG SAVED TO {}#####################".format(con_filename))

                if kwargs.get("config_save_nvram") and kwargs.get("config_save_nvram") == "yes":
                    ios_connect = ConnectHandler(device_type='cisco_ios', host=ip, username=username, password=password)
                    save_file_name = 'copy run flash:{}_{}'.format(con_save_name_onDevice,kwargs.get("type_of_config"))
                    output = ios_connect.send_command_timing(save_file_name)
                    if 'Destination filename' in output:
                        output += ios_connect.send_command_timing("\n")
                        print("#####################CONFIG SAVED TO flash:/{}#####################\n".format(save_file_name))

    def get_ip_from_intf(self,ip):
        import re
        raw_intf = login_network_devices.login_ios_def(ip,uname,passwd).send_command("show ip int br | i {}".format(ip))
        intf_name = re.sub(" .*","",raw_intf)
        return intf_name


    def system_config_tmpl_filler(self,**kwargs):
        auth_config_pre = []
        with open(kwargs.get("config_templ_file"), "r") as auth_config:
            for auth_line in auth_config:
                auth_config_pre.append(auth_line)

        device_IPs = file_control.ingest_list_of_ipaddrs(kwargs.get("device_ip_file"))
        for ip in device_IPs:
            step01_list = []
            step02_list = []
            intf_name_from_ip = self.get_ip_from_intf(ip)
            hostname_info = self.hostname_sys_info(ip)
            for line02 in auth_config_pre:
                if kwargs.get("config_value_finder01") in line02:
                    blank_filled = line02.replace(kwargs.get("config_value_finder01"),intf_name_from_ip)
                    step01_list.append(blank_filled)
                else:
                    step01_list.append(line02)

            for line05 in step01_list:
                line06 = "{} \n".format(line05)
                step02_list.append(line06)

            output_dir = file_control.folder_create(folder_path="NEW CONFIGURATION SCRIPT")
            host_filename = r"{}\{}_global_config_script{}.txt".format(output_dir, hostname_info, dt_now)
            with open(host_filename, 'w+') as host_write:
                host_write.write(hostname_info + "\n")
                for line07 in step02_list:
                    host_write.write(line07)
                print("#####################NEW CONFIGURATION SCRIPT SAVED TO {}##################### \n".format(
                    host_filename))

                if kwargs.get("push_choice") and kwargs.get("push_choice") == "Y":
                    print("#####################STARTING CONFIGURATION PUSH TO {}#####################".format(hostname_info))
                    output = login_network_devices.login_ios_def(ip,uname,passwd).send_config_set(step01_list)
                    print(output)
                    print("#####################DONE#####################")


4

