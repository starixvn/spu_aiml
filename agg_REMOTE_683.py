# import pandas as pd
# import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import time
import matplotlib.pyplot as plt
import csv
import multiprocessing as mp
# from pandarallel import pandarallel
from mysql.connector import MySQLConnection
import os
import pickle
import pandas as pd
import json




if __name__ == "__main__":

  aimluser='long.vn'
  aimlpwd='Welcome1'
  aimlhost='10.18.200.70'
  aimlport='3307'
  aimldb='SPU_AIML'

  date_insert='2021-01-29'
  # define paths
  conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
  cur = conn.cursor()
  # update table SystemParameter
  cur.callproc('SPU_AIML.SPU_AIML_UpdateScanStatus',[date_insert, None])
  conn.commit()

  cur.close()
  conn.close()
  print('Update Scan Status successfully !')
  # df = pd.read_csv(path,encoding='ISO-8859-1')
                                
                              