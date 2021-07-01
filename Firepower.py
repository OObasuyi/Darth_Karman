from login_network_devices import ConnHandler as ch
from ftd_api.bulk_tool import BulkTool
from ftd_api.string_helper import split_string_list
from os import getcwd
import json
import requests


class FPRType:
    """
    This class is based on the work done in jaredtsmith/ftd_api.
    """
    def __init__(self):
        self.connhandle = ch('fpr')
        credinfo = self.connhandle.cred_dict
        self.uname = credinfo['username']
        self.passwd =  credinfo['password']

    def bulk_configs(self,ip,pull_config:bool,file_path = getcwd(),pending:bool = False,sFDMendpoint=None,id_list = None,type_list = None,name_list= None,filter_local=False):
        fprconnect = self.connhandle.login_fpr_def(ip,self.uname,self.passwd)
        bulk_client = BulkTool(fprconnect)
        if pull_config:
            if sFDMendpoint is not None:
                config = bulk_client.url_export(sFDMendpoint, file_path, output_format='JSON')
                return
            pending_changes = False
            if pending:
                pending_changes = True
            bulk_client.bulk_export(file_path, pending_changes, type_list=type_list, id_list=id_list, name_list=name_list)
        else:
            file_list = split_string_list(file_path)
            bulk_client.bulk_import(file_list, input_format=format, type_list=type_list, id_list=id_list, name_list=name_list, filter_local=filter_local)

    def access_control_policy(self,pull:bool,set:bool,ip,deploy=False,save_poutput=False):
        fprconnect = self.connhandle.login_fpr_def(ip, self.uname, self.passwd)
        if pull:
            policies = fprconnect.do_get_raw_with_base_url(additional_url='/policy/accesspolicies/default/accessrules')
            ap = json.loads(policies.content)
            # TODO: Need to Prettify and turn into a CSV if exporting is needed

    def gather_data(self,ip):
        config_event = {"view": {"selected": "All Events"},
            "timeRange": {"mode": "realTime", "historic":
                {"duration": 30, "from": -1, "to": -1},
                "realTime": {"state": "pause", "rate": 60}},
            "filter": [], "filterQuery": {"op": "ALL", "items": []}, "viewColumnsWidth": {}, "showHistoric": True}

        fprconnect = self.connhandle.login_fpr_def(ip, self.uname, self.passwd)
        headers = fprconnect._create_auth_headers()

        enviromental_data = fprconnect.do_get_raw_with_base_url(additional_url='/devices/default/operational/metrics')
        enviromental_data = json.loads(enviromental_data.content)

        send_config_events = requests.post(f'https://{ip}/eventing/api/analyze/events/saveFilters.json', headers=headers, verify=False, data=config_event)
        eHeader = headers.copy()
        eHeader['Content-Type'] = 'application/x-www-form-urlencoded'
        eID = '' #TODO: need help finding where the FTD is pulling this from
        eventing_data = f'condition=%7B%22op%22%3A%22ALL%22%2C%22items%22%3A%5B%7B%22name%22%3A%5B%22Ev_TypeId%22%5D%2C%22type%22%3A%5B%22range%22%5D%2C%22include%22%3A%5B%22true%22%5D%2C%22value%22%3A%5B%22{eID}%22%5D%7D%5D%7D&queuesize=500&includeSavedEvents=true'
        send_config_events = requests.post(f'https://{ip}/eventing/rt/', headers=eHeader, verify=False, data=eventing_data)
        if "task created" in str(send_config_events.content): #FTD sends back an ID to use when fetching event data
            getID = json.loads(send_config_events.content)['id']
            get_config_events = requests.get(f'https://{ip}/eventing/rt/{getID}?pagesize=500', headers=eHeader, verify=False)
            event_data = json.loads(get_config_events.content)


if __name__ == "__main__":
    fpr = FPRType()
    ip = 'IP'
    # fpr.bulk_configs(ip,export=False,file_path = 'Darth_Karman/full_config.json',type_list=['internalcertificate','user','metadata','managementip','webuicertificate','datasslciphersetting'],filter_local = True)
    # fpr.bulk_configs(ip, pull_config=True)
    # fpr.access_control_policy(pull=True,set=False,ip=ip)
    fpr.gather_data(ip)
