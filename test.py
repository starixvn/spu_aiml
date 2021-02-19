from numpy.core.fromnumeric import size
import pandas as pd
import os
import pickle
import numpy as np
import multiprocessing as mp
import time
from icecream import ic
import argparse
from mysql.connector import MySQLConnection
import json
root = "D:/Project/Formula_Bet/MatchData"
fn = "bettrans20201129.csv"
save_folder="D:/Project/Formula_Bet/SaveData"
save_fn='cus_list.pkl'

# ls=[(1,2,3),(4,5,6),(7,8,9)]

# print(f"DF {pd.DataFrame(ls,columns=['x','y','z'])}")

# df=pd.read_csv(os.path.join(root,fn),encoding='ISO-8859-1')
# print(f"df {df.head()}")
# DATE = df[(df.bettype.isin([1,3,7,8]))&(df.liveindicator)]
# CUST_LIST=DATE.custid.unique()
# print(f"LEN CUST LIST {len(CUST_LIST)}")
# with open(os.path.join(save_folder,save_fn),'wb') as f:
#     pickle.dump(CUST_LIST,f)
# live=df[df.liveindicator==1]
# print(f"BETTYPE UNIQUE {df.bettype.unique()}")
# read customer list
# with open(os.path.join(save_folder,save_fn),'rb') as f:
#     CUST_LIST=pickle.load(f)

# build batches
# CUST_LIST=np.sort(CUST_LIST)
# BATCHES=[CUST_LIST[x:x+10] for x in range(0, len(CUST_LIST), 10)]
# print(f"BATCH 1st {BATCHES[0]}")
# print(f"MAX {np.max(BATCHES[0])}")
# print(f"MIN {np.min(BATCHES[0])}")

# def factorial(n):
#     '''returns n!'''
#     return 1 if n < 2 else n * factorial(n-1)

# def tag(name, *content, cls=None, **attrs):
#     """Generate one or more HTML tags"""
#     if cls is not None:
#         attrs['class'] = cls
#     if attrs:
#         attr_str = ''.join(' %s="%s"' % (attr, value) for attr, value in sorted(attrs.items()))
#     else:
#         attr_str = ''
#     if content:
#         return '\n'.join('<%s%s>%s</%s>' % (name, attr_str, c, name) for c in content)
#     else:
#         return '<%s%s />' % (name, attr_str)

# def get_chunk(batch_size : int):
#     batch_count = 0
#     chunk = []
#     for ii in range(7):
#         chunk.append(ii)
#         batch_count += 1
#         if len(chunk) % batch_size == 0:
#             print(f'batch_count {batch_count}')
#             yield chunk
#             # chunk = []
#     if chunk:
#         print('There exists abnormal chunk')
#         yield chunk
#     else:
#         print('All chunks have the same length')

# def main(x):
#     print(f'Chunk {x}')

def foo(i):
    return i+333

def fibonaci(n):
    return fibonaci(n-1)+fibonaci(n-2) if n > 2 else 1

class Kclass():
    attr='yep'


if __name__ == "__main__":
    # print(tag('p', 'hello', id=33))
    # print(tag('p', 'hello', 'world', cls='sidebar'))
    # print(tag(content='testing', name="img"))
    # my_tag = {'name': 'img', 'title': 'Sunset Boulevard','src': 'sunset.jpg', 'cls': 'framed'}
    # print(tag(**my_tag))
    # start = time.time()
    # chunk_ls = get_chunk(5)
    # pool=mp.Pool(2)
    # pool.map(main,chunk_ls)
    # print('Implementation time %.0f seconds' % (time.time()-start))
    # print(f'num batch {int(np.ceil(5/2))}')
    # ic(foo(123))
    # ic(d['key'][1])
    # ic()
    # ic(Kclass.attr)
    # parser=argparse.ArgumentParser(description='Dinh Nguyen 94')
    # # parser.add_argument('--integer',type=int,default=0,help='sum : i+333')
    # parser.add_argument('--integer',type=int,help='find ith element of fibonaci')
    # args=parser.parse_args()
    # # ic(foo(args.integer))
    # print(f'{args.integer}th element of Fibonaci : {fibonaci(args.integer)}')
    # ls = [{"C1":1,"C2":1111},{"C1":1,"C2":2222},{"C1":2,"C2":3333},{"C1":2,"C2":4444},{"C1":3,"C2":5555}]
    fulldatabyAI_dba = '[{"C1":13123123,"C2":13123111}]'
    # fulldatabyAI_dba = json.dumps(ls)
    print(f'fulldatabyAI_dba {fulldatabyAI_dba}')
    print(f'type fulldatabyAI_dba {type(fulldatabyAI_dba)}')
    date_insert = '2021-01-31'
    conn = MySQLConnection(user = 'diego.vn', password = 'specialone1994', host = '10.18.200.70', port = '3307', database = 'SPU_AIML')
    cur = conn.cursor()
    cur.callproc('SPU_AIML_InsertAssociationByAI',[fulldatabyAI_dba,date_insert,None])
    conn.commit()

    print('Insert AssociationByAI Successfully !')
    
    cur.close()
    conn.close()