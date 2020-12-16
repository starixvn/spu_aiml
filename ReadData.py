import pandas as pd
import argparse 
import warnings
import os
warnings.filterwarnings("ignore")
import datetime
import time
import concurrent.futures
from Configuration.Configuration import Configuration
import multiprocessing as mp
from tqdm import tqdm
config = Configuration()
path_csv = config.GetPathCsvFile(config)
# print(f"path csv {path_csv}")
filecsv_name = os.path.join(path_csv,config.GetNameFile(config))
name2 = os.path.join(path_csv,config.GetMajorLeagueName(config))
# log_name = config.GetLogName(config)
name1 = os.path.join(path_csv,config.GetMatchLeagueMapping(config))
file_output = config.GetFileOutput(config)

class ReadData():
    def __init__(self):
        # self.date = date
        pass
    
    def read_data(self,filecsv_name,name1,name2):
        self.data = pd.read_csv(filecsv_name,encoding='ISO-8859-1')

        # self.data = pd.read_csv(filecsv_name)
        
        # name = 'match_league_sport'
        # self.match_league_map = pd.read_csv(name1,error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
        # self.DATE['leagueid'] = self.DATE['matchid'].apply(lambda z : match_league_map[z]['leagueid'])
        # print(f'NUM MATCHES {len(self.match_league_map)}')

        # self.DATE = self.DATE[['custid','matchid','transid','transdate','leagueid','bettype']]
        self.DATE = self.data[self.data.liveindicator==1]
        self.DATE = self.DATE[['custid','matchid','transid','transdate','bettype']]
        # pick up match list
        self.matches = self.DATE.matchid.value_counts().sort_values(ascending=False).index.to_list()
        print(f"number of matches {len(self.matches)}",f"MAX MATCH {self.matches[0]}")

        # self.candidat = self.DATE.groupby(['matchid','bettype']).custid.nunique()
        # self.my_list = self.candidat[self.candidat>1].index.values
        # self.bet_type_list = [1,3,7,8]
        # self.my_list = []
        # for match in self.matches:
        #     for bet_type in self.bet_type_list:
        #         self.my_list.append((match,bet_type))
        # print(f"NUMBER COMBINATIONS {len(self.my_list)}")

        # MAJOR_LEAGUE = pd.read_csv(name2)
        # self.major_league_list = MAJOR_LEAGUE.LeagueId.unique()
        

    def pre_process(self):

        def separate(transdate):
            """
            >>> Input  :    '2020-09-26 7:31:01.872'

            >>> Output :    (2020,9,26,7,31,1)
            """
            date,hms = transdate.split(' ')[0].split('-'),transdate.split(' ')[1].split('.')[0].split(':')
            year,month,day = int(date[0]),int(date[1]),int(date[2])
            hour,min,sec = int(hms[0]),int(hms[1]),int(hms[2])
            return (year,month,day,hour,min,sec)

        def distance_time(transdate1,transdate2):
            """
            >>> Input  :    transdate 1 : (2020,9,26,7,28,1)

                            transdate 2 : (2020,9,26,7,31,1)

            >>> Output :    180 seconds
            """
            
            a = datetime.datetime(*transdate1)
            b = datetime.datetime(*transdate2)
            c = b-a
            return int(c.total_seconds())

        
        
        self.DATE.sort_values('transdate',ignore_index=True,inplace=True)
        print("SORTED DF",self.DATE.head(),sep='\n')

        self.date = self.DATE['transdate'][0]
        # getDate = getFristdate.split()
        # self.date = getDate[0]

        self.DATE['transdate'] = self.DATE['transdate'].apply   (lambda z: distance_time    (
                                                                                            separate(self.date),
                                                                                            separate(z)
                                                                                            )
                                                                )
        print   (   f"DAY {self.date}"
                    # f"NUMBER COMBINATIONS {len(self.my_list)}",
                    # # f"NUMBER CUSTOMERS {len(self.candidat)}",
                    # sep='\n'
                )
        print   ("READ DATA & PREPROCESS SUCCESSFULLY !",self.DATE.head(),sep='\n')
    
# def break_into_multi_files(args):
#     ns,match = args[0],args[1]
#     DF = ns.df
#     # DF = DF[(DF.matchid==comb[0])&(DF.bettype==comb[1])]
#     DF = DF[DF.matchid==match]
#     if DF.custid.nunique() > 1:
#         DF.to_csv(os.path.join(file_output,f"M{match}.csv"),index=False)

if __name__ == "__main__":

    start_time = time.time()

    objlv1 = ReadData()
    objlv1.read_data(filecsv_name,name1,name2)
    objlv1.pre_process()
    # mgr = mp.Manager()
    # ns = mgr.Namespace()
    # ns.df = objlv1.DATE
    # with concurrent.futures.ProcessPoolExecutor() as executor:
            
    #     executor.map(break_into_multi_files,[(ns,match) for match in objlv1.matches])
    for idx in tqdm(range(len(objlv1.matches))):
        match = objlv1.matches[idx]
        M = objlv1.DATE[objlv1.DATE.matchid==match]
        for bt in [1,3,7,8]:
            B = M[M.bettype==bt]
            if B.custid.nunique() > 2:

                B.to_csv(os.path.join(file_output,f"{match}_{bt}.csv"),index=False)
        objlv1.DATE = objlv1.DATE.drop(objlv1.DATE[objlv1.DATE.matchid==match].index)
    
    print("***********************************","BROKEN SUCCESSFULLY !","%.0f SECONDS" % (time.time() - start_time),sep='\n')