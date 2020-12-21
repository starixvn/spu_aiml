using CsvHelper;
using AIML_DataRepository.Mappers;
using AIML_DataRepository.Model;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace AIML_DataRepository.Services
{
    public class TransactionServices : ITransactionServices
    {
        public List<Transaction> ReadCSVFile()
        {
            string Error = string.Empty;
            try
            {
                string location = @"D:\Note\test2.csv";
                using (var reader = new StreamReader(location, Encoding.Default))
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

        public List<Transaction> GetDataTransaction()
        {
            //_inventoryItems.Add(model.Name, model);
            return ReadCSVFile();
            //return model;
        }
    }
}
