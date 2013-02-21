using System;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Reflection;
using System.ServiceProcess;
using NLog;

namespace Mirantis.Keero.WindowsAgent
{
    public abstract class WindowsService : ServiceBase
    {
        private static readonly Logger Log = LogManager.GetCurrentClassLogger();
        public bool RunningAsService { get; private set; }

	    protected static void Start(WindowsService service, string[] arguments)
        {
            Directory.SetCurrentDirectory(Path.GetDirectoryName(Assembly.GetEntryAssembly().Location));

			if (arguments.Contains("/install", StringComparer.OrdinalIgnoreCase))
            {
                new ServiceManager(service.ServiceName).Install();
            }
			else if (arguments.Contains("/uninstall", StringComparer.OrdinalIgnoreCase))
			{
                new ServiceManager(service.ServiceName).Uninstall();
            }
			else if (arguments.Contains("/start", StringComparer.OrdinalIgnoreCase))
			{
                new ServiceManager(service.ServiceName).Start(Environment.GetCommandLineArgs(), TimeSpan.FromMinutes(1));
            }
			else if (arguments.Contains("/stop", StringComparer.OrdinalIgnoreCase))
			{
                new ServiceManager(service.ServiceName).Stop(TimeSpan.FromMinutes(1));
            }
			else if (arguments.Contains("/restart", StringComparer.OrdinalIgnoreCase))
			{
                new ServiceManager(service.ServiceName).Restart(Environment.GetCommandLineArgs(), TimeSpan.FromMinutes(1));
            }
			else if (!arguments.Contains("/console", StringComparer.OrdinalIgnoreCase))
			{
				service.RunningAsService = true;
				Run(service);
			}
			else
			{
				try
				{
					service.RunningAsService = false;
					Console.Title = service.ServiceName;
					service.OnStart(Environment.GetCommandLineArgs());
					service.WaitForExitSignal();
				}
				finally
				{
					service.OnStop();
					service.Dispose();
				}
			}
        }
        
        protected WindowsService()
        {
            var displayNameAttribute =
                this.GetType().GetCustomAttributes(typeof (DisplayNameAttribute), false).Cast<DisplayNameAttribute>().
                    FirstOrDefault();
            if(displayNameAttribute != null)
            {
                ServiceName = displayNameAttribute.DisplayName;
            }
        }


        protected virtual void WaitForExitSignal()
        {
            Console.WriteLine("Press ESC to exit");
            while (Console.ReadKey(true).Key != ConsoleKey.Escape)
            {
            }
        }

		protected override void OnStart(string[] args)
		{
			Log.Info("Service {0} started", ServiceName);

			base.OnStart(args);
		}

		protected override void OnStop()
		{
			Log.Info("Service {0} exited", ServiceName);
			base.OnStop();
		}
    }
}
