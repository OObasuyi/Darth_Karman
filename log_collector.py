import logging
import gzip
import os
from logging.handlers import TimedRotatingFileHandler

class Log_Collector():
    def __init__(self):
        if not os.path.exists('logs'):
            os.makedirs('logs')
        fName = '{}/{}'.format(os.path.dirname(os.getcwd()),'logs/dk_log.log')
        if not os.path.isfile(fName):
            fName = 'logs/dk_log.log'
        self.logger = logging.getLogger()
        conHandler = logging.StreamHandler()
        fileHandler = TimedRotatingFileHandler(filename=fName, when='midnight', backupCount=90, interval=1)

        conHandler.setLevel(logging.WARNING)
        fileHandler.setLevel(logging.INFO)

        logformatCon = logging.Formatter('%(asctime)s %(levelname)s %(message)s',datefmt='%d-%b-%y %H:%M:%S')
        logformatfile = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        conHandler.setFormatter(logformatCon)
        fileHandler.setFormatter(logformatfile)

        fileHandler.rotator=GZipRotator()

        self.logger.addHandler(conHandler)
        self.logger.addHandler(fileHandler)


        self.logger.setLevel(logging.INFO)


class GZipRotator:
    def __call__(self, source, dest):
        os.rename(source, dest)
        f_in = open(dest, 'rb')
        f_out = gzip.open("{}.gz".format(dest), 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        os.remove(dest)
