using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using AIML_DataRepository.Model;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using AIML_DataRepository.Services;

namespace AIML_DataRepository.Controllers
{
    [Route("api/GetDataProduction")]
    [ApiController]
    public class DataPRODController : ControllerBase
    {
        private readonly ITransactionServices _services;

        public DataPRODController(ITransactionServices services)
        {
            _services = services;
        }
        [HttpGet]
        [Route("GetTransactionData")]
        public ActionResult<List<Transaction>> GetDataTransaction()
        {
            var inventoryItems = _services.GetDataTransaction();

            if (inventoryItems == null)
            {
                return NotFound();
            }
            return inventoryItems;
        }
    }
}