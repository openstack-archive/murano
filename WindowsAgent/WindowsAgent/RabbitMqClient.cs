using System;
using System.Collections.Generic;
using System.Configuration;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using NLog;
using RabbitMQ.Client;

namespace Mirantis.Keero.WindowsAgent
{
	class RabbitMqClient : IDisposable
	{
		private static readonly Logger Log = LogManager.GetCurrentClassLogger();
		private static readonly ConnectionFactory connectionFactory;
		private IConnection currentConnecton;

		static RabbitMqClient()
		{
			connectionFactory = new ConnectionFactory {
                HostName = ConfigurationManager.AppSettings["rabbitmq.host"] ?? "localhost",
                UserName = ConfigurationManager.AppSettings["rabbitmq.user"] ?? "guest",
                Password = ConfigurationManager.AppSettings["rabbitmq.password"] ??"guest",
                Protocol = Protocols.FromEnvironment(),
                VirtualHost = ConfigurationManager.AppSettings["rabbitmq.vhost"] ?? "/",
                RequestedHeartbeat = 10
            };
		}
		
		public RabbitMqClient()
		{
			
		}

		public MqMessage GetMessage()
		{
			var queueName = ConfigurationManager.AppSettings["rabbitmq.inputQueue"] ?? Dns.GetHostName().ToLower();
			try
			{
				IConnection connection = null;
				lock (this)
				{
					connection = this.currentConnecton = this.currentConnecton ?? connectionFactory.CreateConnection();
				}
				var session = connection.CreateModel();
				session.BasicQos(0, 1, false);
				//session.QueueDeclare(queueName, true, false, false, null);
				var consumer = new QueueingBasicConsumer(session);
				var consumeTag = session.BasicConsume(queueName, false, consumer);
				var e = (RabbitMQ.Client.Events.BasicDeliverEventArgs) consumer.Queue.Dequeue();
				Action ackFunc = delegate {
					session.BasicAck(e.DeliveryTag, false);
					session.BasicCancel(consumeTag);
					session.Close();
				};

				return new MqMessage(ackFunc) {
					Body = Encoding.UTF8.GetString(e.Body),
					Id = e.BasicProperties.MessageId
				};
			}
			catch (Exception exception)
			{

				Dispose();
				throw;
			}
		}

		public void SendResult(MqMessage message)
		{
			var exchangeName = ConfigurationManager.AppSettings["rabbitmq.resultExchange"] ?? "";
			var resultRoutingKey = ConfigurationManager.AppSettings["rabbitmq.resultRoutingKey"] ?? "-execution-results";
			bool durable = bool.Parse(ConfigurationManager.AppSettings["rabbitmq.durableMessages"] ?? "true");

			try
			{
				IConnection connection = null;
				lock (this)
				{
					connection = this.currentConnecton = this.currentConnecton ?? connectionFactory.CreateConnection();
				}
				var session = connection.CreateModel();
				/*if (!string.IsNullOrEmpty(resultQueue))
				{
					//session.QueueDeclare(resultQueue, true, false, false, null);
					if (!string.IsNullOrEmpty(exchangeName))
					{
						session.ExchangeBind(exchangeName, resultQueue, resultQueue);
					}
				}*/
				var basicProperties = session.CreateBasicProperties();
				basicProperties.SetPersistent(durable);
				basicProperties.MessageId = message.Id;
				basicProperties.ContentType = "application/json";
				session.BasicPublish(exchangeName, resultRoutingKey, basicProperties, Encoding.UTF8.GetBytes(message.Body));
				session.Close();
			}
			catch (Exception)
			{
				Dispose();
				throw;
			}
		}

		public void Dispose()
		{
			lock (this)
			{
				try
				{
					if (this.currentConnecton != null)
					{
						this.currentConnecton.Close();
					}
				}
				catch
				{
				}
				finally
				{
					this.currentConnecton = null;
				}
			}
		}
	}
}
