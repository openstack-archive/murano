using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Management.Automation;
using System.Management.Automation.Runspaces;
using System.Text;
using Newtonsoft.Json;

namespace Mirantis.Keero.WindowsAgent
{
	class PlanExecutor
	{
		class ExecutionResult
		{
			public bool IsException { get; set; }
			public object Result { get; set; }
		}

		private readonly string path;

		public PlanExecutor(string path)
		{
			this.path = path;
		}

		public string Execute()
		{
			try
			{
				var plan = JsonConvert.DeserializeObject<ExecutionPlan>(File.ReadAllText(this.path));
				var resultPath = this.path + ".result";
				List<object> currentResults = null;
				try
				{
					currentResults = JsonConvert.DeserializeObject<List<object>>(File.ReadAllText(resultPath));
				}
				catch
				{
					currentResults = new List<object>();
				}


				var runSpace = RunspaceFactory.CreateRunspace();
				runSpace.Open();

				var runSpaceInvoker = new RunspaceInvoke(runSpace);
				runSpaceInvoker.Invoke("Set-ExecutionPolicy Unrestricted");
				if (plan.Scripts != null)
				{
					foreach (var script in plan.Scripts)
					{
						runSpaceInvoker.Invoke(Encoding.UTF8.GetString(Convert.FromBase64String(script)));
					}
				}

				while (plan.Commands != null && plan.Commands.Any())
				{
					var command = plan.Commands.First();

					var pipeline = runSpace.CreatePipeline();
					var psCommand = new Command(command.Name);
					if (command.Arguments != null)
					{
						foreach (var kvp in command.Arguments)
						{
							psCommand.Parameters.Add(kvp.Key, kvp.Value);
						}
					}
					pipeline.Commands.Add(psCommand);
					try
					{
						var result = pipeline.Invoke();
						if (result != null)
						{
							currentResults.Add(new ExecutionResult {
								IsException = false,
								Result = result.Select(SerializePsObject).Where(obj => obj != null).ToList()
							});
						}
					}
					catch (Exception exception)
					{
						currentResults.Add(new ExecutionResult {
							IsException = true,
							Result = new[] {
								exception.GetType().FullName, exception.Message
							}
						});
					}
					finally
					{
						plan.Commands.RemoveFirst();
						File.WriteAllText(path, JsonConvert.SerializeObject(plan));
						File.WriteAllText(resultPath, JsonConvert.SerializeObject(currentResults));
					}
				}
				runSpace.Close();
				var executionResult = JsonConvert.SerializeObject(new ExecutionResult {
					IsException = false,
					Result = currentResults
				}, Formatting.Indented);
				File.Delete(resultPath);
				return executionResult;
			}
			catch (Exception ex)
			{
				return JsonConvert.SerializeObject(new ExecutionResult {
					IsException = true,
					Result = ex.Message
				}, Formatting.Indented);
			}
		}
	
		private static object SerializePsObject(PSObject obj)
		{
			if (obj.BaseObject is PSCustomObject)
			{
				var result = new Dictionary<string, object>();
				foreach (var property in obj.Properties.Where(p => p.IsGettable))
				{
					try
					{
						result[property.Name] = property.Value.ToString();
					}
					catch
					{
					}
				}
				return result;
			}
			else
			{
				return obj.BaseObject;
			}
		}
	}

}
