import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from Helper import SendLogTelegram
import numpy as np
import pandas as pd
import datetime
import logging
def notify_logging(mess, isInfo = False):
    if isInfo:
        logging.info(mess)
    else:
        logging.error(mess)
    SendLogTelegram.send_message(mess)
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


def distance_time(transdate1, transdate2):
    """
    >>> Input  : transdate 1 : datetime.datetime(2020,9,26,7,28,1)

                 transdate 2 : datetime.datetime(2020,9,26,7,31,1)

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
    
