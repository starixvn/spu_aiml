import pandas as pd
import datetime
import os

from tqdm.std import tqdm
from Configuration.LocalConfiguration import LocalConfiguration
from Configuration.ProConfiguration import ProConfiguration
ENV='LOCAL'

if ENV=='LOCAL':

    config = LocalConfiguration()

else:
    config = ProConfiguration()
root_orig=config.GetPathCsvFile(config)
backup=config.GetBackUp(config)
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

def recursiveApp(list_file):
    # files = os.listdir(root_orig)

    data =  pd.concat([pd.read_csv(os.path.join(root_orig, list_file[idx]),
                                encoding='ISO-8859-1'
                                , skiprows=[1], skipfooter=1
                                ).assign(file_name=list_file[idx]) for idx in tqdm(range(len(list_file)),desc='Combining Files')],ignore_index=True)
    for file in list_file:
        os.rename(os.path.join(root_orig,file),os.path.join(backup,file))
    return data


def count_joining_combs(cus1, cus2,cusDict):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a, comb_b = set(cusDict[cus1]), set(cusDict[cus2])
    return len(comb_a.intersection(comb_b))