from datetime import datetime
from mysql.connector import MySQLConnection
import json
from datetime import date

a = date.today()
#print(a.strftime("%x"))
print(a)

args = [{
        "Trans": 5551111,
        "C": 111,
        "M": 123456,
        "Usn2": "toanprovip",
        "TD": "2002-05-06",
        "WLD": "2002-05-06",
        "OS": 1.5,
        "Hdp1": 1,
        "Hdp2": 0,
        "Stake": 4000,
        "S": "win",
        "SID": 12543,
        "WL": 12.2,
        "AS": 11,
        "AR": 88,
        "LHS": 1,
        "LAS": 0,
        "LI": 0,
        "BT": 1,
        "BC": "abv",
        "BF": "device",
        "RA": 896,
        "RM": 854,
        "RS": 555,
        "Cur": 25,
        "IP": "khongbiet",
        "Balance": '5555555555'
    },
    {
        "Trans": 99991111,
        "C": 211,
        "M": 223456,
        "Usn2": "toaaanprovip",
        "TD": "2002-05-06",
        "WLD": "2002-05-06",
        "OS": 2.5,
        "Hdp1": 2,
        "Hdp2": 0,
        "Stake": 6000,
        "S": "win",
        "SID": 212543,
        "WL": 22.2,
        "AS": 21,
        "AR": 38,
        "LHS": 1,
        "LAS": 0,
        "LI": 0,
        "BT": 1,
        "BC": "home",
        "BF": "device22",
        "RA": 296,
        "RM": 254,
        "RS": 255,
        "Cur": 85,
        "IP": "khongbiet",
        "Balance": 225.355
    }]

jsonstr = json.dumps(args)
print(type(jsonstr))
print(type(args))


# try:
#     conn = MySQLConnection(user = 'darius.vn', password = '1qaz@Wsx3edc', host = '10.18.200.70', port = '33507', database = 'SPU_AIML')
    
#     if conn.is_connected():
#         cursor = conn.cursor()
#         cursor.callproc('SPU_AIML_InsertSuspiciousTickets',[jsonstr,None])
#         conn.commit()
#         conn.close()
#         cursor.close()
        

# except Exception as err:
#     print(err)
# finally:
#     print(conn.is_connected())

# cnx = MySQLConnection(user = 'darius.vn', password = '1qaz@Wsx3edc', host = '10.18.200.70', port = '3307', database = 'SPU_AIML')
# if cnx.is_connected():
#     print(cnx.is_connected())
# else:
#     print(cnx.is_connected())

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
    tesy = sum(map(lambda x:(x/sum_match)**2,lista))

    return 1 - sum(map(lambda x:(x/sum_match)**2,lista))

print(gini_score([]))

