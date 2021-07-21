import datetime
import ipaddress
from socket import gethostbyaddr
from threading import Thread
from time import sleep
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash
from dash.dependencies import Input, Output
from ipwhois import IPWhois
from nfstream import NFStreamer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sqlalchemy import create_engine, text
from login_network_devices import ConnHandler as ch

class NetCap:
    '''this module analyzes network flow and performs some ML and basic visualizations to the dataset still a WIP'''
    app = Dash(__name__)
    def __init__(self,inet,):
        self.connhandle = ch('db')
        self.uname = self.connhandle.cred_dict.get('username')
        self.passwd = self.connhandle.cred_dict.get('password')
        self.inet = inet
        self.database = 'analytics'
        self.db_url = f'mysql+mysqlconnector://{self.uname}:{self.passwd}@127.0.0.1:3306'
        self.engine = create_engine(self.db_url, pool_recycle=3600)
        self.table_name = 'flow_data'
        self._check_db_existance()


    def save_stream_to_db(self):
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
            except:
                # need to open an logging mechasism like tyr
                pass
            sleep(86400)  # perform database pruning everyday once a day

    def _check_db_existance(self):
        with self.engine.connect() as conn:
            conn.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        self.db_url = self.db_url + f'/{self.database}'
        self.engine = create_engine(self.db_url, pool_recycle=3600)


    def cluster_traffic_type(self):
        '''clean the df to only include ints,transform into 2D array,cluster the datapoints, find the optimal silhoute, groupby the new labels '''
        ptt = pd.read_sql(self.table_name, self.db_url)
        x = ptt.drop(columns=[col for col in ptt.columns if ptt[col].dtype != (np.int64 or np.float64)])
        pca = PCA(2)
        x = pca.fit_transform(x)
        sil = self._score_silhoutee(x) # use if needed to find optimal K
        kmean = KMeans(n_clusters=10)
        label = kmean.fit_predict(x)
        u_labels = np.unique(label)
        cluster_groups = ptt.groupby(by=u_labels)

    def _score_silhoutee(self,x):
        sil = []
        kmax = 50
        for k in range(2, kmax + 1):
            kmeans = KMeans(n_clusters=k).fit(x)
            labels = kmeans.labels_
            sil.append(silhouette_score(x, labels, metric='euclidean'))
        return sil


    def classify_traffic(self):
        # TODO: use it classify ads as a test?
        # TODO: need sample ad data
        pass

    def _extract_data(self,type:int):
        if type not in [4,6]:raise Exception('PLEASE CHOOSE 4 OR 6')
        cfc = pd.read_sql(self.table_name, self.db_url)
        nodes = cfc[['src_ip', 'dst_ip', 'bidirectional_bytes', 'src_port', 'dst_port', 'application_name', 'resolv_dst', 'resolv_src', 'timestamp']]
        # check ip.ver just to make sure it conforms to RFC
        nodes_step1 = nodes[nodes['src_ip'].apply(lambda ip: self._val_ip(ip, f'version{str(type)}')) != 0]
        return nodes_step1

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

        self.app.run_server(debug=True, use_reloader=False)

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

    def process_spooler(self):
        pruning = Thread(target=self._db_managment, )
        pruning.daemon = True
        pruning.start()

        save2db = Thread(target=self.save_stream_to_db, )
        # save2db.daemon = True
        save2db.start()




if __name__ == '__main__':
    listener = 'INTERFACE'
    n = NetCap(listener)
    # n.save_stream_to_db()
    # n.create_visuals()
    # n.process_spooler()
    # n._db_managment()
    # n.cluster_traffic_type()
