using CsvHelper.Configuration;
using GetDataProduction.Model;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace GetDataProduction.Mappers
{
    public sealed class TransactionMap: ClassMap<Transaction>
    {
        public TransactionMap()
        {
            //Map(x => x.transid).Name("transid");

            //Map(x => x.custid).Name("custid");

            //Map(x => x.matchid).Name("matchid");

            //Map(x => x.username2).Name("username2");

            //Map(x => x.transdate).Name("transdate");

            //Map(x => x.winlostdate).Name("winlostdate");

            //Map(x => x.oddsspread).Name("oddsspread");

            //Map(x => x.odds).Name("odds");

            //Map(x => x.hdp1).Name("hdp1");

            //Map(x => x.hdp2).Name("hdp2");

            //Map(x => x.stake).Name("stake");

            //Map(x => x.status).Name("status");

            //Map(x => x.statusid).Name("statusid");

            //Map(x => x.winlost).Name("winlost");

            //Map(x => x.actualstake).Name("actualstake");

            //Map(x => x.actualrate).Name("actualrate");

            //Map(x => x.livehomescore).Name("livehomescore");

            //Map(x => x.liveawayscore).Name("liveawayscore");

            //Map(x => x.liveindicator).Name("liveindicator");

            //Map(x => x.bettype).Name("bettype");

            //Map(x => x.betteam).Name("betteam");

            //Map(x => x.betfrom).Name("betfrom");

            //Map(x => x.arecommend).Name("arecommend");

            //Map(x => x.mrecommend).Name("mrecommend");

            //Map(x => x.srecommend).Name("srecommend");

            //Map(x => x.currency).Name("currency");

            //Map(x => x.ip).Name("ip");

            //Map(x => x.balance).Name("balance");

            // test data
            Map(x => x.Name).Name("Name");

            Map(x => x.Mobile).Name("Mobile");

            Map(x => x.Body).Name("Body");
        }
    }
}
