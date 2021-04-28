import json
import time

import pandas as pd
from mysql.connector import MySQLConnection

from DataAccess.AssociationIPDA.AssociationByIPCTS import AssociationByIPCTSDA
from Helper import Utilities
from Configuration.Configuration import config


class CommonDA:
    def __init__(self, db='aiml'):
        if db == 'aiml':
            self.conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                        host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        elif db == 'cts':
            self.conn = MySQLConnection(user=config.ctsuser, password=config.ctspwd,
                                   host=config.ctshost, port=config.ctsport, database=config.ctsdb)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def insert(self, proc_name, batches_data, error_message, date_insert=None, write_error_to_csv=False, save_ip=False, save_ip_date=None, to_json=False):
        try:
            for data in batches_data:
                if to_json:
                    jsonList = json.dumps(data)
                else:
                    jsonList = data
                if date_insert:
                    proc_output = self.cursor.callproc(proc_name, [jsonList, date_insert, None])
                else:
                    proc_output = self.cursor.callproc(proc_name, [jsonList, None])

                if proc_output[-1] is not None:
                    if write_error_to_csv:
                        dataSP_error = json.loads(jsonList)
                        df_dataSP_error = pd.DataFrame(dataSP_error)
                        df_dataSP_error.to_csv(config.errorFolder+f"file_error_SP_data_{time.time()}.csv", index=False)
                    write_error_message_telegram = f'GROUP BETTING | {config.ENV} | ERROR | From {proc_name}: {proc_output[-1]} | With JSON {jsonList}'
                    Utilities.notify_logging(write_error_message_telegram)

                dba_results = [r.fetchall() for r in self.cursor.stored_results()]
                if save_ip:
                    if config.transfer_ip:
                        save_dba_results(dba_results, save_ip_date)
                self.conn.commit()

        except Exception as err:
            Utilities.notify_logging(error_message + str(err))
            raise ValueError

    def get(self, proc_name, id_data, message_telegram):
        try:
            proc_output = self.cursor.callproc(proc_name, id_data)
            if proc_output[-1] is not None:
                message_telegram = f'GROUP BETTING | {config.ENV} | ERROR | From {proc_name}: {proc_output[-1]} | With CusList {id_data}'
                Utilities.notify_logging(message_telegram)
            dba_results = [r.fetchall() for r in self.cursor.stored_results()]
            self.conn.commit()
            return dba_results
        except Exception as err:
            Utilities.notify_logging(message_telegram + str(err))
            raise ValueError

    def update(self, proc_name, custid_list, message_telegram):
        try:
            proc_output = self.cursor.callproc(proc_name, [custid_list, None])
            if proc_output[-1] is not None:
                message_telegram = f'GROUP BETTING | {config.ENV} | ERROR | From {proc_name}: {proc_output[-1]} | With CusList {custid_list}'
                Utilities.notify_logging(message_telegram)
            self.conn.commit()

        except Exception as err:
            Utilities.notify_logging(message_telegram + str(err))
            raise ValueError

    def truncate(self, table_name):
        try:
            self.cursor.callproc('SPU_AIML_DBA_Truncate_Table', [table_name])
            self.conn.commit()
        except Exception as err:
            error_message = f'GROUP BETTING | {config.ENV} | ERROR | Truncate table: {table_name} failed: '
            Utilities.notify_logging(error_message + str(err))
            raise ValueError


def save_dba_results(dba_results, date_insert):
    if len(dba_results[0]) > 0:
        df_CTS = pd.DataFrame(dba_results[0], columns=[
            "C1",
            "C2"])
        full_data_IPCTS_dba = df_CTS.to_json(orient="records")
        association_by_IPCTS_da = AssociationByIPCTSDA()
        association_by_IPCTS_da.insert(full_data_IPCTS_dba, date_insert=date_insert)
