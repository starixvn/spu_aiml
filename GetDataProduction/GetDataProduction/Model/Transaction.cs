using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace GetDataProduction.Model
{
    public class Transaction
    {
        public int transid { get; set; }
        public string custid { get; set; }
        public string matchid { get; set; }
        public int username2 { get; set; }
        public string transdate { get; set; }
        public string winlostdate { get; set; }
        public int oddsspread { get; set; }
        public string odds { get; set; }
        public string hdp1 { get; set; }
        public int hdp2 { get; set; }
        public string stake { get; set; }
        public string status { get; set; }
        public int statusid { get; set; }
        public string winlost { get; set; }
        public string actualstake { get; set; }
        public int actualrate { get; set; }
        public string livehomescore { get; set; }
        public string liveawayscore { get; set; }
        public int liveindicator { get; set; }
        public string bettype { get; set; }
        public string betteam { get; set; }
        public int betfrom { get; set; }
        public string arecommend { get; set; }
        public string mrecommend { get; set; }
        public int srecommend { get; set; }
        public string currency { get; set; }
        public string ip { get; set; }
        public string balance { get; set; }

    }
}
