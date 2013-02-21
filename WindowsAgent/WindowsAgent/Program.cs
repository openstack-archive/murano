using System;
using System.ComponentModel;
using System.IO;
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

		static void Main(string[] args)
		{
			Start(new Program(), args);
		}

		protected override void OnStart(string[] args)
		{
			base.OnStart(args);
			this.rabbitMqClient = new RabbitMqClient();
			this.thread = new Thread(Loop);
			this.thread.Start();
		}

		void Loop()
		{
			const string filePath = "data.json";
			while (!stop)
			{
				try
				{
					if (!File.Exists(filePath))
					{
						var message = rabbitMqClient.GetMessage();
						File.WriteAllText(filePath, message.Body);
						message.Ack();
					}
					var result = new PlanExecutor(filePath).Execute();
					if(stop) break;
					rabbitMqClient.SendResult(result);
					File.Delete(filePath);
				}
				catch (Exception exception)
				{
					WaitOnException(exception);
				}
				
			}

		}

		private void WaitOnException(Exception exception)
		{
			if (stop) return;
			Log.WarnException("Exception in main loop", exception);
			var i = 0;
			while (!stop && i < 10)
			{
				Thread.Sleep(100);
				i++;
			}
		}

		protected override void OnStop()
		{
			stop = true;
			this.rabbitMqClient.Dispose();
			Console.WriteLine("Stop");
			base.OnStop();
		}

	}
}
