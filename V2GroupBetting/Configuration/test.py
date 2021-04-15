from mysql.connector import MySQLConnection

if __name__=='__main__':
   conn = MySQLConnection(user = 'darius.vn', password = '1qaz@Wsx3edc',
                           host = '10.18.200.72', port = 3306, database = 'SPU_AIML')
   cursor = conn.cursor()
   cursor.execute("SELECT @@session.transaction_isolation;")
   print(cursor.fetchall()[0])