import json
import time

import pandas as pd
from mysql.connector import MySQLConnection

from Utilities import FunctionSupport
from app import config


class CommonDA:
    def insert_single(self, proc_name, data):
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                   host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            # update table SystemParameter
            proc_output = cur.callproc(proc_name, data)
            if proc_output[-1] is not None:
                message_telegram = f'{config.ENV} | Error updating data: {proc_name} {proc_output[-1]}'
                FunctionSupport.notify_logging(message_telegram)
            dba_results = [r.fetchall() for r in cur.stored_results()]
            conn.commit()

            cur.close()
            conn.close()
            return dba_results

        except Exception as e:
            message_telegram = f"{config.ENV} | Error insert data: {e}"
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError

    def insert_many(self, proc_name, batches_data, date_insert, write_error_to_csv=False):
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                    host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cursor = conn.cursor()
            for data in batches_data:
                jsonList = json.dumps(data)
                proc_output = cursor.callproc(proc_name, [jsonList, date_insert, None])
                if proc_output[-1] is not None:
                    if write_error_to_csv:
                        dataSP_error = json.loads(jsonList)
                        df_dataSP_error = pd.DataFrame(dataSP_error)
                        df_dataSP_error.to_csv(config.errorFolder+f"file_error_SP_data_{time.time()}.csv",index=False)
                    message_telegram = f'{config.ENV} | Error return from {proc_name}: {proc_output[-1]} | With JSON {jsonList}'
                    FunctionSupport.notify_logging(message_telegram)
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            message_telegram = f'{config.ENV} | Error insert table {proc_name} in SPU DB: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError

    def get(self, proc_name, id_data):
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd, host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            proc_output = cur.callproc(proc_name, id_data)
            if proc_output[-1] is not None:
                message_telegram = f'{config.ENV} | Error return from SP {proc_name}: {proc_output[-1]} | With CusList {id_data}'
                FunctionSupport.notify_logging(message_telegram)
            dba_results = [r.fetchall() for r in cur.stored_results()]
            conn.commit()
            cur.close()
            conn.close()
            return dba_results
        except Exception as err:
            message_telegram = f'{config.ENV} | Error get data from {proc_name} in SPU when on-the-fly: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError

    def update(self, proc_name, custid_list):
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            proc_output = cur.callproc(proc_name, [custid_list, None])
            if proc_output[-1] is not None:
                message_telegram = f'{config.ENV} | Error return from SP {proc_name}: {proc_output[-1]} | With CusList {custid_list}'
                FunctionSupport.notify_logging(message_telegram)
            conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            message_telegram = f'{config.ENV} | Error Update Staging Status: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError
