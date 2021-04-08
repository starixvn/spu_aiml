namespace AIML_DataRepository.Services
{
    using AIML_DataRepository.Model;
    using System.Collections.Generic;
    public interface ITransactionServices
    {
        List<Transaction> GetDataTransaction(string locationFile, string fileName);
    }
}
