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

    def compute_time_score(self,triple):
        """
        >>> Input  :    array of transactions ID,
                        array of time points,
                        array of customers

        >>> Output :    time_score : a real number in range [0,1],
                        effective transactions ID : a set
        """ 
        cus_arr,trans_arr,time_arr = triple[:,0],triple[:,1],triple[:,2]
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
        
        return (time_score,','.join([str(x) for x in eff_trans]))
    
    def compute_league_score(self,list_minor=None,list_major=None):
        """"
        >>> Input  : list of minor leagues,list of major leagues

        >>> Output : league_score
        """
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

            return 1 - sum(map(lambda x:(x/sum_match)**2,lista))
        # list_minor=[league for league in leagues if league not in major]
        # list_major=[league for league in leagues if league in major]
        gini_minor = gini_score(list_minor)
        gini_major = gini_score(list_major)
        if len(list_minor) == 0:
            league_score = (gini_major + 3/2) * (2/5)
        elif len(list_major) == 0:
            league_score = (gini_minor + 5/2) * (2/7)
        else:
            minor_score = (gini_minor + 5/2) * (2/7)
            major_score = (gini_major + 3/2) * (2/5)
            league_score = (3 * (minor_score + 1) + (major_score + 2)) * (1/9)
        return league_score