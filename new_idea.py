# import libraries
import pandas as pd
import numpy as np
from sklearn.metrics import pairwise_distances
import multiprocessing as mp
# from tqdm.notebook import tqdm
from tqdm import tqdm
import csv
import concurrent.futures as cf
import time
import datetime
import os
import json
import gc
import pickle
from GroupBetting.ProcessCusBased import ProcessCusBased
from Configuration.Configuration import Configuration
config = Configuration()
# algorithmScore = FeatureScore()
# aggregate = AggregateDatabase()

# get information all ticket of each match
# save_dir =config.GetSaveDirectoryModel(config)
path_csv = config.GetPathCsvFile(config)
filecsv_name = os.path.join(path_csv,config.GetNameFile(config))
name2 = os.path.join(path_csv,config.GetMajorLeagueName(config))
# log_name = config.GetLogName(config)
name1 = os.path.join(path_csv,config.GetMatchLeagueMapping(config))
output1a = config.GetTemp1A(config)
# output1b = config.GetTemp1B(config)
# output2 = config.GetTemp2(config)
# match_output = config.GetMatchOuput(config)
# score_output = config.GetScoreOuput(config)
# trans_output = config.GetTransOuput(config)
dict_name = config.GetDictName(config)


def processing(args):
    support = ProcessCusBased()
    k,ns=args[0],args[1]
    ls=ns.ls
    big_data=ns.big_data
    match_league_map=ns.match_league_map
    major=ns.major
# for k in tqdm(range(len(ls)-1),desc="PROCESSING..."):
#   if i % 1e9 == 0:
#     mod = i % 1e9
#     os.mkdir(os.path.join(root,save_folder,"folder %.0f" % (mod+1)))
    a=ls[0]
    info_a=big_data[a]

    comb_a=set(info_a.keys())
#   for j in tqdm(range(k+1,len(ls)),desc=f"LOOP {k+1} . . ."):
  # for b in ls:
    # i += 1
    b = ls[k]
    
    info_b=big_data[b]
    comb_b=set(info_b.keys())
    intersec = comb_a.intersection(comb_b)
    if len(intersec)>0:
        # i += 1
        bet_count=0
        mil,mal,my_dict={},{},{}
        d = {}
        # my_dict['C1']=str(a)
        # my_dict['C2']=str(b)
        for comb in intersec:
        
            (match,bettype)=comb
            arr = np.concatenate((info_a[comb],info_b[comb]),axis=0)
            bet_count += arr.shape[0]
            l=match_league_map[match]['leagueid']
            if l in major:
                if l in mal:
                    mal[l] += 1
                # mal[l] +=1 if l in mal else mal[l]=1
                else:
                    mal[l]=1
            else:
                if l in mil:
                    mil[l] += 1
                # mil[l] +=1 if l in mil else mil[l]=1
                else:
                    mil[l]=1
    
            d[str(comb)]=arr[arr[:,2].argsort()]
        # i += 1
  # if i > 1e6  or k == len(ls)-2:
    ts_result = pd.Series(d).apply(support.compute_time_score)
    
    ts_arr=ts_result.apply(lambda z : z[0]).values
    
    my_dict['num_eff_comb']=len(ts_arr[ts_arr>0])

    my_dict['eff_trans']=ts_result.apply(lambda z : z[1]).to_dict()
    
    my_dict['num_joing_comb']=len(intersec)
    my_dict['comb_score']=len(ts_arr[ts_arr>0]) / len(ts_arr)
    # print(f"MIL {mil.values()}",f"MAL {mal.values()}")
    my_dict['league_score']=support.compute_league_score(list(mil.values()),list(mal.values()))
    
    # S['time_score']=S['time_score'].apply(lambda z: np.mean(np.array(z)[np.array(z) >0] if np.sum(z)>0 else 0))
    my_dict['time_score']= np.mean(ts_arr[ts_arr>0]) if len(ts_arr[ts_arr>0]) > 0 else 0
    my_dict['bet_count']=bet_count
    
    with open(os.path.join(output1a,f'{a}_{b}.json'), 'w') as g:
    # with open(os.path.join(root,save_folder,"folder %.0f" % (mod+1),f'{k}.pkl'), 'wb') as handle:  ,"folder %.0f" % (mod+1)
        json.dump(my_dict, g)

# break
    # del d,DF,S,my_dict
    del d,my_dict
    gc.collect()
      # i = 0
      # d = {}

if __name__ == "__main__":

    start_time = time.time()

    match_league_map = pd.read_csv(name1,error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
    MAJOR_LEAGUE = pd.read_csv(name2)
    major = MAJOR_LEAGUE.LeagueId.unique()
    # save_dict="dict_output"
    
    with open(os.path.join(path_csv,dict_name), 'rb') as f:
        big_data=pickle.load(f)
    print(f"NUM CUS {len(big_data)}")

    ls=list(big_data.keys())
# print(f"NUM CUS {len(ls)} | CUS 0 {ls[0]}")

    mgr = mp.Manager()
    ns = mgr.Namespace()
    ns.big_data=big_data
    ns.ls=ls
    ns.match_league_map=match_league_map
    ns.major=major

    pool = mp.Pool(processes=4)
    tasks=[(k,ns) for k in range(1,len(ls))]
    for _ in tqdm(pool.imap_unordered(processing, tasks), total=len(tasks)):
        pass
    

  
    print("***********************************************************************************************************************************************************************************")
    print("TOTAL IMPLEMENTATION TIME %.0f SECONDS" % (time.time() - start_time))


# mkdir output1 output2 score_output trans_output match_output
# rm -r output1 output2 score_output trans_output match_output