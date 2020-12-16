
import os
import pandas as pd
import json
from mysql.connector import MySQLConnection
class InsertDataBase():
    def __init__(self,trans):
        self.trans = trans
    
    def insert_2_table_2(self):
        pass

    def insert_transactions(self,data,output):
        # print("START INSERT !")
        cols = ['transid', 'custid', 'matchid', 'username2', 'trandate', 'winlostdate', 'oddsspread', 'odds', 'hdp1', 'hdp2', 'stake', 'status',
                'statusid', 'winlost', 'actualstake', 'actualrate', 'livehomescore', 'liveawayscore', 'liveindicator', 'bettype', 'betteam', 'betfrom', 'arecommend'
                'mrecommend', 'srecommend', 'currency', 'ip', 'balance']
        TRANSACTIONS = (data[data.transid.isin([int(x) for x in self.trans if x != ''])][cols]).reset_index(drop=True)
        TRANSACTIONS.rename(columns = {
                                        "transid":"Trans",
                                        "custid": "C",
                                        "matchid": "M",
                                        "username2": "Usn2",
                                        "trandate": "TD",
                                        "winlostdate": "WLD",
                                        "oddsspread": "OS",
                                        "odds": "O",
                                        "hdp1": "Hdp1",
                                        "hdp2": "Hdp2",
                                        "stake": "Stake",
                                        "status": "S",
                                        "statusid": "SID",
                                        "winlost": "WL",
                                        "actualstake": "AS",
                                        "actualrate": "AR",
                                        "livehomescore": "LHS",
                                        "liveawayscore": "LAW",
                                        "liveindicator": "LI",
                                        "bettype": "BT",
                                        "betteam": "BC",
                                        "betfrom": "BF",
                                        "arecommend": "RA",
                                        "mrecommend": "RM",
                                        "srecommend": "RS",
                                        "currency": "Cur",
                                        "ip": "IP",
                                        "balance": "Balance"
        })
        convertJSON = TRANSACTIONS.to_json(orient="records")
        parsed = json.loads(convertJSON)
        jsonList = json.dumps(parsed, indent = 4)
        try:
            conn = MySQLConnection(user = 'darius.vn', password = '1qaz@Wsx3edc', host = '10.18.200.70', port = '3037', database = 'SPU_AIML')
            cursor = conn.cursor()
            cursor.callproc('SPU_AIML_InsertSuspiciousTickets',[jsonList,None])
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            print(err)
        
        print(f"{TRANSACTIONS.shape[0]} TRANSACTIONS HAVE BEEN INSERTED SUCCESSFULLY !")
        print("TRANSACTIONS HEAD",'****************',TRANSACTIONS.head(),sep='\n')
