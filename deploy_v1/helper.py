import numpy as np
from numba import prange, njit, set_num_threads, jit
from numba.typed import List
import numba
from tqdm import tqdm
#count=0
@njit(parallel=True)
def compute_pairwise_cus(X,n_jobs=6):
    set_num_threads(n_jobs)
    n = X.shape[0]
    mat = np.empty((n, n), np.float64)
#     mat = np.repeat('', n*n).reshape(n, -1)
#     mat = list(np.arange(n*n).reshape(n, -1))

    #if save_trans :
        #transids = [np.array([0]).astype(np.int64) for _ in range(int(n*(n+1)/2) - n)]
        #for i in prange(n-1):
            #for j in range(i+1, n):
                #mat[i, j], trans = mat[j, i], trans = calculate_difference(X[i], X[j])

                #pos = int(i*n+j - i*(i+1)/2 - (i+1))
                #transids[pos] = np.array(list(trans)).astype(np.int64)

        #np.fill_diagonal(mat, 0.0)   
        #return mat, List(transids)
    
    for i in prange(n-1):
    #for i in tqdm(range(n-1),desc="PROCESSING..."):
        for j in range(i+1, n):
            mat[i, j] = mat[j, i] = calculate_difference(X[i], X[j])
        #count += 1
        #if i % 1000 == 0 :
        #print("Num Loops have been taken : ",i)
            

    np.fill_diagonal(mat, 0.0)   
    return mat

@njit
def calculate_difference(ls1, ls2):
    # drop trash
    ls1 = ls1[ls1 != -1]
    ls2 = ls2[ls2 != -1]
    
    '''reshape to [[transdate, custID],
                   [],
                   ...]
    '''
    ls1 = ls1.reshape(-1, 2)
    ls2 = ls2.reshape(-1, 2)
    
    DISTANCE_TIME_DISTRIBUTION = np.vstack((ls1, ls2))
    MY_LYST = DISTANCE_TIME_DISTRIBUTION[DISTANCE_TIME_DISTRIBUTION[:,0].argsort()]
    
#     sum_of_average_diff, transid_set, time_score = [], set(), 0
    
    #trans_arr,time_arr,cus_arr = MY_LYST.T
    
    time_arr,cus_arr = MY_LYST.T
    
    #diff_time = time_arr[1:]-time_arr[:-1]
    diff_cus = cus_arr[1:]-cus_arr[:-1]
    #zip_trans = np.column_stack((trans_arr[1:],trans_arr[:-1]))
    zip_time = np.column_stack((time_arr[1:],time_arr[:-1]))

# 
    #eff_trans = zip_trans[(diff_cus != 0) & (diff_time < 20)].flatten().astype(np.int64)
    eff_zip_time = zip_time[diff_cus != 0]
# #     eff_trans = [np.str(i) for i in eff_trans]
    #fil_cus_tickets = diff_time[diff_cus != 0]
    #fil_time_tickets = fil_cus_tickets[fil_cus_tickets < 20]
    diff_time=eff_zip_time[:,0]-eff_zip_time[:,1]
    eff_diff_time=diff_time[diff_time<=20]
    if len(eff_diff_time)==0:
        time_score = 0
    else:
        time_score = (20-np.mean(eff_diff_time)) / 20
#     time_score = numba.int64(time_score*100)  
#     transids.append(','.join(list(int(eff_trans).flatten().astype(str))))
#     return np.str(time_score)+'//'+ ','.join(list(eff_trans))
    #return (time_score, set(list(eff_trans)))
    return time_score