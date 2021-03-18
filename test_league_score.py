def compute_league_score(list_minor = None, list_major = None):
    """"
    >>> Input  :    list_minor, list of number of match in minor league
                    list_major, list of number of match in major league

    >>> Output :    league_score
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
  

if __name__ == "__main__":

#   list_major=[1,1,2]
  list_major=[1,1]
  # list_minor=[4,2,1,2,1,2,1,1,1,1,1,1,1,1,1,1,1,1,1]
  list_minor=[]
#   list_minor=[1,2,2,2,1,1,1,1,2,1,3,1,1]
  ls=compute_league_score(list_minor=list_minor,list_major=list_major)
  print('League Score %.3f' % (ls))