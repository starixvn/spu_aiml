import json
import pandas as pd
from mysql.connector import MySQLConnection
# from Utilities import count_joining_combs

class GroupBettingDataAccess():
    def __init__(self):
        pass

    def insert_association_stats_staging(args):
        data_frame,config = args
        list_of_dict = data_frame.to_dict(orient="records")
        if len(list_of_dict) > 0:
            chunks = [list_of_dict[x:x+config.chunk_size] for x in range(0, len(list_of_dict), config.chunk_size)]
            try:
                conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                    host=config.aimlhost, port=config.aimlport, database=config.aimldb)
                cursor = conn.cursor()
                for chunk in chunks:
                    jsonList = json.dumps(chunk)
                    _,out1 = cursor.callproc('SPU_AIML_InsertAssociationStatsStaging', [jsonList, None])
                    # print()
                    if out1 is not None:
                        print(out1)
                    conn.commit()
                cursor.close()
                conn.close()
            except Exception as err:
                # logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
                print(f'{config.ENV} | Error in insert_association_stats_staging function: {err}')
                # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError
        else:
            pass
    
    def insert_association_suspicious_info(args):
        data_frame,config = args
        list_of_dict = data_frame.to_dict(orient="records")
        chunks = [list_of_dict[x:x+config.chunk_size] for x in range(0, len(list_of_dict), config.chunk_size)]
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cursor = conn.cursor()
            for chunk in chunks:
                jsonList = json.dumps(chunk)
                _,out1 = cursor.callproc('SPU_AIML_InsertAssociationSuspiciousInfo', [jsonList, None])
                if out1 is not None:
                    print(out1)
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            # logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            print(f'{config.ENV} | Error in insert_association_suspicious_info function: {err}')
            # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
    
    def insert_association_by_AI(args):
        data_frame,config = args
        list_of_dict = data_frame.to_dict(orient="records")
        chunks = [list_of_dict[x:x+config.chunk_size] for x in range(0, len(list_of_dict), config.chunk_size)]
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cursor = conn.cursor()
            for chunk in chunks:
                jsonList = json.dumps(chunk)
                _,out1 = cursor.callproc('SPU_AIML_InsertAssociationByAI', [jsonList, None])
                if out1 is not None:
                    print(out1)
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            # logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            print(f'{config.ENV} | Error in insert_association_by_AI function: {err}')
            # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
    
    def insert_association_stats(args):
        data_frame,date_insert,config = args
        list_of_dict = data_frame.to_dict(orient="records")
        chunks = [list_of_dict[x:x+config.chunk_size] for x in range(0, len(list_of_dict), config.chunk_size)]
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cursor = conn.cursor()
            for chunk in chunks:
                jsonList = json.dumps(chunk)
                _,_,out1 = cursor.callproc('SPU_AIML_InsertAssociationStats', [jsonList,date_insert, None])
                if out1 is not None:
                    print(out1,jsonList,sep='\n')
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            # logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            print(f'{config.ENV} | Error in insert_association_stats function: {err}')
            # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError

    def insert_association_by_AI_to_CTS(args):
        data_frame,date_insert,config = args
        list_of_dict = data_frame.to_dict(orient="records")
        chunks = [list_of_dict[x:x+config.chunk_size] for x in range(0, len(list_of_dict), config.chunk_size)]
        try:
            conn = MySQLConnection(user=config.ctsuser, password=config.ctspwd,
                                host=config.ctshost, port=config.ctsport, database=config.ctsdb)
            cursor = conn.cursor()
            for chunk in chunks:
                jsonList = json.dumps(chunk)
                _,_,out1 = cursor.callproc('CTS_DC_Association_InsertAssociationByAI', [jsonList,date_insert, None])
                if out1 is not None:
                    print(out1)
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            # logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            print(f'{config.ENV} | Error in insert_association_by_AI_to_CTS function: {err}')
            # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
    
    def get_association_stats_staging(args):
        string_format_of_cus_list,config = args
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                            host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            _,out1 = cur.callproc('SPU_AIML_GetAssociationStatsStaging',[string_format_of_cus_list, None])
            if out1 is not None:
                print(out1)
                # logging.error(f'{ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1}')
                # message_telegram = f'{ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1}'
                # SendLogTelegram.send_message(message_telegram)
            dba_results = [r.fetchall() for r in cur.stored_results()]
            conn.commit()
            cur.close()
            conn.close()
            if len(dba_results[0]) == 0:
                return []
            df = pd.DataFrame(dba_results[0], columns=[
                "C1",
                "C2",
                "TS",
                "ML",
                "BL",
                "LeagueID",
                "IsMajorLeague",
                "TJC",
                "IsNew"
                ])
            return df
        except Exception as err:
            # logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            print(f'{config.ENV} | Error in get_association_stats_staging function: {err}')
            # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError

    def get_association_stats(args):
        min_cus,max_cus,config = args
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                            host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            _,_,out1 = cur.callproc('SPU_AIML_GetAssociationStats',[int(min_cus),int(max_cus), None])
            if out1 is not None:
                print(out1)
                # logging.error(f'{ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1}')
                # message_telegram = f'{ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1}'
                # SendLogTelegram.send_message(message_telegram)
            dba_results = [r.fetchall() for r in cur.stored_results()]
            conn.commit()
            cur.close()
            conn.close()
            if len(dba_results[0]) == 0:
                return []
            df = pd.DataFrame(dba_results[0], columns=[
                "C1"
                ,"C2"
                ,"TS"
                ,"ML"
                ,"BL"
                ,"LeagueID"
                ,"IsMajorLeague"
                ,"TJC"
                ,"IsNew"
                ,"AccTS"
                ,"AccMS"
                ,"AccLS"
                ,"AccTJD"
                ,"AccTJSC"
                ])
            # fill 0 to NaN
            df['AccTS'].fillna(0, inplace=True)
            df['AccMS'].fillna(0, inplace=True)
            df['AccLS'].fillna(0, inplace=True)
            df['AccTJD'].fillna(0, inplace=True)
            df['AccTJSC'].fillna(0, inplace=True)

            # df['TJC'] = df.apply(
            # lambda z: count_joining_combs(z['C1'], z['C2'],daily_cus_dict), axis=1)
        
            df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
            
            df = df.astype({"sample_id": 'int64'})
            df['TS'] = df['TS'].astype('float')
            df['AccTS'] = df['AccTS'].astype('float')
            df['AccMS'] = df['AccMS'].astype('float')
            df['AccLS'] = df['AccLS'].astype('float')
            return df
        except Exception as err:
            # logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            print(f'{config.ENV} | Error in get_association_stats function: {err}')
            # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError

