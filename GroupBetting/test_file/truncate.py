from mysql.connector import MySQLConnection
import argparse

if __name__ == "__main__":

  parser=argparse.ArgumentParser(description='Created by diego.nguyen@nexcel | Truncate Table')
  
  parser.add_argument('--name',type=str,help='name of table . It could be one of among [AssociationStats,AssociationStats_V2,...,AssociationStatsStaging,AssociationSuspiciousInfo,...]')
  
  args=parser.parse_args()

  try:
    conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
    cursor = conn.cursor()
    cursor.callproc('SPU_AIML_DBA_Truncate_Table',[args.name])
    conn.commit()
    cursor.close()
    conn.close()
  except Exception as err:
    print(err)