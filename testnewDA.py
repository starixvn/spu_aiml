import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from DataAccess02.Model.BaseDAModel import BaseDAModel
from DataAccess02.Model.BaseDA import BaseDA
from Configuration.Configuration import config

if __name__ == '__main__':
    aiml_spu = BaseDAModel(config.aimldb, config.aimlhost, config.aimlport, config.aimluser, config.aimlpwd)
    paraminput = ["1,6",None]
    result = BaseDA.execute(aiml_spu.call_sp("SPU_AIML_GetAssociationStatsStaging",paraminput))
    print(result)
    