namespace AIML_DataRepository.Controllers

{
    using System.Collections.Generic;
    using AIML_DataRepository.Model;
    using Microsoft.Extensions.Configuration;
    using Microsoft.AspNetCore.Mvc;
    using AIML_DataRepository.Services;

    [Route("api/GetDataProduction")]
    [ApiController]
    public class DataPRODController : ControllerBase
    {
        private readonly ITransactionServices _services;
        private readonly IConfiguration Configuration;

        public DataPRODController(
            ITransactionServices services,
            IConfiguration configuration
            )
        {
            Configuration = configuration;
            _services = services;
        }
        [HttpGet]
        [Route("GetTransactionData")]
        public ActionResult<List<Transaction>> GetDataTransaction()
        {
            var locationFile = Configuration["ServiceInformation:Path"];
            var fileName = Configuration["ServiceInformation:FileName"];
            var inventoryItems = _services.GetDataTransaction(locationFile, fileName);

            if (inventoryItems == null)
            {
                return NotFound();
            }
            return inventoryItems;
        }
    }
}