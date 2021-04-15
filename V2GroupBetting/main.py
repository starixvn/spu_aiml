import warnings
warnings.filterwarnings("ignore")
import time
from Configuration.SystemConfig import SystemConfig
from DataAccess import CommonDataAccess
from Utilities import remove_files,check_files
from GroupBettingManagement import GroupBettingManagement

ENV='LOCAL'

config = SystemConfig(ENV.capitalize()+"config.ini",ENV)

if __name__ == "__main__":

    CommonDataAccess.truncate_association_stats_staging(config)

    remove_files(config.root, config.cus_list_fn, config.cus_dict_fn)

    initial = []
    while True:
        time_phase0 = time.time()
        output = GroupBettingManagement.read_and_clean_data((initial, config))
        if output is None:
            continue
        data,initial,month,day,year = output
        batch_cus_dict, batch_cus_list, daily_cus_dict, daily_cus_list, date_insert = GroupBettingManagement.preprocess_data_and_prepare_necessary_files((
                                                                                        data, time_phase0, config))
        GroupBettingManagement.do_phase_1((batch_cus_dict, date_insert, config))
        output = check_files(config.root_orig, initial, day)
        while output is None:
            time.sleep(config.time_sleep)
            output = check_files(config.root_orig, initial, day)
        initial,time_constant = output
        if time_constant !=0 :
            date_insert = year+'-'+month+'-'+day
            the_first_is_the_last = False
            if len(initial)>2:
                GroupBettingManagement.do_phase_2((batch_cus_list, daily_cus_dict, date_insert, the_first_is_the_last, config))
            else:
                the_first_is_the_last = True
            GroupBettingManagement.finalize((daily_cus_list, date_insert, daily_cus_dict, the_first_is_the_last, config))
            CommonDataAccess.update_scan_status((date_insert, config))
        else:
            GroupBettingManagement.do_phase_2((batch_cus_list, daily_cus_dict,date_insert, the_first_is_the_last, config))
        time.sleep(config.time_sleep)