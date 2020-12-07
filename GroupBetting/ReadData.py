import pandas as pd
import argparse 
# from helpers import *
import datetime

class Read_data():
    def __init__(self,date):
        self.date = date
        # pass
    
    def read_data(self,prefix,suffix,name1,name2):
        self.data = pd.read_csv(prefix+self.date+suffix)

        # name = 'match_league_sport'
        match_league_map = pd.read_csv(name1+suffix).set_index('matchid').to_dict(orient='index')
        self.data['leagueid'] = self.data['matchid'].apply(lambda z : match_league_map[z]['leagueid'])

        self.DATE = self.data[self.data.liveindicator==1]
        self.DATE = self.DATE[['custid','matchid','transid','transdate','leagueid','bettype']]
        # pick up match list
        # matches = DATE.matchid.unique()
        # print(f"number of matches {len(matches)}")
        self.candidat = self.DATE.groupby(['matchid','bettype']).custid.nunique()
        self.my_list = self.candidat[self.candidat>1].index.values
        # for match in matches:
        #     for bet_type in bet_type_list:
        #         my_list.append((match,bet_type))
        print(f"NUMBER COMBINATIONS {len(self.my_list)}")

        MAJOR_LEAGUE = pd.read_csv(name2+suffix)
        self.major_league_list = MAJOR_LEAGUE.LeagueId.unique()
        print(f"NUMBER OF MAJOR LEAGUES {len(self.major_league_list)}")
    
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
        
        self.DATE['transdate'] = self.DATE['transdate'].apply   (lambda z: distance_time    (
                                                                                            separate(self.date+' '+'0:0:0.0'),
                                                                                            separate(z)
                                                                                            )
                                                                )
        self.DATE.sort_values('transdate',inplace=True)

# if __name__ == "__main__":

#     parser = argparse.ArgumentParser()

#     parser.add_argument('--prefix',type=str,required=True)
#     parser.add_argument('--date',type=str,required=True)
#     parser.add_argument('--suffix',type=str,default='.csv')
#     parser.add_argument('--name1',type=str,required=True)
#     parser.add_argument('--name2',type=str,required=True)

#     args = parser.parse_args()

#     obj = Read_data(args.date)
#     obj.read_data(args.prefix,args.suffix,args.name1,args.name2)
#     obj.pre_process()
    
#     print(obj.DATE.head())