using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;

namespace GetDataProduction.Controllers
{
    [Produces("application/json")]
    [Route("api/DataPROD")]
    public class DataPRODController : Controller
    {
        private readonly string AppName = new ConfigurationBuilder().AddJsonFile("appsettings.json").Build().GetSection("AppSettings")['APP_Name'];
        private int _currentId;
        private readonly string _folderName = ConfigurationManager.AppSettings["FileSystemFolder"];
        private readonly string _basePath = HttpContext.Current.Server.MapPath(@"~\" + ConfigurationManager.AppSettings["FileSystemFolder"]);
    }
}