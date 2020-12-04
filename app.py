from datetime import datetime
from flask import Flask,Response, jsonify, request, render_template
import json
import pickle
import os
from os import environ
import logging
import _thread
import uuid
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import datetime
import time
import multiprocessing
import concurrent.futures
import pyodbc
from Configuration.Configuration import Configuration
from GroupBetting.FeatureScore import FeatureScore
from GroupBetting.AggregateDatabase import AggregateDatabase

config = Configuration()
algorithmScore = FeatureScore()
aggregate = AggregateDatabase()

# get information all ticket of each match
save_dir =config.GetSaveDirectoryModel(config)
path_csv =config.GetPathCsvFile(config)
filecsv_name = config.GetNameFile(config)
filemajorleague_name = config.GetMajorLeagueName(config)
log_name = config.GetLogName(config)

# get information of database
username = config.getUsername(config)
password = config.getPassword(config)
server = config.getServerName(config)
database_name = config.getDatabaseName(config)
#logging.basicConfig(filename=os.path.join(save_dir,log_name),level=logging.INFO)

def readMatchCSV():
    listMatches = pd.read_csv(path_csv + filecsv_name)
    return listMatches

def saveDataInDatabase():
    conn = pyodbc.connect('Driver = {SQL Server};Server ='+server+';Database ='+database_name+';UID ='+username+';PWD='+password)

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM database_name.table')

def getDatefromDF(dfmatches):
    getFristdate = dfmatches['transdate'][0]
    getDate = getFristdate.split()
    date = getDate[0]
    return date



if __name__ == '__main__':
    ## code to test
    match_league_map = pd.read_csv(path_csv+'match_league_sport.csv').set_index('matchid').to_dict(orient='index')

    bet_type_list = [1,3,7,8]
    listMatches = readMatchCSV()
    matchesLiveIndicator = listMatches[listMatches.liveindicator == 1]

    df_majorleague = pd.read_csv(path_csv + filemajorleague_name)
    majorLeagueList = df_majorleague.LeagueId.unique()

    ## code to test
    matchesLiveIndicator['leagueid'] = matchesLiveIndicator['matchid'].apply(lambda z : match_league_map[z]['leagueid'])

    matchesLiveIndicator = matchesLiveIndicator[['custid','matchid','transid','transdate','leagueid','bettype']]
    date = getDatefromDF(matchesLiveIndicator)
    
    matchesLiveIndicator['transdate'] = matchesLiveIndicator['transdate'].apply(lambda z: algorithmScore.distance_time(algorithmScore.separate(date+' '+'0:0:0.0'),
                                                                                                                       algorithmScore.separate(z)))
    matchesLiveIndicator.sort_values('transdate', inplace=True)
    matches = matchesLiveIndicator.matchid.unique()
    my_list = []
    for match in matches:
        for bet_type in bet_type_list:
            my_list.append((match,bet_type))
    print(f"Number Combinations {len(my_list)}")

    my_dict = {}
    id = 0
    my_trans = []
    start_time = time.time()
    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = [executor.submit(algorithmScore.calculateTotalScore,[element, matchesLiveIndicator]) for element in my_list]
        
        for f in concurrent.futures.as_completed(results):
            infor_of_couples = f.result()[0]
            trans = f.result()[1]
            my_trans += list(trans)
            for info in infor_of_couples:
               my_dict[id] = info
               id += 1

    print("TOTAL IMPLEMENTATION TIME %.0f SECONDS" % (time.time() - start_time))

    aggregate.aggregateScoreCouple(my_dict)
    print("***********************************************************************************************************************************************************************************")
    print("TOTAL IMPLEMENTATION TIME %.0f SECONDS" % (time.time() - start_time))
    


