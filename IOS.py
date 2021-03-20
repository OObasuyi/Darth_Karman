import datetime
import re
import sys
import file_control
from login_network_devices import ConnHandler as ch
import pandas as pd
from system_information import IosSi


class IosPii:
    dt_now = datetime.datetime.now().strftime('%Y%m%d%H%M')
    
    def __init__(self):
        self.connhandle = ch()
        self.uname = self.connhandle.cred_dict.get('username')
        self.passwd = self.connhandle.cred_dict.get('password')

    def get_interface_name(self, ginDict:dict):
        output_dir = file_control.folder_create(folder_path="gin_output")

        if ginDict.get("device_ip_list") and ginDict.get("file_name"):
            return print("PLEASE SPECIFY LOCAL FILE OR DEVICE LIST")

        elif ginDict.get("device_ip_list"):
            with open(ginDict.get("device_ip_list")) as device_list:
                for ip in device_list:
                    pulled_phy_interfaces_lines = []
                    config = self.connhandle.login_ios_def(ip,self.uname,self.passwd).send_command(ginDict.get("cmd_to_send"))
                    host_conf = IosSi().hostname_sys_info(ip)
                    host_conf = host_conf.split('')[1].replace('-', '_')
                    pulled_phy_interfaces_lines.append(host_conf)
                    list_str = list(config.split("inter"))
                    for line01 in list_str:
                        if ginDict.get("intf_not_needed_01") in line01:pass
                        elif ginDict.get("intf_not_needed_02") in line01:pass
                        else:
                            switch_port_list = list(line01.split("\n"))
                            for line02 in switch_port_list:
                                if line02.startswith("face"):
                                    inter_line = line02.replace("face", "interface")
                                    pulled_phy_interfaces_lines.append(inter_line)
                    host_filename = f"{output_dir}\{host_conf} interface configs_{self.dt_now}.txt"
                    with open(host_filename, "w+") as intf_write:
                        for line03 in pulled_phy_interfaces_lines:
                            intf_write.write(line03 + "\n")
                    print(f"#####################CONFIG SAVED TO {host_filename}#####################")

        elif ginDict.get("file_name"):
            pulled_phy_interfaces_lines = []
            with open(ginDict.get("file_name"), "r") as config_file:
                for C_line in config_file:
                    if C_line.startswith("interface") and ginDict.get("intf_not_needed_01") not in C_line and ginDict.get("intf_not_needed_02") not in C_line:
                        pulled_phy_interfaces_lines.append(C_line)
            host_Cfilename= f"{output_dir}\{ginDict['file_name']} interface configs_{self.dt_now}.txt"
            with open(host_Cfilename, "w+") as intf_write:
                for pp_line in pulled_phy_interfaces_lines:intf_write.write(pp_line + "\n")

    def check_int_stat(self, cisDict:dict):
        output_dir = file_control.folder_create(folder_path="cis_output")

        if cisDict.get("device_ip_list") and cisDict.get("file_name"):
            return print("PLEASE SPECIFY LOCAL FILE OR DEVICE LIST")

        elif cisDict.get("device_ip_list"):
            with open(cisDict.get("device_ip_list")) as device_list:
                for ip in device_list:
                    leave_only_int_name = []
                    config_01 = self.connhandle.login_ios_def(ip,self.uname,self.passwd).send_command("sho ip int br")
                    config_02 = self.connhandle.login_ios_def(ip,self.uname,self.passwd).send_command("sho int status")
                    host_conf = IosSi().hostname_sys_info(ip)
                    host_conf = host_conf.split('')[1].replace('-', '_')
                    self.connhandle.login_ios_def(ip,self.uname,self.passwd).disconnect()
                    leave_only_int_name.append(host_conf)
                    list_str01 = list(config_01.split("\n"))
                    list_str02 = list(config_02.split("\n"))
                    for line01 in list_str01:
                        for line02 in list_str02:
                            if cisDict.get("status01") in line01 and cisDict.get("status02") in line02:
                                splitted01 =line02.split(' ', 1)[0]
                                leave_only_int_name.append(splitted01)
                    leave_only_int_name =list(dict.fromkeys(leave_only_int_name))
                    host_filename = f"{output_dir}\{host_conf}_interface_status_output_{self.dt_now}.txt"
                    with open(host_filename, "w+") as host_status_file:
                        for line03 in leave_only_int_name:
                            host_status_file.write(line03 + "\n")
                    print(f"#####################INTERFACE STATUS SAVED TO {host_filename}#####################")

        elif cisDict.get("file_name"):
            step01 = []
            leave_only_int_name = []
            with open(cisDict.get("file_name"), "r") as c_file:
                for line04 in c_file:
                    if cisDict.get("status01") in line04 or cisDict.get("status02") in line04:
                        splitted02 = line04.split(' ', 1)[0]
                        step01.append(splitted02)

            for line05 in step01:
                if re.search("[A-Z].[0-9]",line05):pass
                elif re.search("[0-9]$", line05):
                    leave_only_int_name.append(line05)
                host_filename = r"{}\{}_interface_status_output_{}.txt".format(output_dir, cisDict.get("file_name"), self.dt_now)
                with open(host_filename, "w+") as host_status_file:
                    for line06 in leave_only_int_name: host_status_file.write(line06+ "\n")

    def find_intf_config_from_arg(self, ficfaDict:dict):
        output_dir = file_control.folder_create(folder_path = "ficfa_output")
        count_up = 0

        device_IPs = file_control.ingest_list_of_ipaddrs(ficfaDict.get("device_ip_file"))
        for ip in device_IPs:
            pre_interf_list = []
            interf_list = []
            matchlist = []
            try:
                intf_conf = self.connhandle.login_ios_def(ip,self.uname,self.passwd).send_command("sh run | section interface")
            except:
                print(sys.exc_info()[1])
                continue
            host_conf = self.hostname_sys_info(ip)
            host_conf = host_conf.split('')[1].replace('-', '_')
            pre_interf_list.append(host_conf)
            list_str = list(intf_conf.split("inter"))
            for line02 in list_str:
                if ficfaDict.get("keyword_dont_add_01") and ficfaDict.get("keyword_dont_add_01") in line02:pass
                elif ficfaDict.get("keyword_dont_add_02") and ficfaDict.get("keyword_dont_add_02") in line02:pass
                elif ficfaDict.get("keyword_dont_add_03") and ficfaDict.get("keyword_dont_add_03") in line02:pass
                elif ficfaDict.get("intf_not_needed_01") and re.search(".*{}.*".format(ficfaDict.get("intf_not_needed_01")), line02):pass
                elif ficfaDict.get("intf_not_needed_02") and re.search(".*{}.*".format(ficfaDict.get("intf_not_needed_02")), line02):pass
                elif ficfaDict.get("attib_to_look_for_01") in line02:
                    switch_port_list = list(line02.split("\n"))
                    for line03 in switch_port_list:
                        if line03.startswith("face"):
                            inter_line = line03.replace("face", "interface")
                            pre_interf_list.append(inter_line)
                            count_up += 1
                        else:
                            pre_interf_list.append(line03)

                        if ficfaDict.get("attib_to_look_for_01") in line03:
                            matchlist.append(line03)


            pre_interf_list.append(f"INTERFACES MATCHED:{str(count_up)}")
            matchlist = set([mi for mi in matchlist if any(miiter.isdigit() for miiter in mi)])
            matchlist = [int(s) for ml in matchlist for s in ml.split() if s.isdigit()]

            count_up = 0
            host_filename =f"{output_dir}/{host_conf} interface match output_{self.dt_now}.txt"
            for line09 in pre_interf_list:
                line10 = "{} \n".format(line09)
                interf_list.append(line10)
            with open(host_filename, 'w+') as hFile:
                for mla in matchlist:
                    hFile.write('MATCHED ITEMs NAMES:{}\n'.format(mla))
                for line11 in interf_list:
                    hFile.write(line11)

            print(f"#####################INTERFACE MATCH RESULTS SAVED TO {host_filename}#####################")

    def interface_config_tmpl_filler(self, params:dict,localizedConfig= False):
        auth_config_pre = []
        with open(params.get("config_templ_file"), "r") as auth_config:
            for auth_line in auth_config:
                auth_config_pre.append(auth_line)

        device_IPs = file_control.ingest_list_of_ipaddrs(params.get("device_ip_file"))
        for ip in device_IPs:
            step01_list = []
            step02_list = []
            try:
                intf_conf = self.connhandle.login_ios_def(ip,self.uname,self.passwd).send_command("sh run | section interface")
            except:
                print(sys.exc_info()[1])
                continue

            host_conf = self.hostname_sys_info(ip)
            list_str = list(intf_conf.split("\ninter"))
            # per-switch: dont make config script for certain ports on certain devices 
            for line01 in list_str: 
                if localizedConfig:  # make sure all the read data has the correct templete!
                    hostNameMatch = host_conf.lstrip('hostname').strip() #if you want to filter by hostname
                    local_config = pd.read_csv(params.get("localized_config_file"))
                    col_name = local_config.columns.values.tolist()
                    local_config['LCF_hostname'] = local_config['LCF_hostname'].map(lambda row: row.lstrip(' ').strip())
                    sendTop = bool
                    if not local_config[local_config['LCF_MGMG_IP'] == ip].empty or not local_config[local_config['LCF_hostname'] == hostNameMatch].empty:
                        lcf_DNA = local_config[local_config['LCF_MGMG_IP'] == ip]
                        keys = params.keys()
                        for key in keys:
                            if key in col_name:
                                if 'exclude' in key and f'switchport access vlan {str(int(lcf_DNA[key].iloc[0]))}' in line01:
                                    sendTop = True
                                elif 'exclude' in key and f'switchport voice vlan {str(int(lcf_DNA[key].iloc[0]))}' in line01:
                                    sendTop = True
                                else:
                                    sendTop =False
                        if sendTop: continue
                # all-switches: decide on where to make a config script based on config items on the port
                if params.get("keyword_dont_add_01") and params.get("keyword_dont_add_01") in line01:continue
                elif params.get("keyword_dont_add_02") and params.get("keyword_dont_add_02") in line01:continue
                elif params.get("keyword_dont_add_03") and params.get("keyword_dont_add_03") in line01:continue
                elif params.get("keyword_dont_add_04") and re.search(f".*{params.get('keyword_dont_add_04')}.*", line01):continue
                elif params.get("keyword_dont_add_05") and params.get("keyword_dont_add_05") in line01:continue
                elif params.get("interface_range_allow") and not re.match(f".*{params.get('interface_range_allow')}.*", line01):pass
                elif params.get("interface_range_deny") and re.match(f".*{params.get('interface_range_deny')}.*", line01):continue
                elif params.get("attib_to_change") and params.get("attib_to_change") in line01:
                    switch_port_list = list(line01.split("\n"))
                    for line02 in switch_port_list:
                        if line02.startswith("face"):
                            inter_line = line02.replace("face", "interface")

                            for line03 in auth_config_pre:
                                if "interface" in line03:
                                    correct_intf = line03.replace(line03, inter_line)
                                    step01_list.append(correct_intf)

                        elif line02.startswith("interface"):
                            inter_line = line02

                            for line03 in auth_config_pre:
                                if "interface" in line03:
                                    correct_intf = line03.replace(line03, inter_line)
                                    step01_list.append(correct_intf)

                        elif params.get("attib_to_change") in line02:
                            attr_val = line02.strip(params.get("attib_to_change"))

                            for line04 in auth_config_pre:
                                if params.get("fill_in_the_blank_val") in line04:
                                    correct_attr = line04.replace(params.get("fill_in_the_blank_val"), attr_val)
                                    step01_list.append(correct_attr)

                                elif "interface" in line04:pass
                                else:step01_list.append(line04)

                        if params.get('removefromConfig') is not None:
                            if params.get('removefromConfig') in line02:
                                del_line_replace = line02.replace(line02, f"\n no {line02}")
                                step01_list.append(del_line_replace)


                elif params.get("attib_to_change_2") and params.get("attib_to_change_2") in line01:
                    switch_port_list = list(line01.split("\n"))
                    for line02 in switch_port_list:
                        if line02.startswith("face"):
                            inter_line = line02.replace("face", "interface")

                            for line03 in auth_config_pre:
                                if "interface" in line03:
                                    correct_intf = line03.replace(line03, inter_line)
                                    step01_list.append(correct_intf)

                        elif params.get("attib_to_change_2") in line02:
                            attr_val = line02.strip(params.get("attib_to_change_2"))

                            for line04 in auth_config_pre:
                                if params.get("fill_in_the_blank_val") in line04:
                                    correct_attr = line04.replace(params.get("fill_in_the_blank_val"), attr_val)
                                    step01_list.append(correct_attr)

                                elif "interface" in line04:
                                    pass
                                else:
                                    step01_list.append(line04)


                elif params.get("attib_to_change") and params.get("attib_to_change") not in line01 or params.get("attib_to_change_2") and params.get("attib_to_change_2") not in line01:
                    switch_port_list = list(line01.split("\n"))
                    for line02 in switch_port_list:
                        if line02.startswith("face"):
                            inter_line = line02.replace("face", "interface")

                            if params.get("baseline_vlan"):
                                attr_val = params.get("baseline_vlan")
                                for line03 in auth_config_pre:
                                    if "interface" in line03:
                                        correct_intf = line03.replace(line03, inter_line)
                                        step01_list.append(correct_intf)

                                for line04 in auth_config_pre:
                                    if params.get("fill_in_the_blank_val") in line04:
                                        correct_attr = line04.replace(params.get("fill_in_the_blank_val"), attr_val)
                                        step01_list.append(correct_attr)

                                    elif "interface" in line04:
                                        pass
                                    else:
                                        step01_list.append(line04)

    # since the newline char was stripped earlier add it back in the lines
            for line05 in step01_list:
                if line05.startswith('interface'): line05 = '\n' + line05 + '\n'
                step02_list.append(line05)

            output_dir = file_control.folder_create(folder_path=f'ictf_{params["foldername"]}')
            host_conf = host_conf.split('')[1].replace('-','_')
            host_filename = f"{output_dir}/{output_dir}_{host_conf}_ICS_{self.dt_now}.txt"
            with open(host_filename,'w+') as host_write:
                for line07 in step02_list:
                    host_write.write(line07)
                print(f"#####################NEW CONFIGURATION SCRIPT SAVED TO {host_filename}##################### \n")

                if bool(params.get("push_choice")):
                    print(f"#####################STARTING CONFIGURATION PUSH TO {host_conf}#####################")
                    output = self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_config_set(step01_list)
                    print(output)
                    print("#####################DONE#####################")

    def delete_config_from_intf(self, params:dict,localizedConfig= False):
        device_IPs = file_control.ingest_list_of_ipaddrs(params.get("device_ip_file"))
        for ip in device_IPs:
            step01_list = []
            step02_list = []
            intf_conf = self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_command("sh run | section interface")
            host_conf = self.hostname_sys_info(ip)
            list_str = list(intf_conf.split("\ninter"))
            for line01 in list_str:
                if localizedConfig:  # make sure all the read data has the correct templete!
                    hostNameMatch = host_conf.lstrip('hostname').strip()  # if you want to filter by hostname
                    local_config = pd.read_csv(params.get("localized_config_file"))
                    col_name = local_config.columns.values.tolist()
                    local_config['LCF_hostname'] = local_config['LCF_hostname'].map(lambda row: row.lstrip(' ').strip())
                    sendTop = bool
                    if not local_config[local_config['LCF_MGMG_IP'] == ip].empty or not local_config[local_config['LCF_hostname'] == hostNameMatch].empty:
                        lcf_DNA = local_config[local_config['LCF_MGMG_IP'] == ip]
                        keys = params.keys()
                        for key in keys:
                            if key in col_name:
                                if 'exclude' in key and f'switchport access vlan {str(int(lcf_DNA[key].iloc[0]))}' in line01:
                                    sendTop = True
                                elif 'exclude' in key and f'switchport voice vlan {str(int(lcf_DNA[key].iloc[0]))}' in line01:
                                    sendTop = True
                                else:
                                    sendTop = False
                        if sendTop: continue
                if params.get("keyword_dont_add_01") and params.get("keyword_dont_add_01") in line01:continue
                elif params.get("keyword_dont_add_02") and params.get("keyword_dont_add_02") in line01:continue
                elif params.get("keyword_dont_add_03") and params.get("keyword_dont_add_03") in line01:continue
                elif params.get("keyword_dont_add_04") and re.search(f".*{params.get('keyword_dont_add_04')}.*", line01):continue
                elif params.get("interface_range_allow") and not re.match(f".*{params.get('interface_range_allow')}.*", line01):pass
                elif params.get("interface_range_deny") and re.match(f".*{params.get('interface_range_deny')}.*", line01):continue
                elif params.get("config_to_del") and params.get("config_to_del") in line01:
                    switch_port_list = list(line01.split("\n"))
                    for line02 in switch_port_list:
                        if line02.startswith("face"):
                            inter_line = line02.replace("face", "interface")
                            step01_list.append(inter_line)

                        elif params.get("config_to_del") in line02:
                            del_line_replace = line02.replace(line02,"no {}".format(line02))
                            step01_list.append(del_line_replace)

                        elif params.get("config_to_del_02") and params.get("config_to_del_02") in line02:
                            del_line_replace = line02.replace(line02, "no {}".format(line02))
                            step01_list.append(del_line_replace)

                        elif params.get("config_to_del_03") and params.get("config_to_del_03") in line02:
                            del_line_replace = line02.replace(line02, "no {}".format(line02))
                            step01_list.append(del_line_replace)

                elif params.get("config_to_del_02") and params.get("config_to_del_02") in line01:
                    switch_port_list = list(line01.split("\n"))

                    for line02 in switch_port_list:
                        if line02.startswith("face"):
                            inter_line = line02.replace("face", "interface")
                            step01_list.append(inter_line)

                        elif params.get("config_to_del_02") in line02:
                            del_line_replace = line02.replace(line02, "no {}".format(line02))
                            step01_list.append(del_line_replace)

                elif params.get("config_to_del_03") and params.get("config_to_del_03")in line01:
                    switch_port_list = list(line01.split("\n"))

                    for line02 in switch_port_list:
                        if line02.startswith("face"):
                            inter_line = line02.replace("face", "interface")
                            step01_list.append(inter_line)

                        elif params.get("config_to_del_03") in line02:
                            del_line_replace = line02.replace(line02, "no {}".format(line02))
                            step01_list.append(del_line_replace)


            for line03 in step01_list:
                if line03.startswith('interface'): line03 = '\n' + line03 + '\n'
                step02_list.append(line03)
            output_dir = file_control.folder_create(folder_path=f'dcfi_{params["foldername"]}')
            host_conf = host_conf.split('')[1].replace('-', '_')
            host_filename = f"{output_dir}/{host_conf}_dcfi_{self.dt_now}.txt"
            with open(host_filename, 'w+') as host_write:
                host_write.write(host_conf + "\n")
                for line07 in step02_list:
                    host_write.write(line07)
                print("#####################NEW CONFIGURATION SCRIPT SAVED TO {}#####################\n".format(host_filename))

            if params.get("push_choice"):
                print("#####################STARTING CONFIGURATION PUSH TO {}#####################".format(host_conf))
                output = self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_config_set(step01_list)
                print(output)
                print("#####################DONE#####################")

    def hostname_sys_info(self, ip):
        hostname = self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_command("sh run | i ^hostname")
        hostname = hostname.lstrip()
        return hostname

    def get_mac_addres_table(self, ip_list_file):
        device_IPs = file_control.ingest_list_of_ipaddrs(ip_list_file)
        for ip in device_IPs:
            col_names = []
            col_vals = []
            try:
                mato = self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_command("sho mac address-table")
            except:
                continue
            hostname = self.hostname_sys_info(ip)
            mato = mato.lstrip()
            config_split = self.config_file_mannipulator(mato,strip_by='\n')

            for line in config_split:
                if re.search('[V|v]lan.*[M|m]ac [A|a]ddress.*[T|t]ype.*[P|p]ort.',line):
                    col_headers = line.split("  ")
                    col_headers = [not_empty for not_empty in col_headers if not_empty]
                    for col_line in col_headers:
                        if 'Vlan' or 'Mac Address' or 'Type' or 'Ports' in col_line:
                            if re.search('^ ',col_line):
                                col_line = re.sub('^ ', '', col_line)
                                col_names.append(col_line)
                            else:
                                col_names.append(col_line)
                        else:
                            pass

                elif re.search('^.*[0-9]',line):
                    col_val = line.split(" ")
                    col_val = [not_empty for not_empty in col_val if not_empty]
                    if 'Total' in col_val:
                        pass
                    elif 'static' in col_val or 'static'.upper() in col_val:
                        col_vals.append(col_val)
                    elif 'dynamic' in col_val or 'dynamic'.upper() in col_val:
                        col_vals.append(col_val)

            corrected_col_vals01 = []
            corrected_col_vals02 = []
            reMatch = re.compile('ip.*')

            for val_list in col_vals: #remove column element
                val_list = [i for i in val_list if not reMatch.match(i)]
                corrected_col_vals01.append(val_list)

            for val_list in corrected_col_vals01: #remove list element
                if 'CPU' in val_list:
                    pass
                else:
                    corrected_col_vals02.append(val_list)
                    corrected_col_vals01.remove(val_list) #reclaim memory


            matoPD = pd.DataFrame(corrected_col_vals02,columns=col_names)
            print(matoPD)
            #
            output_dir = file_control.folder_create(folder_path="DEVICE INFORMATION")
            host_filename = r"{}/{}_mac_address_table_output{}.csv".format(output_dir, hostname, self.dt_now)
            matoPD.to_csv(host_filename,index=False)

            print("#####################NEW CONFIGURATION SCRIPT SAVED TO {}##################### \n".format(host_filename))

    def config_file_mannipulator(self,config_output:str,strip_by):
        config_split = config_output.split(strip_by)
        return config_split
    

    def vty_timer_info(self,ip_list):
        for ip in file_control.ingest_list_of_ipaddrs(ip_list):
            vty_timer = self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_command("more nvram:startup-config | i exec-timeout")
            return vty_timer

    def change_vty_to_0_0(self, ip_list,timer):
        shorten_vty_timeout_config = ["line vty 0 15",f"exec-timeout {timer}"]
        for ip in file_control.ingest_list_of_ipaddrs(ip_list):
            output = self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_config_set(shorten_vty_timeout_config)
            print(ip,output)
            self.connhandle.login_ios_def(ip, self.uname, self.passwd).disconnect()

    def revert_to_old_config(self, ip_list,file_name,user,passwd):
        en_archiving = ["archive", "path flash:", "maximum 1"]
        with open(ip_list,'r') as device_list:
            for ip in device_list:
                self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_config_set(en_archiving)   
                output = self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_command_timing(f'configure replace flash:{file_name} list revert trigger error')
                if 'Enter Y if you are sure' in output:
                    output += self.connhandle.login_ios_def(ip, self.uname, self.passwd).send_command_timing("yes")
                    hstnme = self.hostname_sys_info(ip)
                    print("#####################ROLLING BACK CONFIG FOR {}#####################\n".format(hstnme))
                    print(output)



if __name__ == "__main__":

    ios = IosPii()
    # ios.get_mac_addres_table("device_ip_test.txt")
    # ios.combine_files_into_one('mac address',"DEVICE INFORMATION",'.csv')
    # file_control.remove_item_from_txt('NEW CONFIGURATION SCRIPT',removeite='shut',overwrite=True)
