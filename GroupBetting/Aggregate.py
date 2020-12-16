from time import process_time
from mysql.connector import MySQLConnection
import pandas as pd
import numpy as np
from datetime import date
import time
import os
from tqdm import tqdm
from Configuration.Configuration import Configuration
# from GroupBetting.FeatureScore import FeatureScore

config = Configuration()
# algorithmScore = FeatureScore()

# get information of database
username = config.getUsername(config)
password = config.getPassword(config)
server = config.getServerName(config)
database_name = config.getDatabaseName(config)
class Aggregate():
    def __init__(self,file_name,score_output,output1):
        self.file_name = file_name
        self.score_output = score_output
        self.output1 = output1
    
    def compute_league_score(self,list_minor = None, list_major = None):
        """"
        >>> Input  : list_minor, list of number of match in minor league
                    list_major, list of number of match in major league

        >>> Output : league_score
        """
        def gini_score(lista):
            """
            >>> Input  : list of integer,each represents quantity of some class
            >>> Output : gini score
            ------------------------
            Example

            > Input  : [1,1]
            > Output : .5
            """
            sum_match = sum(lista)

            return 1 - sum(map(lambda x:(x/sum_match)**2,lista))

        gini_minor = gini_score(list_minor)
        gini_major = gini_score(list_major)
        if len(list_minor) == 0:
            league_score = (gini_major + 3/2) * (2/5)
        elif len(list_major) == 0:
            league_score = (gini_minor + 5/2) * (2/7)
        else:
            minor_score = (gini_minor + 5/2) * (2/7)
            major_score = (gini_major + 3/2) * (2/5)
            league_score = (3 * (minor_score + 1) + (major_score + 2)) * (1/9)
        return league_score
    
    def getScoreFromDatabase(self):
        
        try:
            conn = MySQLConnection(user = username, password = password, host = '10.18.200.70', port = server, database = database_name)
            cursor = conn.cursor()
            cursor.callproc('SPU_AIML_UpdateScanStatus',[date.today(),None])
            conn.commit()
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()

    
    def aggregate(self,MAJOR_LEAGUE_LIST):

        # print("START AGGREGATE !")

        def process_league(list_of_league):
            """
            >>> Input  : list of leagues
            >>> Output : league_score,
                        number of minor leagues
            """
            # major,minor,list_league = [],[],set()
            major,minor = [],[]
            for league in list_of_league:
                # list_league.add(str(league))
                if league in MAJOR_LEAGUE_LIST:
                    major.append(league)
                else:
                    minor.append(league)
            league_score = self.compute_league_score(list_minor=minor,list_major=major)
            # return (league_score,','.join(list_league))
            return league_score
        
        def check_transid_is_empty_string(transid):
            if transid == '':
                return 0
            else:
                return len(transid.split(','))

        def process_time(list_of_time_score):
            """
            >>> Input  : list of time score
            >>> Output : time_score_in_a_match,  
                         number of effective match,
                         match_score,
                         num_joining_match
            """
            num_joining_match = len(list_of_time_score)
            new_array = np.asarray(list_of_time_score)
            new_array = new_array[new_array>0]
            if np.sum(new_array) == 0:
                time_score,num_eff_match,match_score = 0,0,0
            else:
                time_score = np.mean(new_array)
                num_eff_match = len(new_array)
                match_score = num_eff_match / num_joining_match
            return (time_score,
                    num_eff_match,
                    match_score,
                    num_joining_match)

        # baseline result 
        RESULTS = pd.read_csv(os.path.join(self.output1,self.file_name),names=['bet_type','time_score','leagueid','bet_count'])
        # print("BASELINE RESULTS",'********************',RESULTS.head(),sep='\n')
        # Aggregate with multilevel index
        SCORE = RESULTS.groupby('bet_type').agg(lambda x: list(x))
        # print("GROUPBY",'********************',SCORE.head(),sep='\n')
        # print("END AGGREGATE !")
        # print("START SCORING !")
        # process league column
        # SCORE['process_league'] = SCORE['league'].apply(process_league)
        SCORE['league_score'] = SCORE['leagueid'].apply(process_league)
        # SCORE['list_league'] = SCORE['process_league'].apply(lambda z : z[1])

        # process time score column | time_score -->  num_eff_match --> match_score --> num_joining_match
        SCORE['process_time'] = SCORE['time_score'].apply(process_time)
        SCORE['time_score'] = SCORE['process_time'].apply(lambda z : z[0])
        
        SCORE['num_effective_match'] = SCORE['process_time'].apply(lambda z : z[1])
        SCORE['match_score'] = SCORE['process_time'].apply(lambda z : z[2])
        SCORE['num_joining_match'] = SCORE['process_time'].apply(lambda z : z[3])

        # process match column
        # SCORE['list_match'] = SCORE['match'].apply(lambda z : ','.join(z))

        # process bet count column
        SCORE['bet_count'] = SCORE['bet_count'].apply(lambda z : sum(z))

        # process trans id column
        SCORE['total_score'] = SCORE['match_score'] + SCORE['time_score'] + SCORE['league_score']
        # SCORE['num_trans'] = SCORE['transid'].apply(check_transid_is_empty_string)
        # SCORE[SCORE['transid']==''].num_trans.apply(lambda z)

        # print("START FILTER !")
        # filter 
        FILTER = SCORE[SCORE.total_score==SCORE.total_score.max()]
        
        # final result !
        FINAL = FILTER  [
                        [
                            'time_score','match_score','league_score',
                            'num_effective_match','num_joining_match',
                            'bet_count'
                            # ,'transid','num_trans'
                        ]
                        ]
        # with open(os.path.join(self.score_output,self.file_name),'wb') as g:
        #     pickle.dump(final,g)
        FINAL.to_csv(os.path.join(self.score_output,self.file_name))
        # print("FINAL",'********************',FILTER.head(),sep='\n')
        # print("RESULTS SAVED SUCCESSFULLY !")