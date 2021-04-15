import pandas as pd
import numpy as np
# import multiprocessing as mp
# # import os
# # import pickle
# import multiprocessing as mp
# def sum_of_square(x):
#     count+=1
#     print('x^2 = ',x**2)
if __name__ == "__main__":
    # root="C:/Users/diego.nguyen/Downloads/DataVer04"
    # root="C:/Users/diego.nguyen/Downloads/DataVer02/New folder"
    # for fn in os.listdir(root):
    #     data=pd.read_csv( os.path.join(root,fn)
    #                     ,encoding='ISO-8859-1'
    #                     ,skiprows=[1]
    #                     ,skipfooter=1
    #                 )
    #     DATE = data[(data.bettype.isin([1, 3, 7, 8]))
    #                         & (data.liveindicator)]
    #     df=DATE.groupby(['matchid','bettype'])['custid'].nunique()
        # num_cus=DATE.custid.nunique()
        # print(f'File {fn} | Num cus {num_cus}','\n')
        # print(f'df | {fn}',df,sep='\n')
    # root="D:/Project/Formula_BET/SaveData"
    # cus_dict_fn="daily_cus_dict.pkl"
    # with open(os.path.join(root, cus_dict_fn), 'rb') as g:
    #     daily_cus_dict = pickle.load(g)
    # custid=12254460
    # if custid in daily_cus_dict:
    #     print(f'YES and here its combs {daily_cus_dict[custid]}')
    # else:
    #     print('No It is not')
    # count = 1
    # pool = mp.Pool(2)
    # ls = list(range(10))
    # pool.map(sum_of_square,ls)
    # vector1D = np.array([2,4,6])
    # matrix = np.array([[0],[1],[2]])
    # print('vector1D\n',vector1D)
    # print('matrix\n',matrix)
    # print('Adding 1Dvector and 2Dmatrix\n',vector1D+matrix)
    # print('My name is \"Diego\"')
    ls = list(range(10))
    np.random.shuffle(ls)
    print('ls\n',ls)
    