using AIML_DataRepository.Model;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace AIML_DataRepository.Services
{
    public interface ITransactionServices
    {
        List<Transaction> GetDataTransaction();
    }
}
