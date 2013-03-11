using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Management.Automation;
using System.Net;
using System.Text;
using System.Threading;
using NLog;

namespace Mirantis.Keero.WindowsAgent
{
	[DisplayName("Keero Agent")]
	sealed public class Program : WindowsService
	{
		private static readonly Logger Log = LogManager.GetCurrentClassLogger();
		private volatile bool stop;
		private Thread thread;
		private RabbitMqClient rabbitMqClient;
		private int delayFactor = 1;
		private string plansDir;

		static void Main(string[] args)
		{
			Start(new Program(), args);
		}

		protected override void OnStart(string[] args)
		{
			base.OnStart(args);

			Log.Info("Version 0.3");

			this.rabbitMqClient = new RabbitMqClient();

			var basePath = Path.GetDirectoryName(Process.GetCurrentProcess().MainModule.FileName);
			this.plansDir = Path.Combine(basePath, "plans");


			if (!Directory.Exists(plansDir))
			{
				Directory.CreateDirectory(plansDir);
			}

			this.thread = new Thread(Loop);
			this.thread.Start();
		}

		void Loop()
		{
			const string unknownName = "unknown";
			while (!stop)
			{
				try
				{
					foreach (var file in Directory.GetFiles(this.plansDir, "*.json.result")
						.Where(file => !File.Exists(Path.Combine(this.plansDir, Path.GetFileNameWithoutExtension(file)))))
					{
						var id = Path.GetFileNameWithoutExtension(Path.GetFileNameWithoutExtension(file)) ?? unknownName;
						if (id.Equals(unknownName, StringComparison.InvariantCultureIgnoreCase))
						{
							id = "";
						}

						var result = File.ReadAllText(file);
						Log.Info("Sending results for {0}", id ?? unknownName);
						rabbitMqClient.SendResult(new MqMessage { Body = result, Id =  id });
						File.Delete(file);
					}

					var path = Directory.EnumerateFiles(this.plansDir, "*.json").FirstOrDefault();
					if (path == null)
					{
						var message = rabbitMqClient.GetMessage();
						var id = message.Id;
						if(string.IsNullOrEmpty(id))
						{
							id = unknownName;
						}
						
						path = Path.Combine(this.plansDir, string.Format("{0}.json", id));
						File.WriteAllText(path, message.Body);
						Log.Info("Received new execution plan {0}", id);
						message.Ack();
					}
					else
					{
						var id = Path.GetFileNameWithoutExtension(path);
						Log.Info("Executing exising plan {0}", id);
					}
					var executor = new PlanExecutor(path);
					executor.Execute();
					File.Delete(path);
					delayFactor = 1;

					if (stop) break;
					if (executor.RebootNeeded)
					{
						Reboot();
					}
				}
				catch (Exception exception)
				{
					WaitOnException(exception);
				}
				
			}

		}

		private void Reboot()
		{
			Log.Info("Going for reboot!!");
			LogManager.Flush();
			/*try
			{
				System.Diagnostics.Process.Start("shutdown.exe", "-r -t 0");
			}
			catch (Exception ex)
			{
				Log.ErrorException("Cannot execute shutdown.exe", ex);
			}*/

		
			try
			{
				PowerShell.Create().AddCommand("Restart-Computer").AddParameter("Force").Invoke();
			}
			catch (Exception exception)
			{

				Log.FatalException("Reboot exception", exception);
			}
			finally
			{
				Log.Info("Waiting for reboot");
				for (var i = 0; i < 10 * 60 * 5 && !stop; i++)
				{
					Thread.Sleep(100);
				}
				Log.Info("Done waiting for reboot");
			}

		}

		private void WaitOnException(Exception exception)
		{
			if (stop) return;
			Log.WarnException("Exception in main loop", exception);
			var i = 0;
			while (!stop && i < 10 * (delayFactor * delayFactor))
			{
				Thread.Sleep(100);
				i++;
			}
			delayFactor = Math.Min(delayFactor + 1, 6);
		}

		protected override void OnStop()
		{
			stop = true;
			this.rabbitMqClient.Dispose();
			base.OnStop();
		}

	}
}