# class AssociationByIPDataAccess():
#     pass

class CommonDataAccess():
    def __init__(self):
        pass

    def truncate_association_stats_staging(args):
        config = args
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                        host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            # Truncate table AssociationStatsStaging
            cur.callproc('SPU_AIML_DBA_Truncate_Table',['AssociationStatsStaging'])
            conn.commit()
        except Exception as err:
            # logging.error(f'{ENV} | Error Update Staging Status: {err}')
            print(f'{config.ENV} | Error in truncate_association_stats_staging function: {err}')
            # message_telegram = f'{ENV} | Error Update Staging Status: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
    
    def update_scan_status(args):
        date_insert,config = args
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                    host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            # update table SystemParameter
            # cur.callproc('SPU_AIML.SPU_AIML_UpdateScanStatus',
            #             [date_insert, None])
            _,out1 = cur.callproc('SPU_AIML_UpdateScanStatus',[date_insert, None])
            if out1 is not None:
                print(out1)
                # logging.error(f'{ENV} | Error return from SP SPU_AIML_UpdateScanStatus: {out1}')
                # message_telegram = f'{ENV} | Error return from SP SPU_AIML_UpdateScanStatus: {out1}'
                # SendLogTelegram.send_message(message_telegram)
            conn.commit()

            cur.close()
            conn.close()
        except Exception as err:
            # logging.error(f'{ENV} | Error Update Staging Status: {err}')
            print(f'{config.ENV} | Error in update_scan_status function: {err}')
            # message_telegram = f'{ENV} | Error Update Staging Status: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
    
    def update_association_stats_staging_status(args):
        string_format_of_cus_list,config = args
        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            # cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [
            #             args[0], None])
            _,out1 = cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [string_format_of_cus_list, None])
            if out1 is not None:
                print(out1)
                # logging.error(f'{ENV} | Error return from SP SPU_AIML_UpdateAssociationStatsStagingStatus: {out1}')
                # message_telegram = f'{ENV} | Error return from SP SPU_AIML_UpdateAssociationStatsStagingStatus: {out1}'
                # SendLogTelegram.send_message(message_telegram)
            conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            # logging.error(f'{ENV} | Error Update Staging Status: {err}')
            print(f'{config.ENV} | Error in update_association_stats_staging_status function: {err}')
            # message_telegram = f'{ENV} | Error Update Staging Status: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
