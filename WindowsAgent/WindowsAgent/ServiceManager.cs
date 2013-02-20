using System;
using System.Configuration.Install;
using System.Reflection;
using System.ServiceProcess;
using NLog;

namespace Mirantis.Keero.WindowsAgent
{
    public class ServiceManager
    {
        private readonly string serviceName;

        public ServiceManager(string serviceName)
        {
            this.serviceName = serviceName;
        }

        private static readonly Logger Log = LogManager.GetCurrentClassLogger();

        public bool Restart(string[] args, TimeSpan timeout)
        {
            var service = new ServiceController(serviceName);
            try
            {
                var millisec1 = TimeSpan.FromMilliseconds(Environment.TickCount);

                service.Stop();
                service.WaitForStatus(ServiceControllerStatus.Stopped, timeout);
                Log.Info("Service is stopped");

                // count the rest of the timeout
                var millisec2 = TimeSpan.FromMilliseconds(Environment.TickCount);
                timeout = timeout - (millisec2 - millisec1);

                service.Start(args);
                service.WaitForStatus(ServiceControllerStatus.Running, timeout);
                Log.Info("Service has started");
                return true;
            }
            catch (Exception ex)
            {
                Log.ErrorException("Cannot restart service " + serviceName, ex);
                return false;
            }
        }

        public bool Stop(TimeSpan timeout)
        {
            var service = new ServiceController(serviceName);
            try
            {
                service.Stop();
                service.WaitForStatus(ServiceControllerStatus.Stopped, timeout);
                return true;
            }
            catch (Exception ex)
            {
                Log.ErrorException("Cannot stop service " + serviceName, ex);
                return false;
            }
        }

        public bool Start(string[] args, TimeSpan timeout)
        {
            var service = new ServiceController(serviceName);
            try
            {
                service.Start(args);
                service.WaitForStatus(ServiceControllerStatus.Running, timeout);
                return true;
            }
            catch (Exception ex)
            {
                Log.ErrorException("Cannot start service " + serviceName, ex);
                return false;
            }
        }

        public bool Install()
        {
            try
            {
                ManagedInstallerClass.InstallHelper(
                    new string[] { Assembly.GetEntryAssembly().Location });
            }
            catch(Exception ex)
            {
                Log.ErrorException("Cannot install service " + serviceName, ex);
                return false;
            }
            return true;
        }

        public bool Uninstall()
        {
            try
            {
                ManagedInstallerClass.InstallHelper(
                    new string[] { "/u", Assembly.GetEntryAssembly().Location });
            }
            catch (Exception ex)
            {
                Log.ErrorException("Cannot uninstall service " + serviceName, ex);
                return false;
            }
            return true;
        }

    }
    
}
