# import pandas as pd
# import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import time
import torch
import csv
import multiprocessing as mp
#from pandarallel import pandarallel
from mysql.connector import MySQLConnection
import os
import pickle
import pandas as pd
import json




# define paths
root="/home/vnteam/Data/MatchData/"
orig_fn="bettrans20201129.csv"
result_fn="datastaging.csv"
mjl_fn="major_league.csv"
mlm_fn="match20201129.csv"
save_fn='cus_list.pkl'

# define batch_size
chunk_size=100000

# pandarallel.initialize(

if __name__ == "__main__":

    try:
        conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
        cursor = conn.cursor()
        cursor.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',['AssociationStats'])
        
        conn.commit()
        #results = [r.fetchall() for r in cursor.stored_results()]
        #results = cursor.fetchall()
        # for res in cursor.stored_results():
        #     result = res.fetchall()
        # print(result)
        #print(results)

        cursor.close()
        conn.close()

    except Exception as err:
        print(err)
