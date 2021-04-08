namespace AIML_DataRepository.Services
{
    using CsvHelper;
    using AIML_DataRepository.Mappers;
    using AIML_DataRepository.Model;
    using System;
    using System.Collections.Generic;
    using System.IO;
    using System.Linq;
    using System.Text;
    public class TransactionServices : ITransactionServices
    {
        public List<Transaction> ReadCSVFile(string locationFile, string fileName)
        {
            string Error = string.Empty;
            try
            {
                string path = locationFile + fileName;
                using (var reader = new StreamReader(path, Encoding.Default))
                using (var csv = new CsvReader(reader, System.Globalization.CultureInfo.CurrentCulture))
                {
                    csv.Configuration.RegisterClassMap<TransactionMap>();
                    var records = csv.GetRecords<Transaction>().ToList();
                    return records;
                }
            }
            catch (Exception e)
            {
                //Error = e.Message;
                //return Error;
                throw new Exception(e.Message);

            }
        }

        public List<Transaction> GetDataTransaction(string locationFile, string fileName)
        {
            //_inventoryItems.Add(model.Name, model);
            return ReadCSVFile(locationFile,fileName);
            //return model;
        }
    }
}
