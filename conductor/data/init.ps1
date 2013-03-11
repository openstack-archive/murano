#ps1

$WindowsAgentConfigBase64 = '%WINDOWS_AGENT_CONFIG_BASE64%'
$WindowsAgentConfigFile = "C:\Keero\Agent\WindowsAgent.exe.config"

Import-Module CoreFunctions

Stop-Service "Keero Agent"
Backup-File $WindowsAgentConfigFile
Remove-Item $WindowsAgentConfigFile -Force
ConvertFrom-Base64String -Base64String $WindowsAgentConfigBase64 -Path $WindowsAgentConfigFile
Exec sc.exe 'config','"Keero Agent"','start=','delayed-auto'
Start-Service 'Keero Agent'
Write-Log 'All done!'