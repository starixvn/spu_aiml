import os
import pickle
import sys
import re
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
sys.path.append("D:\\Project\\aiml_cleancode\\DataAccess\\Model\\SPU_AIML\\")
from DataAccess.Model.SPU_AIML.SPU_GetAssociationStatsStagingDAModel import SPU_GetAssociationStatsStagingDAModel
from Helper import Notifier
import numpy as np
import pandas as pd
import datetime
import subprocess
import logging
from Configuration.Configuration import config
from numba import prange, njit, set_num_threads


def notify_logging(mess, isInfo = False):
    if isInfo:
        logging.info(mess)
    else:
        logging.error(mess)
    Notifier.send_message(mess)
    

@njit(parallel=True)
def compute_pairwise_cus(X, time_threshold, n_jobs=4):
    set_num_threads(n_jobs)
    n = X.shape[0]
    mat = np.empty((n, n), np.float64)
    #     mat = np.repeat('', n*n).reshape(n, -1)
    #     mat = list(np.arange(n*n).reshape(n, -1))

    # if save_trans :
    # transids = [np.array([0]).astype(np.int64) for _ in range(int(n*(n+1)/2) - n)]
    # for i in prange(n-1):
    # for j in range(i+1, n):
    # mat[i, j], trans = mat[j, i], trans = calculate_difference(X[i], X[j])

    # pos = int(i*n+j - i*(i+1)/2 - (i+1))
    # transids[pos] = np.array(list(trans)).astype(np.int64)

    # np.fill_diagonal(mat, 0.0)
    # return mat, List(transids)

    for i in prange(n - 1):
        for j in range(i + 1, n):
            mat[i, j] = mat[j, i] = calculate_difference(X[i], X[j], time_threshold)

    np.fill_diagonal(mat, 0.0)
    return mat


@njit
def calculate_difference(ls1, ls2, time_threshold):
    # drop trash
    ls1 = ls1[ls1 != -1]
    ls2 = ls2[ls2 != -1]

    '''reshape to [[transdate, custID],
                   [],
                   ...]
    '''
    ls1 = ls1.reshape(-1, 2)
    ls2 = ls2.reshape(-1, 2)

    STACK = np.vstack((ls1, ls2))
    SORT = STACK[STACK[:, 0].argsort()]

    time_arr, cus_arr = SORT.T

    diff_cus = cus_arr[1:] - cus_arr[:-1]
    # zip_trans = np.column_stack((trans_arr[1:],trans_arr[:-1]))
    zip_time = np.column_stack((time_arr[1:], time_arr[:-1]))

    # eff_trans = zip_trans[(diff_cus != 0) & (diff_time < 20)].flatten().astype(np.int64)
    eff_zip_time = zip_time[diff_cus != 0]
    # fil_cus_tickets = diff_time[diff_cus != 0]
    # eff_diff_time = fil_cus_tickets[fil_cus_tickets < 20]
    diff_time = eff_zip_time[:, 0] - eff_zip_time[:, 1]
    eff_diff_time = diff_time[diff_time <= 20]
    if len(eff_diff_time) == 0:
        time_score = 0
    else:
        time_score = (time_threshold - np.mean(eff_diff_time)) / time_threshold

    # return (time_score, set(list(eff_trans)))
    return time_score

def str_to_class(classname):
    #return getattr(sys.modules[__name__], classname)
    return globals()[classname]

def notify_logging(mess, isInfo = False):
    if isInfo:
        logging.info(mess)
    else:
        logging.error(mess)
    #Notifier.send_message(mess)

def change_permission_file(list_file):
    list_file_denied = [f for f in list_file if (os.access(config.root_orig + f, os.R_OK) is False or os.access(config.root_orig + f, os.X_OK) is False)]
    if len(list_file_denied) > 0:
        message_telegram = f"{config.ENV} | Processing change permission file : {len(list_file_denied)}"
        notify_logging(message_telegram)
        for i in list_file_denied:
            subprocess.Popen(f"echo 'Welcome1' | sudo -S  chmod 755 {config.root_orig + i}", stdout=subprocess.PIPE, shell=True)
def distance_time(transdate1, transdate2):
    """
    >>> Input  : transdate 1 : datetime.datetime(2020,9,26,7,28,1)

                 transdate 2 : datetime.datetime(2020,9,26,7,31,1)

    >>> Output : 180 seconds
    """

    return (datetime.datetime(*transdate2)-datetime.datetime(*transdate1)).total_seconds()

def separate(transdate):
    """
    >>> Input  :    '2020-09-26 7:31:01.872'

    >>> Output :    (2020,9,26,7,31,1)
    """
    date, hms = transdate.split(' ')[0].split(
        '-'), transdate.split(' ')[1].split('.')[0].split(':')
    year, month, day = int(date[0]), int(date[1]), int(date[2])
    hour, min, sec = int(hms[0]), int(hms[1]), int(hms[2])
    return (year, month, day, hour, min, sec)


def time_distance(transdate1, transdate2):
    """
    >>> Input  : transdate_1 : datetime.datetime(2020,9,26,7,28,1)

                 transdate_2 : datetime.datetime(2020,9,26,7,31,1)

    >>> Output : 180 seconds
    """

    return (datetime.datetime(*transdate2)-datetime.datetime(*transdate1)).total_seconds()


def count_joining_combs_by_file_cus_dict(cus1,cus2,batch_cus_dict):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a, comb_b = set(batch_cus_dict[cus1]), set(batch_cus_dict[cus2])
    return len(comb_a.intersection(comb_b))


def count_joining_combs_by_daily_cus_dict(cus1,cus2,daily_cus_dict):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a, comb_b = set(daily_cus_dict[cus1]), set(daily_cus_dict[cus2])
    return len(comb_a.intersection(comb_b))


def transform_to_list(df):
    keys, values1, values2 = df.sort_values('sample_id').values.T
    ukeys, index = np.unique(keys, True)
    arrays = np.split(values1, index[1:])
    arrays2 = np.split(values2, index[1:])
    df2 = pd.DataFrame({'sample_id': ukeys, 'ML': [list(
        a) for a in arrays], 'BL': [list(b) for b in arrays2]})
    return df2

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

    return 1 - sum(map(lambda x: (x/sum_match)**2, lista))


def total_leaguescore(x, y):
    if y == 1:
        return (x + 5/2) * (2/7)
    elif x == 1:
        return (y + 3/2) * (2/5)
    elif y != 1 and x != 1:
        minor_score = (x + 5/2) * (2/7)
        major_score = (y + 3/2) * (2/5)
        return (3 * (minor_score + 1) + (major_score + 2)) * (1/9)

def load_a_file(location,file_name):
    with open(os.path.join(location, file_name), 'rb') as f:
        my_file = pickle.load(f)
    return my_file

def save_a_file(location,file_name,object):
    with open(os.path.join(location, file_name), 'wb') as f:
        pickle.dump(object,f)
        
def move_files(from_location,to_location,list_files):
    for file in list_files:
        os.rename(os.path.join(from_location,file),os.path.join(to_location,file))
        
        
def filter_files_by_type(list_files,str_type):
    str_type = ".csv"
    pattern = str_type + "$"
    results = [i for i in list_files if re.findall(pattern,i)]
    return results

def filter_files_by_day(list_files):
    myStrCheck = list_files[0].rsplit("_",4)
    pattern = "^" + myStrCheck[0]
    results = [i for i in list_files if re.findall(pattern,i)]
    return results









    
