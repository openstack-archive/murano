#ps1

$WindowsAgentConfigBase64 = '%WINDOWS_AGENT_CONFIG_BASE64%'
$WindowsAgentConfigFile = "C:\Keero\Agent\WindowsAgent.exe.config"

$NewComputerName = '%INTERNAL_HOSTNAME%'

$RestartRequired = $false

Import-Module CoreFunctions

Write-Log "Updating Keero Windows Agent."
Stop-Service "Keero Agent"
Backup-File $WindowsAgentConfigFile
Remove-Item $WindowsAgentConfigFile -Force
ConvertFrom-Base64String -Base64String $WindowsAgentConfigBase64 -Path $WindowsAgentConfigFile
Exec sc.exe 'config','"Keero Agent"','start=','delayed-auto'
Write-Log "Service has been updated."

Write-Log "Renaming computer ..."
Rename-Computer -NewName $NewComputerName | Out-Null
Write-Log "New name assigned, restart required."
$RestartRequired = $true


Write-Log 'All done!'
if ( $RestartRequired ) {
    Write-Log "Restarting computer ..."
    Restart-Computer -Force
}
else {
    Start-Service 'Keero Agent'
}
