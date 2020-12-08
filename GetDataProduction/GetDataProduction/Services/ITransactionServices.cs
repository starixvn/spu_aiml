using GetDataProduction.Model;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace GetDataProduction.Services
{
    public interface ITransactionServices
    {
        List<Transaction> GetDataTransaction();
    }
}
