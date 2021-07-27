import datetime
import ipaddress
from sys import argv,executable,version_info
from os import execv
from socket import gethostbyaddr
from threading import Thread
from time import sleep
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash
from dash.dependencies import Input, Output
from ipwhois import IPWhois
from nfstream import NFStreamer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_selection import SelectKBest,chi2
from scipy.spatial.distance import cdist
from sqlalchemy import create_engine, text
from login_network_devices import ConnHandler as ch
from waitress import serve
from log_collector import Log_Collector

class NetCap:
    '''this module analyzes network flow and performs some ML and basic visualizations to the dataset still a WIP'''
    app = Dash(__name__)
    def __init__(self,inet,db_url='127.0.0.1'):
        self.connhandle = ch('db')
        self.uname = self.connhandle.cred_dict.get('username')
        self.passwd = self.connhandle.cred_dict.get('password')
        self.inet = inet
        self.database = 'analytics'
        self.db_url = f"mysql+mysqlconnector://{self.uname}:{self.passwd}@{db_url}:3306"
        self.engine = create_engine(self.db_url, pool_recycle=3600)
        self.table_name = 'flow_data'
        self._check_db_existance()
        self.logC = Log_Collector()

    def save_stream_to_db(self):
        while True:
            online_streamer = NFStreamer(source=self.inet,statistical_analysis=True, splt_analysis=10,n_dissections=30)
            for f in online_streamer:
                key = f.keys()
                val = f.values()
                flow = dict(zip(key,val))
                flow = pd.DataFrame([flow])
                flow.replace(r'^\s*$','unknown', regex=True,inplace=True)
                for col in flow.columns:
                    if isinstance(flow[col][0],list):
                        colID = 1
                        for i in flow[col][0]:
                            flow[f'{col}_item_{colID}'] = i
                            colID += 1
                        flow.drop(columns=[col],inplace=True)
                flow.drop(columns=['id','expiration_id'], inplace=True)
                flow['timestamp'] = datetime.datetime.now().replace(microsecond=0)
                flow['resolv_dst'] = flow.dst_ip.apply(lambda ip: self._val_ip(ip, 'reverse_dns'))
                flow['resolv_src'] = flow.src_ip.apply(lambda ip: self._val_ip(ip, 'reverse_dns'))
                flow.to_sql(name=self.table_name, con=self.engine, if_exists='append', index=False)

    def _db_managment(self):
        while True:
            rollback_period = (datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S')
            try:
                with self.engine.connect() as conn:
                    conn.execute(text(f"DELETE FROM {self.table_name} where timestamp <= '{rollback_period}'"))
            except Exception as error:
                self.logC.logger.exception('dbm',exc_info=True)
            sleep(86400)  # perform database pruning everyday once a day

    def _check_db_existance(self):
        with self.engine.connect() as conn:
            conn.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        self.db_url = self.db_url + f'/{self.database}'
        self.engine = create_engine(self.db_url, pool_recycle=3600)

    def cluster_traffic_type(self):
        #TODO: NEED TO LABEL THE ROWS SO WE CAN CLASSIFY THEM as Ad,MALICIOUS TYPE TRAFFIC? MAYBE USE A TRAINING SET FROM https://github.com/shramos/Awesome-Cybersecurity-Datasets
        ptt = pd.read_sql(self.table_name, self.db_url)
        ptt.drop(columns=['timestamp', 'resolv_dst', 'resolv_src', 'dst_mac', 'dst_oui','src_mac', 'src_oui','protocol', 'ip_version','vlan_id', 'bidirectional_first_seen_ms', 'bidirectional_last_seen_ms',],inplace=True)

        # reassamble SPLIT packets in orignal list format
        direction = []
        piat = []
        ps = []
        all_items = {'piat':piat,'ps':ps,'direction':direction}
        for litem in [col for col in ptt.columns.tolist() if 'item' in col]:
            if 'splt_direction' in litem:
                direction.append(litem)
            elif 'splt_piat' in litem:
                piat.append(litem)
            elif 'splt_ps' in litem:
                ps.append(litem)

        def add_list_items(x,v):
            return sum([x[i] for i in v])

        for k,v in all_items.items():
            ptt[k] = ptt.apply(lambda x: add_list_items(x,v),axis=1) # add the items in the SPLT list
        # drop the old SPLT columns
        ptt.drop(columns=[i for v in all_items.values() for i in v],inplace=True)
        x = ptt.apply(lambda x: pd.factorize(x)[0]) # turn all the columns in a integer representation to
        sil = self.find_optimal_K(x,'elbow') # use if needed to find optimal K
        bestfeatures = SelectKBest(score_func=chi2,k=10)
        fit = bestfeatures.fit(x.drop(columns=['application_name']), x.application_name)
        featureScores = pd.concat([pd.DataFrame(x.columns), pd.DataFrame(fit.scores_)], axis=1)
        featureScores.columns = ['colN', 'score']
        featureScores.sort_values(by='score',ascending=False,inplace=True)
        featureScores.reset_index(inplace=True,drop=True)
        featureScores = featureScores.head(20).colN.tolist()
        # were only using a subset of important features now
        x = x[featureScores]
        kmean = KMeans(n_clusters=10)
        label = kmean.fit_predict(x)
        ptt['cluster_id'] = label # assign the cluster ID we predicted to a new column
        cluster_groups = ptt.groupby('cluster_id')
        return cluster_groups # returns a pandas group opject we can pull the K-cluster by using the get_groups() function

    def find_optimal_K(self,x,type_):
        distortions = []
        inertias = []
        mapping1 = {}
        mapping2 = {}
        sil = []
        kmax = 50
        if type_ == 'silhouette_score':
            for k in range(2, kmax + 1):
                kmeans = KMeans(n_clusters=k).fit(x)
                labels = kmeans.labels_
                sil.append(silhouette_score(x, labels, metric='euclidean',sample_size=int(len(x) / 4 ))) #if its a huge dataset it will take some time
            return sil
        elif type_ == 'elbow':
            # faster elbow method https://www.geeksforgeeks.org/elbow-method-for-optimal-value-of-k-in-kmeans/
            for k in range(2, kmax + 1):
                kmeans = KMeans(n_clusters=k).fit(x)
                distortions.append(sum(np.min(cdist(x, kmeans.cluster_centers_,'euclidean'), axis=1)) / x.shape[0])
                inertias.append(kmeans.inertia_)
                mapping1[k] = sum(np.min(cdist(x, kmeans.cluster_centers_,'euclidean'), axis=1)) / x.shape[0]
                mapping2[k] = kmeans.inertia_
            fig = go.Figure(data=go.Scatter(x=list(range(2, kmax + 1)), y=distortions,mode='lines+markers'))
            fig.update_xaxes(title_text="K Size",title_standoff=25)
            fig.update_yaxes(title_text="distortions",title_standoff=25)
            fig.show()

    def classify_traffic(self):
        # TODO: this will work with cluster
        pass

    def _extract_data(self,type:int):
        if type not in [4,6]:raise Exception('PLEASE CHOOSE 4 OR 6')
        cfc = pd.read_sql(self.table_name, self.db_url)
        nodes = cfc[['src_ip', 'dst_ip', 'bidirectional_bytes', 'src_port', 'dst_port', 'application_name', 'resolv_dst', 'resolv_src', 'timestamp']]
        # check ip.ver just to make sure it conforms to RFC
        nodes_step1 = nodes[nodes['src_ip'].apply(lambda ip: self._val_ip(ip, f'version{str(type)}')) != 0]
        return nodes_step1

    #todo: need to add a toggle where we can choose what timeframe
    def create_visuals(self):
        self.app.layout = html.Div([html.H1('Byte Usage by Destination IP'),
                                   dcc.Graph(id = 'ipv4-graph',animate=True),
                                  dcc.Graph(id = 'ipv6-graph',animate=True),
                                dcc.Interval(id='interval-component',interval=300000,n_intervals=0)]) #update every 5 mins

        @self.app.callback(Output('ipv4-graph', 'figure'),[Input('interval-component', 'n_intervals')])
        def _update_graph_scatter_4(n):
            nodes_v4 = self._extract_data(4)
            scat4 = px.scatter(nodes_v4, x=nodes_v4.dst_ip, y=nodes_v4.bidirectional_bytes, hover_data=[nodes_v4.src_ip, nodes_v4.src_port, nodes_v4.dst_port, nodes_v4.application_name, nodes_v4.resolv_dst, nodes_v4.resolv_src, nodes_v4.timestamp])
            return scat4

        @self.app.callback(Output('ipv6-graph', 'figure'), [Input('interval-component', 'n_intervals')])
        def _update_graph_scatter_6(n):
            nodes_v6 = self._extract_data(6)
            scat6 = px.scatter(nodes_v6, x=nodes_v6.dst_ip, y=nodes_v6.bidirectional_bytes, hover_data=[nodes_v6.src_ip, nodes_v6.src_port, nodes_v6.dst_port, nodes_v6.application_name, nodes_v6.resolv_dst, nodes_v6.resolv_src, nodes_v6.timestamp])
            return scat6

        # this is gonna be a hack since I cant figure out for now how to release the port in a timely manner when we are restarting the script
        port = 8050
        erCount = 0
        while True:
            if 8050 >= port <= 8055:
                try:
                    serve(self.app.server, host='0.0.0.0', port=port)
                except:
                    self.logC.logger.critical(f"{'*' * 10}WAITING TO GRAB USE PORT:{port} PLEASE WAIT{'*' * 10}")
                    sleep(5)
                    serve(self.app.server,host='0.0.0.0', port=port)
            else:
                # well try this process three times after which well just stop the program
                erCount += 1
                port = 8050
                if erCount >= 3:
                    self.logC.logger.critical(f"{'*' * 10}CANT GET A PORT!!! SHUTTING DOWN SERVER{'*' * 10}")
                    raise SystemExit

    def _val_ip(self,ip:str,sevice:str):
        if sevice == 'reverse_dns':
            try:
                if ipaddress.ip_address(ip).is_global:
                    return gethostbyaddr(ip)[0] if not None else 'NO_RECORD'
                else:
                    raise Exception
            except:
                return 'UNRESOLVABLE'
        elif sevice == 'whois':
            try:
                if ipaddress.ip_address(ip).is_global:
                    return IPWhois(ip).lookup_whois().get('asn_description')
                else:
                    return None
            except:
                return None
        elif sevice == 'version4':
            try:
                ipaddress.IPv4Network(ip)
                return True
            except:
                return False
        elif sevice == 'version6':
            try:
                ipaddress.IPv6Network(ip)
                return True
            except:
                return False

    def am_i_alive_check(self):
        # Check if all process are still running OKAY if not restart

        # restart func non-accessible besides this func
        def _restart():
            current_ver = version_info
            current_ver = f'python{current_ver[0]}.{current_ver[1]}'

            self.logC.logger.critical(f"{'*'*10}TRYING TO RESTART{'*'*10}")
            execv(executable, [current_ver] + argv)

        def _shutdown():
            self.logC.logger.critical(f"{'*' * 10}TRYING TO SHUTDOWN{'*' * 10}")
            raise SystemExit

        sleep(300)  # sleep 5M at start before starting in case we are running on old data on first try
        while True:
            #check last DB write
            last_ts = None
            try:
                dt_now = datetime.datetime.now().replace(microsecond=0)
                write_period = (dt_now - datetime.timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
                with self.engine.connect() as conn:
                    last_ts = conn.execute(text(f"SELECT timestamp FROM {self.table_name} "
                                      f"where timestamp >= '{write_period}' "
                                      f"ORDER BY timestamp "
                                      f"DESC LIMIT 1"))

                try:
                    last_ts = [ts for ts in last_ts][0]
                except:
                    self.logC.logger.critical(f"{'*'*10}DATABASE HASN'T BEEN WRITTEN TO IN 12HRS STALE DATA!{'*'*10}")
                    _restart()
            except Exception as error:
                self.logC.logger.exception('alive_check',exc_info=True)
                _shutdown()
            sleep(3600)  # sleep 1hr

    def process_spooler(self):
        save2db = Thread(target=self.save_stream_to_db, )
        save2db.daemon = True
        save2db.start()

        pruning = Thread(target=self._db_managment, )
        pruning.daemon = True
        pruning.start()

        visuals = Thread(target=self.create_visuals, )
        visuals.daemon = True
        visuals.start()

        avail_check = Thread(target=self.am_i_alive_check, )
        avail_check.start()

if __name__ == '__main__':
    interface = 'en0'
    dburl = ''
    n = NetCap(interface,dburl)
    # n.save_stream_to_db()
    # n.create_visuals()
    # n.am_i_alive_check()
    # n.process_spooler()
    # n._db_managment()
    n.cluster_traffic_type()
