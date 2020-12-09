
import os
import pandas as pd
class InsertDataBase():
    def __init__(self,trans):
        self.trans = trans
    
    def insert_2_table_2(self):
        pass

    def insert_transactions(self,data,output):
        # print("START INSERT !")
        cols =  [
                'transid','matchid','leagueid','custid','transdate','liveindicator','bettype',
                'stake','odds','oddsspread','hdp1','hdp2','betfrom','liveawayscore','livehomescore'
                ]
        TRANSACTIONS = (data[data.transid.isin([int(x) for x in self.trans if x != ''])][cols]).reset_index(drop=True)
        TRANSACTIONS.to_csv(os.path.join(output,'transactions.csv'))
        print(f"{TRANSACTIONS.shape[0]} TRANSACTIONS HAVE BEEN INSERTED SUCCESSFULLY !")
        print("TRANSACTIONS HEAD",'****************',TRANSACTIONS.head(),sep='\n')