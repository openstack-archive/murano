#ps1

$WindowsAgentConfigBase64 = '%AGENT_CONFIG_BASE64%'
$WindowsAgentConfigFile = "C:\Murano\Agent\WindowsAgent.exe.config"
$WindowsAgentLogFile = "C:\Murano\Agent\log.txt"

$NewComputerName = '%INTERNAL_HOSTNAME%'
$MuranoFileShare = '\\%MURANO_SERVER_ADDRESS%\share'

$CaRootCertBase64 = "%CA_ROOT_CERT_BASE64%"
$CaRootCertFile = "C:\Murano\ca.cert"

$RestartRequired = $false

Import-Module CoreFunctions
Initialize-Logger 'CloudBase-Init' 'C:\Murano\PowerShell.log'

$ErrorActionPreference = 'Stop'

trap {
    Write-LogError '<exception>'
    Write-LogError $_ -EntireObject
    Write-LogError '</exception>'
    exit 1
}

Write-Log "Importing CA certificate ..."
if ($CaRootCertBase64 -eq '') {
    Write-Log "Importing CA certificate ... skipped"
}
else {
    ConvertFrom-Base64String -Base64String $CaRootCertBase64 -Path $CaRootCertFile
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2 $CaRootCertFile
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("AuthRoot","LocalMachine")
    $store.Open("MaxAllowed")
    $store.Add($cert)
    $store.Close()
    Write-Log "Importing CA certificate ... done"
}

Write-Log "Updating Murano Windows Agent."
Stop-Service "Murano Agent"
Backup-File $WindowsAgentConfigFile
Remove-Item $WindowsAgentConfigFile -Force -ErrorAction 'SilentlyContinue'
Remove-Item $WindowsAgentLogFile -Force -ErrorAction 'SilentlyContinue'
ConvertFrom-Base64String -Base64String $WindowsAgentConfigBase64 -Path $WindowsAgentConfigFile
Exec sc.exe 'config','"Murano Agent"','start=','delayed-auto'
Write-Log "Service has been updated."

Write-Log "Adding environment variable 'MuranoFileShare' = '$MuranoFileShare' ..."
[Environment]::SetEnvironmentVariable('MuranoFileShare', $MuranoFileShare, [EnvironmentVariableTarget]::Machine)
Write-Log "Environment variable added."

Write-Log "Renaming computer to '$NewComputerName' ..."
$null = Rename-Computer -NewName $NewComputerName -Force

Write-Log "New name assigned, restart required."
$RestartRequired = $true


Write-Log 'All done!'
if ( $RestartRequired ) {
    Write-Log "Restarting computer ..."
    Restart-Computer -Force
}
else {
    Start-Service 'Murano Agent'
}
