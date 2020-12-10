import pandas as pd
import argparse 
import warnings
import os
warnings.filterwarnings("ignore")
import datetime
from Configuration.Configuration import Configuration
from multiprocessing import Value

config = Configuration()
path_csv = config.GetPathCsvFile(config)
# print(f"path csv {path_csv}")
filecsv_name = os.path.join(path_csv,config.GetNameFile(config))
name2 = os.path.join(path_csv,config.GetMajorLeagueName(config))
# log_name = config.GetLogName(config)
name1 = os.path.join(path_csv,config.GetMatchLeagueMapping(config))
class ReadData():
    def __init__(self):
        # self.date = date
        pass
    
    def read_data(self,filecsv_name,name1,name2):
        # self.data = pd.read_csv(filecsv_name,encoding='ISO-8859-1')

        self.data = pd.read_csv(filecsv_name)

        
        
        # name = 'match_league_sport'
        self.match_league_map = pd.read_csv(name1,error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
        # self.DATE['leagueid'] = self.DATE['matchid'].apply(lambda z : match_league_map[z]['leagueid'])
        print(f'NUM MATCHES {len(self.match_league_map)}')

        # self.DATE = self.DATE[['custid','matchid','transid','transdate','leagueid','bettype']]
        
        # pick up match list
        # matches = DATE.matchid.unique()
        # print(f"number of matches {len(matches)}")

        # self.candidat = self.DATE.groupby(['matchid','bettype']).custid.nunique()
        # self.my_list = self.candidat[self.candidat>1].index.values
        # for match in matches:
        #     for bet_type in bet_type_list:
        #         my_list.append((match,bet_type))
        # print(f"NUMBER COMBINATIONS {len(self.my_list)}")

        MAJOR_LEAGUE = pd.read_csv(name2)
        self.major_league_list = MAJOR_LEAGUE.LeagueId.unique()
        

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

        self.DATE = self.data[self.data.liveindicator==1]
        self.DATE = self.DATE[['custid','matchid','transid','transdate','bettype']]
        
        self.DATE.sort_values('transdate',inplace=True)

        getFristdate = self.data['transdate'][0]
        getDate = getFristdate.split()
        self.date = getDate[0]

        self.DATE['transdate'] = self.DATE['transdate'].apply   (lambda z: distance_time    (
                                                                                            separate(self.date+' '+'0:0:0.0'),
                                                                                            separate(z)
                                                                                            )
                                                                )
        print   (   f"DAY {self.date}"
                    # f"NUMBER COMBINATIONS {len(self.my_list)}",
                    # # f"NUMBER CUSTOMERS {len(self.candidat)}",
                    # sep='\n'
                )
        print   ("READ DATA & PREPROCESS SUCCESSFULLY !",self.DATE.head(),sep='\n')

if __name__ == "__main__":

    # parser = argparse.ArgumentParser()

    # parser.add_argument('--prefix',type=str,required=True)
    # parser.add_argument('--date',type=str,required=True)
    # parser.add_argument('--suffix',type=str,default='.csv')
    # parser.add_argument('--name1',type=str,required=True)
    # parser.add_argument('--name2',type=str,required=True)

    # args = parser.parse_args()

    objlv1 = ReadData()
    objlv1.read_data(filecsv_name,name1,name2)
    objlv1.pre_process()

    # shared_df  = Value(pd.DataFrame,objlv1.DATE)
    print("READ DATA & PREPROCESS SUCCESSFULLY !",objlv1.DATE.head(),sep='\n')