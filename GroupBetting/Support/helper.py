import numpy as np
from numba import prange, njit, set_num_threads, jit
from numba.typed import List
import numba
from tqdm import tqdm

@njit(parallel=True)
def compute_pairwise_cus(X,time_threshold,n_jobs=4):
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
        for j in range(i+1, n):
            mat[i, j] = mat[j, i] = calculate_difference(X[i], X[j], time_threshold)

    np.fill_diagonal(mat, 0.0)   
    return mat

@njit
def calculate_difference(ls1, ls2, time_threshold):
    # drop trash
    ls1 = ls1[ls1 != -1]
    ls2 = ls2[ls2 != -1]
    
    '''reshape to [[transdate, custID],
                   [],
                   ...]
    '''
    ls1 = ls1.reshape(-1, 2)
    ls2 = ls2.reshape(-1, 2)
    
    STACK = np.vstack((ls1, ls2))
    SORT = STACK[STACK[:,0].argsort()]
    
    time_arr,cus_arr = SORT.T
    
    diff_cus = cus_arr[1:]-cus_arr[:-1]
    #zip_trans = np.column_stack((trans_arr[1:],trans_arr[:-1]))
    zip_time = np.column_stack((time_arr[1:],time_arr[:-1]))

    #eff_trans = zip_trans[(diff_cus != 0) & (diff_time < 20)].flatten().astype(np.int64)
    eff_zip_time = zip_time[diff_cus != 0]
    #fil_cus_tickets = diff_time[diff_cus != 0]
    #eff_diff_time = fil_cus_tickets[fil_cus_tickets < 20]
    diff_time=eff_zip_time[:,0]-eff_zip_time[:,1]
    eff_diff_time=diff_time[diff_time<=20]
    if len(eff_diff_time)==0:
        time_score = 0
    else:
        time_score = (time_threshold-np.mean(eff_diff_time)) / time_threshold

    #return (time_score, set(list(eff_trans)))
    return time_score
((32/(52*8))*(31/(52*8 - 1)))