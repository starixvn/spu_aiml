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
    












    
