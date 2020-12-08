using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using GetDataProduction.Model;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using GetDataProduction.Services;

namespace GetDataProduction.Controllers
{
    [Route("api/getdata")]
    [ApiController]
    public class DataPRODController : ControllerBase
    {
        private readonly ITransactionServices _services;

        public DataPRODController(ITransactionServices services)
        {
            _services = services;
        }
        [HttpPost]
        [Route("GetData2")]
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