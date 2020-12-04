from time import process_time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import datetime
import time
from sklearn.cluster import DBSCAN
from tqdm import tqdm
from Configuration.Configuration import Configuration
from GroupBetting.FeatureScore import FeatureScore

config = Configuration()
algorithmScore = FeatureScore()

# get information of database
username = config.getUsername(config)
password = config.getPassword(config)
server = config.getServerName(config)
database_name = config.getDatabaseName(config)
class AggregateDatabase():
    """description of class"""
    def __init__(self, *args):
        pass
    
    def process_league(self, list_of_league, major_league_list):
        """
        >>> Input  : list of leagues
        >>> Output : league_score,
                    number of minor leagues
        """
        major = []
        minor = []
        for league in list_of_league:
            if league in major_league_list:
                major.append(league)
            else:
                minor.append(league)
        league_score = algorithmScore.compute_league_score(list_minor=minor, list_major=major)
        return (league_score, len(minor))

    def process_time(self, list_of_time_score):
        """
        >>> Input  : list of time score
        >>> Output : time_score_in_a_match,
                    number of joining match,
                    number of effective match,
                    match_score
        """
        num_joining_match = len(list_of_time_score)
        new_array = np.asarray(list_of_time_score)
        new_array = new_array[new_array > 0]

        if np.sum(new_array) == 0:
            time_score = 0
            num_eff_match = 0
            match_score = 0
        else:
            time_score = np.mean(new_array)
            num_eff_match = len(new_array)
            match_score = num_eff_match / num_joining_match
        return (time_score, num_joining_match, num_eff_match, match_score)

    def aggregateScoreCouple(self, results):
        start = time.time()
        df_resultsOfDate = pd.DataFrame(results.values(), index = results.keys())
        
        # Aggregate with multilevel index
        df_scoreOfDate = df_resultsOfDate.groupby(['couple','bet_type']).agg(lambda x: list(x))

        # process league column
        df_scoreOfDate['process_league'] = df_scoreOfDate['league'].apply(self.process_league)
        df_scoreOfDate['league_score'] = df_scoreOfDate['process_league'].apply(lambda z: z[0])
        df_scoreOfDate['num_minor'] = df_scoreOfDate['process_league'].apply(lambda z: z[1])

        # process time score column | time_score --> num_joining_match --> num_eff_match --> match_score
        df_scoreOfDate['process_time'] = df_scoreOfDate['time_score'].apply(self.process_time)
        df_scoreOfDate['time_score'] = df_scoreOfDate['process_time'].apply(lambda z: z[0])
        df_scoreOfDate['num_match'] = df_scoreOfDate['process_time'].apply(lambda z: z[1])
        df_scoreOfDate['num_effective_match'] = df_scoreOfDate['process_time'].apply(lambda z: z[2])
        df_scoreOfDate['match_score'] = df_scoreOfDate['process_time'].apply(lambda z: z[3])

        # process bet count column
        df_scoreOfDate['bet_count'] = df_scoreOfDate['bet_count'].apply(lambda z: sum(z))

        # process trans id column
        df_scoreOfDate['transid'] = df_scoreOfDate['transid'].apply(lambda z: ' '.join(z))

        # filter
        filterGroupBetting = df_scoreOfDate[(df_scoreOfDate.time_score < 0) | ((df_scoreOfDate.time_score == 0) & (df_scoreOfDate.num_minor >= 5))]

        # final result
        df_finalResults = filterGroupBetting[['time_score', 'match_score', 'league_score', 'num_effective_match', 'num_match', 'num_minor', 'bet_count', 'transid']]

        print(f"IMPLEMENTATION TIME {time.time() - start} seconds")
        df_finalResults.head()
        # for index, row in df_finalResults.iterrows():
        #     couple = index.get_level_values