import requests
import os
import logging
from datetime import datetime
from Configuration.Configuration import Configuration
import warnings
warnings.filterwarnings("ignore")
config = Configuration()
# algorithmScore = FeatureScore()
# aggregate = AggregateDatabase()

# get information all ticket of each match
save_dir = config.GetSaveDirectoryModel(config)
path_csv = config.GetPathCsvFile(config)
filecsv_name = os.path.join(path_csv, config.GetNameFile(config))
name2 = os.path.join(path_csv, config.GetMajorLeagueName(config))
log_name = config.GetLogName(config)
name1 = os.path.join(path_csv, config.GetMatchLeagueMapping(config))
output1 = config.GetTemp1(config)
output2 = config.GetTemp2(config)
match_output = config.GetMatchOuput(config)
score_output = config.GetScoreOuput(config)
trans_output = config.GetTransOuput(config)
logging.basicConfig(filename=os.path.join(save_dir, log_name), level=logging.INFO)


if __name__ == "__main__":
    try:
        url = 'http://localhost:8082/api/GetDataProduction/GetTransactionData'
        data = requests.get(url)
        if data != []:
            print("Don't have data from PROD")
        else:
            print("Don't have data from PROD")
    except Exception as e:
        logging.info(datetime.now())
        logging.error('Error: ' + str(e))
        
    
        
        
    
        
        
        