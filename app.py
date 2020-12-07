from datetime import datetime
# from flask import Flask,Response, jsonify, request, render_template
import json
import pickle
import os
from os import environ
import logging
import _thread
import uuid
import pandas as pd
import argparse
import numpy as np
from tqdm import tqdm
import datetime
import time
import multiprocessing
import concurrent.futures
import pyodbc
import os
from Configuration.Configuration import Configuration
from GroupBetting.FeatureScore import Processing
from GroupBetting.AggregateDatabase import Aggregate
from GroupBetting.Insert import Insert
from GroupBetting.ReadData import Read_data

config = Configuration()
# algorithmScore = FeatureScore()
# aggregate = AggregateDatabase()

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

# def readMatchCSV():
#     listMatches = pd.read_csv(path_csv + filecsv_name)
#     return listMatches

def saveDataInDatabase():
    conn = pyodbc.connect('Driver = {SQL Server};Server ='+server+';Database ='+database_name+';UID ='+username+';PWD='+password)

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM database_name.table')

# def getDatefromDF(dfmatches):
#     getFristdate = dfmatches['transdate'][0]
#     getDate = getFristdate.split()
#     date = getDate[0]
#     return date

def submit_job(prefix,date,suffix,name1,name2,output1,output2,score_output,trans_output,match_output):

  # process_start_time = time.time()
    objlv1 = Read_data(date)
    objlv1.read_data(prefix,suffix,name1,name2)
    objlv1.pre_process()
    results,trans = [],set()
    print("READ DATA AND PREPROCESS SUCESSFULLY !",objlv1.DATE.head(3),sep='\n')
    total_combination = len(objlv1.my_list)
    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     results = [executor.submit(algorithmScore.calculateTotalScore,[element, matchesLiveIndicator]) for element in my_list]
    for j in range(4):
        match,bet_type = objlv1.my_list[j]

        league = objlv1.DATE.leagueid.unique()[0]
        objlv2 = Processing(objlv1.DATE[(objlv1.DATE.matchid==match)&(objlv1.DATE.bettype==bet_type)],
                                            match=match,bet_type=bet_type,league=league,total_combination=total_combination,order_of_combination=j+1,
                                            output1=output1,output2 = output2,match_output = match_output)

        objlv2.processing_a_match()
    print('\n')
    # print(f"START AGGREGATE")
    # for idx,file_name in enumerate(os.listdir(output1)):
    #   if (idx+1) % 5e2 == 0:
    #     print(f"{idx+1} files DONE !")
    for file_name in tqdm(os.listdir(output1),desc='AGGREGATING . . .'):
        objlv3 = Aggregate(file_name,score_output,output1)
        objlv3.aggregate(objlv1.major_league_list)
    print('\n')
    # print(f"START INSERT")
    for file_name in tqdm(os.listdir(output2),desc='INSERTING . . .'):
        if 'eff_trans' in file_name:
            with open(os.path.join(output2,file_name),'rb') as f:
                eff_trans = pickle.load(f)
                # print(f"EFF TRANS {eff_trans} | TYPE {type(eff_trans)}")
                trans = trans.union(eff_trans)
    objlv4 = Insert(trans)
    objlv4.insert_transactions(objlv1.data,trans_output)



if __name__ == '__main__':
    start_time = time.time()

    # parser = argparse.ArgumentParser()

    # parser.add_argument('--prefix',type=str,default='D:/Project/Formula_BET/MatchData/not_')
    # parser.add_argument('--date',type=str,required=True)
    # parser.add_argument('--suffix',type=str,default='.csv')
    # parser.add_argument('--name1',type=str,default='D:/Project/Formula_BET/MatchData/match_league_sport')
    # parser.add_argument('--name2',type=str,default='D:/Project/Formula_BET/MatchData/major_league')
    # parser.add_argument('--output1',type=str,default='D:/Project/Formula_BET/SaveData/output1')
    # parser.add_argument('--output2',type=str,default='D:/Project/Formula_BET/SaveData/output2')
    # parser.add_argument('--score_output',type=str,default='D:/Project/Formula_BET/SaveData/score_output')
    # parser.add_argument('--trans_output',type=str,default='D:/Project/Formula_BET/SaveData/trans_output')
    # parser.add_argument('--match_output',type=str,default='D:/Project/Formula_BET/SaveData/match_output')

    # args = parser.parse_args()

    submit_job(args.prefix,args.date,args.suffix,args.name1,args.name2,args.output1,args.output2,args.score_output,args.trans_output,args.match_output)

    
    print("***********************************************************************************************************************************************************************************")
    print("TOTAL IMPLEMENTATION TIME %.0f SECONDS" % (time.time() - start_time))
    
        
    #     for f in concurrent.futures.as_completed(results):
    #         infor_of_couples = f.result()[0]
    #         trans = f.result()[1]
    #         my_trans += list(trans)
    #         for info in infor_of_couples:
    #            my_dict[id] = info
    #            id += 1

    # # print("TOTAL IMPLEMENTATION TIME %.0f SECONDS" % (time.time() - start_time))
    # aggregate = AggregateDatabase(majorLeagueList)
    # aggregate.aggregateScoreCouple(my_dict)
    # print("***********************************************************************************************************************************************************************************")
    # print("TOTAL IMPLEMENTATION TIME %.0f SECONDS" % (time.time() - start_time))
    


