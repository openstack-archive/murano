using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Mirantis.Keero.WindowsAgent
{
	class MqMessage
	{
		private readonly Action ackFunc;

		public MqMessage(Action ackFunc)
		{
			this.ackFunc = ackFunc;
		}
		
		public MqMessage()
		{
		}

		public string Body { get; set; }
		public string Id { get; set; }

		public void Ack()
		{
			ackFunc();
		}
	}
}
