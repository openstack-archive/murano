#ps1

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


$WindowsAgentConfigBase64 = '%AGENT_CONFIG_BASE64%'
$WindowsAgentConfigFile = "C:\Murano\Agent\WindowsAgent.exe.config"
$WindowsAgentLogFile = "C:\Murano\Agent\log.txt"

$CurrentComputerName = HOSTNAME
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
# (jose-phillips) If the Master Image or CloudBase-Init is already set the hostname this procedure fail.
if ($CurrentComputerName -ne $NewComputerName){
  Write-Log "Renaming computer to '$NewComputerName' ..."
  $null = Rename-Computer -NewName $NewComputerName -Force

  Write-Log "New name assigned, restart required."
  $RestartRequired = $true
}

Write-Log 'All done!'
if ( $RestartRequired ) {
    Write-Log "Restarting computer ..."
    Restart-Computer -Force
}
else {
    Start-Service 'Murano Agent'
}
