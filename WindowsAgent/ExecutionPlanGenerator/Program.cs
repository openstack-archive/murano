using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace ConsoleApplication1
{
	class Command
	{
		public string Name { get; set; }
		public Dictionary<string, object>  Arguments { get; set; }
	}
	class ExecutionPlan
	{
		public List<string> Scripts { get; set; }
		public List<Command> Commands { get; set; }
		public int RebootOnCompletion { get; set; }
	}


	class Program
	{
		static void Main(string[] args)
		{
			if (args.Length < 1 || args.Length > 2)
			{
				Console.WriteLine("Usage: ExecutionPlanGenerator inputfile [outputfile]");
				return;
			}

			var outFile = args.Length == 2 ? args[1] : null;

			var plan = new ExecutionPlan {
				Scripts = new List<string>(),
				Commands = new List<Command>()
			};



			var lines = File.ReadAllLines(args[0]);


			foreach (var statement in lines
				.Select(t => t.Split(new[] { ' ', '\t' }, 2))
				.Where(t => t.Length == 2)
				.Select(t => new Tuple<string, string>(t[0].Trim().ToLower(), t[1].Trim())))
			{
				switch (statement.Item1)
				{
					case "include":
						Include(statement.Item2, plan, args[0]);
						break;
					case "call":
						Call(statement.Item2, plan);
						break;
					case "reboot":
						plan.RebootOnCompletion = int.Parse(statement.Item2);
						break;
					case "out":
						if (args.Length < 2)
						{
							var path = statement.Item2;
							if (!Path.IsPathRooted(path))
							{
								path = Path.Combine(Path.GetDirectoryName(args[0]), path);
							}
							outFile = path;
						}
						break;
				}
			}

			var data = JsonConvert.SerializeObject(plan, Formatting.Indented);
			if (outFile == null)
			{
				Console.WriteLine(data);
			}
			else
			{
				File.WriteAllText(outFile, data);
			}
		}

		private static void Call(string line, ExecutionPlan plan)
		{
			var parts = line.Split(new[] { ' ', '\t'}, 2);
			var command = new Command() {
				Name = parts[0].Trim(),
				Arguments = new Dictionary<string, object>()
			};


			if (parts.Length == 2)
			{
				foreach (var x in parts[1]
					.Split(',')
					.Select(t => t.Split('='))
					.Where(t => t.Length == 2)
					.Select(t => new KeyValuePair<string, string>(t[0].Trim(), t[1].Trim())))
				{
					object value = null;
					long num;
					bool boolean;
					if (x.Value.StartsWith("\""))
					{
						value = x.Value.Substring(1, x.Value.Length - 2);
					}
					else if (long.TryParse(x.Value, out num))
					{
						value = num;
					}
					else if (bool.TryParse(x.Value, out boolean))
					{
						value = boolean;
					}
					else
					{
						continue;
					}
					command.Arguments.Add(x.Key, value);
				}
			}
			plan.Commands.Add(command);
		}

		private static void Include(string file, ExecutionPlan plan, string dslPath)
		{
			var path = file;
			if (!Path.IsPathRooted(file))
			{
				path = Path.Combine(Path.GetDirectoryName(dslPath), path);
			}

			var text = File.ReadAllText(path, Encoding.UTF8);
			plan.Scripts.Add(Convert.ToBase64String(Encoding.UTF8.GetBytes(text)));
		}
	}
}
