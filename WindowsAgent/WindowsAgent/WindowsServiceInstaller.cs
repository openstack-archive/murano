using System.ComponentModel;
using System.Configuration.Install;
using System.Linq;
using System.Reflection;
using System.ServiceProcess;

namespace Mirantis.Keero.WindowsAgent
{
	[RunInstaller(true)]
	public class WindowsServiceInstaller : Installer
    {
		public WindowsServiceInstaller()
        {
            var processInstaller = new ServiceProcessInstaller { Account = ServiceAccount.LocalSystem };
            foreach (var type in Assembly.GetEntryAssembly().GetExportedTypes().Where(t => t.IsSubclassOf(typeof(ServiceBase))))
            {
                var nameAttribute = type.GetCustomAttributes(typeof (DisplayNameAttribute), false)
                    .Cast<DisplayNameAttribute>().FirstOrDefault();
                if(nameAttribute == null) continue;
                var serviceInstaller = new ServiceInstaller {
                    StartType = ServiceStartMode.Automatic,
                    ServiceName = nameAttribute.DisplayName,
                    DisplayName = nameAttribute.DisplayName
                };
                var descriptionAttribute = type.GetCustomAttributes(typeof(DescriptionAttribute), false)
                    .Cast<DescriptionAttribute>().FirstOrDefault();
                if(descriptionAttribute != null)
                {
                    serviceInstaller.Description = descriptionAttribute.Description;
                }

                Installers.Add(serviceInstaller);
            }

            Installers.Add(processInstaller);

        }
    }
}
