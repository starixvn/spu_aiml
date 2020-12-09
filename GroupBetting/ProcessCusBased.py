import numpy as np

class ProcessCusBased():
    def __init__(self):
        pass

    def find_intersection(self,set_a,set_b):
        """
        >>> Input  : set of matches / leagues / sports of customer A,
                    set of matches / leagues / sports of customer B
                        
        >>> Output : set of intersection
        """
        return set_a.intersection(set_b)

    def compute_time_score(self,trans_arr,time_arr,cus_arr):
        """
        >>> Input  :    array of transactions ID,
                        array of time points,
                        array of customers

        >>> Output :    time_score : a real number in range [0,1],
                        effective transactions ID : a set
        """ 
        
        diff_time = time_arr[1:]-time_arr[:-1]
        diff_cus = cus_arr[1:]-cus_arr[:-1]
        zip_trans = np.column_stack((trans_arr[1:],trans_arr[:-1]))
        
        eff_trans = zip_trans[(diff_cus != 0) & (diff_time <= 20)]
        fil_cus_tickets = diff_time[diff_cus != 0]
        fil_time_tickets = fil_cus_tickets[fil_cus_tickets <= 20]
        if len(fil_time_tickets)==0:
            time_score = 0
        else:
            time_score = (20-np.mean(fil_time_tickets)) / 20

        eff_trans = set(eff_trans.flatten())
        if len(eff_trans) == 0:
            eff_trans = ''
        
        return time_score,eff_trans