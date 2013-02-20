using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Mirantis.Keero.WindowsAgent
{
	class ExecutionPlan
	{
		public class Command
		{
			public string Name { get; set; } 
			public Dictionary<string, object> Arguments { get; set; }
		}

		public string[] Scripts { get; set; }
		public LinkedList<Command> Commands { get; set; }
	}
}
