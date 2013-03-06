Function Set-LocalUserPassword {
    param (
        [String] $UserName,
        [String] $Password,
        [Switch] $Force
    )
    
    trap { Stop-Execution $_ }
    
    if ((Get-WmiObject Win32_UserAccount -Filter "LocalAccount = 'True' AND Name='$UserName'") -eq $null) {
        throw "Unable to find local user account '$UserName'"
    }
    
    if ($Force) {
        Write-Log "Changing password for user '$UserName' to '*****'" # :)
        ([ADSI] "WinNT://./$UserName").SetPassword($Password) | Out-Null
    }
    else {
        Write-LogWarning "You are trying to change the password for the user '$UserName'. To do this please run the command again with -Force parameter."
    }
}



Function Set-AutoLogonCredentials {
	param (
		[String] $DomainName,
		[String] $UserName,
		[String] $Password
	)
	
	$KeyName = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"

	if ($DomainName -ne "") {
		$UserName = "$DomainName\$UserName"
	}
    
    Write-Log "Setting AutoLogon credentials ..."
	try {
    	[Microsoft.Win32.Registry]::SetValue($KeyName, "DefaultUserName", "$UserName", [Microsoft.Win32.RegistryValueKind]::String)
    	[Microsoft.Win32.Registry]::SetValue($KeyName, "DefaultPassword", "$Password", [Microsoft.Win32.RegistryValueKind]::String)
    	[Microsoft.Win32.Registry]::SetValue($KeyName, "AutoAdminLogon", "1", [Microsoft.Win32.RegistryValueKind]::String)
    	[Microsoft.Win32.Registry]::SetValue($KeyName, "ForceAutoLogon", "1", [Microsoft.Win32.RegistryValueKind]::String)
    }
    catch {
        Write-LogError "FAILED"
        return
    }
    
    Write-Log "SUCCESS"
}



Function Join-Domain {
<#
.SYNOPSIS
Executes "Join domain" action.
#>
	param (
		[String] $DomainName,
		[String] $UserName,
		[String] $Password,
        [Switch] $AllowRestart
	)
	
	$Credential = New-Credential -UserName "$DomainName\$UserName" -Password $Password

	# Add the computer to the domain
	if (Test-ComputerName -DomainName $DomainName) {
		#Stop-Execution -Success -ExitString "Computer already joined to domain '$DomainName'"
        Write-LogWarning "Computer already joined to domain '$DomainName'"
	}
	else {
		Write-Log "Joining computer to domain '$DomainName' ..."
		
		Add-Computer -DomainName $DomainName -Credential $Credential -Force -ErrorAction Stop
		
        if ($AllowRestart) {
            Write-Log "Restarting computer ..."
            Restart-Computer -Force
        }
        else {
		    #Stop-Execution -ExitCode 3010 -ExitString "Please restart the computer now."
            Write-Log "Please restart the computer now."
        }
	}
}



Function Expand-Template {
    param (
        [String] $TemplateFile,
        [String] $OutputFile,
        [System.Collections.Hashtable] $ReplacementList,
        [String] $Encoding = "Ascii"
    )
    
    if (-not [IO.File]::Exists($TemplateFile)) {
        Write-Error "File '$TemplateFile' not exists"
        return $null
    }
    
    if ([IO.File]::Exists($OutputFile)) {
        [IO.File]::Delete($OutputFile)
    }
    
    Get-Content $TemplateFile -Encoding $Encoding |
        ForEach-Object {
            $Line = $_
            foreach ($Key in $ReplacementList.Keys) {
                $Line = $Line.Replace("%_$($Key)_%", $ReplacementList[$Key])
            }
            Add-Content -Path $OutputFile -Encoding $Encoding -Value $Line
        }
}



Function Add-WindowsFeatureWrapper {
<#
.SYNOPSIS
Wraps Install-WindowsFeature function.

.DESCRIPTION
This function adds some logic to multiple feature installation.

It fails if any of required features fails.

It reports that reboot required if it is required, or restarts the computer.
#>
	param (
		[Parameter(Mandatory=$true)]
		[String[]] $Name,
		[Switch] $IncludeManagementTools,
		[Switch] $AllowRestart,
        [Switch] $NotifyRestart
	)
	
    $RestartNeeded = $false
    
	foreach ($Feature in $Name) {
		Write-Log "Installing feature '$Feature' ..."
		$Action = Install-WindowsFeature `
			-Name $Feature `
			-IncludeManagementTools:$IncludeManagementTools `
			-ErrorAction Stop
		
		if ($Action.Success -eq $true) {
			if ($Action.FeatureResult.RestartNeeded -eq $true) {
				Write-LogWarning "Restart required"
				$RestartNeeded = $true
			}
			Write-Log "Feature '$Feature' installed successfully"
		}
		else {
			Stop-Execution "Failed to install feature '$Feature'"
		}
	}
	
    if ($RestartNeeded) {
        Write-Log "Restart required to finish feature(s) installation."
        if ($AllowRestart) {
            Write-Log "Restarting computer ..."
            Restart-Computer -Force
        }
        elseif ($NotifyRestart) {
            Stop-Execution -ExitCode 3010 -ExitString "Please restart the computer now."
        }
    }
}



Function Test-WmiReturnValue {
<#
.SYNOPSIS
Check the ReturnValue property of the object provided.

.DESCRIPTION
This funciton checks if ReturnValue property is equal to 0.

=== TODO ===
If it is not, then funtion should try to provide desctiption for the error code based on the WMI object type.
WMI object type must be provided explicitely.
#>
	param (
		[Parameter(ValueFromPipeline=$true,Mandatory=$true)]
		$InputObject,
		[String] $Type = ""
	)
		
	try {
		$ReturnValue = $InputObject.ReturnValue
	}
	catch {
		throw "Property 'ReturnValue' not found on this object"
	}
		
	if ($ReturnValue -eq 0) {
		Write-Log "WMI operation completed successfully"
	}
	else {
		throw "Operation failed with status code = $ReturnValue"
	}
}



Function Set-NetworkAdapterConfiguration {
<#
.SYNOPSIS
Set network adapter configuration.

.DESCRIPTION


.EXAMPLE
PS> Set-NetworkAdapterConfiguration -MACAddress aa:bb:cc:dd:ee:ff -Auto

Convert "dynamic" parameters (DHCP) to "static" (manual) for network adapter with MAC address aa:bb:cc:dd:ee:ff

.EXAMPLE
PS> Set-NetworkAdapterConfiguration -MACAddress aa:bb:cc:dd:ee:ff -DNSServer "192.168.0.1","192.168.0.2"

Configure DNS servers list for network adapter with MAC address aa:bb:cc:dd:ee:ff

#>
	param (
		[String] $MACAddress = "",
		
		[Parameter(ParameterSetName="ManualConfig")]
		[String] $IPAddress = "",
		
		[Parameter(ParameterSetName="ManualConfig")]
		[String] $IPNetmask = "",
		
		[Parameter(ParameterSetName="ManualConfig")]
		[String[]] $IPGateway = @(),
		
		[Parameter(ParameterSetName="ManualConfig")]
		[String[]] $DNSServer = @(),
		
		[Parameter(ParameterSetName="ManualConfig")]
		[Switch] $FirstAvailable,

		[String] $Name = "",
		
		[Parameter(ParameterSetName="AutoConfig",Mandatory=$true)]
		[Switch] $Auto,

		[Parameter(ParameterSetName="AutoConfig")]
		[Switch] $All
	)
    
	Write-Log "Configuring network adapter(s) ..."
    
	:SetIPAddress switch($PSCmdlet.ParameterSetName) {
		"AutoConfig" {
            Write-Log "'auto' mode"
            
			$IPv4RegExp = "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
			
			if ($All -eq $true) {
				$Filter = { $_.AdapterTypeId -eq 0 }
				$Name = ""
			}
			else {
				$Filter = { $_.MACAddress -eq $MACAddress }
			}
			
			Get-WmiObject Win32_NetworkAdapter |
				Where-Object $Filter |
				ForEach-Object {
					$NetworkAdapter = $_
					$AdapterConfig = Get-WmiObject Win32_NetworkAdapterConfiguration |
						Where-Object { $_.Index -eq $NetworkAdapter.DeviceId }
					
					Write-Log "Configuring '$($NetworkAdapter.Name)' ..."
					
					for ($i = 0; $i -lt $AdapterConfig.IPAddress.Length; $i++) {
						if ($AdapterConfig.IPAddress[$i] -match $IPv4RegExp) {
							$IPAddress = $AdapterConfig.IPAddress[$i]
							$IPNetmask = $AdapterConfig.IPSubnet[$i]
							$IPGateway = $AdapterConfig.DefaultIPGateway
                            $DNSServer = $AdapterConfig.DNSServerSearchOrder
							
							Write-Log "Setting IP address ($IPAddress), netmask ($IPNetmask) ..."
							$AdapterConfig.EnableStatic($IPAddress, $IPNetmask) | Out-Null
                            
                            Write-Log "Setting default gateways ($IPGateway) ..."
							$AdapterConfig.SetGateways($IPGateway) | Out-Null
                            
                            Write-Log "Setting DNS servers ($DNSServer) ..."
                            $AdapterConfig.SetDNSServerSearchOrder($DNSServer) | Out-Null
						}
					}
                    
                    Write-Log "'$($NetworkAdapter.Name)' configured"
				}
		}
		"ManualConfig" {
            Write-Log "'manual' mode"
			if ( $FirstAvailable ) {
                Write-Log "Selecting first available network adapter ..."
				$NetworkAdapter = Get-WmiObject Win32_NetworkAdapter |
					Where-Object { $_.AdapterTypeId -eq 0 } |
					Select-Object -First 1
			}
			else {
				$NetworkAdapter = Get-WmiObject Win32_NetworkAdapter |
					Where-Object { $_.MACAddress -eq $MACAddress }
			}
			
			if ( $NetworkAdapter -eq $null ) {
				Write-LogError "Network adapter with MAC = '$MACAddress' not found."
				return
			}
			
			$AdapterConfig = Get-WmiObject Win32_NetworkAdapterConfiguration |
				Where-Object { $_.Index -eq $NetworkAdapter.DeviceId }

			if (($IPAddress -ne "") -and ($IPNetmask -ne "")) {
				Write-Log "Configuring IP address / netmask for '$($NetworkAdapter.Name)' ..."
				
				<#
				for ($i = 0; $i -lt $AdapterConfig.IPAddress.Length; $i++)
				{
					if (($AdapterConfig.IPAddress[$i] -eq $IPAddress) -and ($AdapterConfig.IPSubnet[$i] -eq $IPNetmask))
					{
						Write-Log "There is an adapter with required configuration."
						break SetIPAddress
					}
				}
				#>
				Write-Log "Setting IP address $IPAddress, netmask $IPNetmask"
				$AdapterConfig.EnableStatic("$IPAddress", "$IPNetmask") | Out-Null
				
				Write-Log "IP address configured."
			}
			
			if ($IPGateway.Count -gt 0) {
				Write-Log "Configuring IP gateway for '$($NetworkAdapter.Name)' ..."
				
				$AdapterConfig.SetGateways($IPGateway) | Out-Null
				
				Write-Log "IP gateway configured."
			}
			
			if ($DNSServer.Count -gt 0) {
				Write-Log "Configuring DNS server(s) for '$($NetworkAdapter.Name)' ..."
				
				$AdapterConfig.SetDNSServerSearchOrder($DNSServer) | Out-Null
				
				Write-Log "DNS configured."
			}
		}
	}

	if ($Name -ne "") {
		Write-Log "Changing adapter name '$($NetworkAdapter.NetConnectionId)' --> '$Name'"
		$NetworkAdapter.NetConnectionId = "$Name"
		$NetworkAdapter.Put() | Out-Null
	}
}



Function Show-EthernetNetworkAdapters {
    Get-WmiObject Win32_NetworkAdapter -Filter "PhysicalAdapter = 'True' AND AdapterTypeId = '0'" |
        Select-Object 'Index','MACAddress','NetConnectionId'
}



Function Test-ComputerName {
<#
.SYNOPSIS
Test if computer name is set, and the computer belongs to specified domain / workgroup.

.DESCRIPTION
Function tests the following conditions:
* the computer name is equal to the provided one
* the computer is a part of domain
* the computer belongs to the specified domain
* the computer belongs to the specified workgroup

Multiple checks are logically ANDed.
#>
    [CmdletBinding()]
	param (
		[String] $ComputerName,
		[String] $DomainName,
		[String] $WorkgroupName,
		[Switch] $PartOfDomain
	)
	process {
    	$ComputerSystem = Get-WmiObject Win32_ComputerSystem
    	
    	if (($ComputerName -ne "") -and ($ComputerSystem.Name -ne "$ComputerName")) {
            Write-Error "ComputerName is not equal to '$ComputerName'"
    		return $false
    	}
    	
    	if (($DomainName -ne "") -and ($ComputerSystem.Domain -ne "$DomainName")) {
            Write-Error "DomainName is not equal to '$DomainName'"
    		return $false
    	}
    	
    	if (($WorkgroupName -ne "") -and ($ComputerSystem.Workgroup -ne "$WorkgroupName")) {
            Write-Error "WorkgroupName is not equal to '$WorkgroupName'"
    		return $false
    	}
    	
    	if (($PartOfDOmain -eq $true) -and ($ComputerSystem.PartOfDomain -eq $false)) {
            Write-Error "Computer is not the part of any domain."
    		return $false
    	}
    	
    	return $true
    }
}



Function Set-ComputerName {
    param (
        [String] $Name
    )
    
    
	# Rename the computer
	if ($Name -ne "") {
		if (Test-ComputerName -ComputerName $Name) {
			Stop-Execution -Success -ExitString "Computer name already configured"
		}
		else {
			Write-Log "Renaming computer to '$Name'"
				
			Rename-Computer -NewName $NewName -Force -ErrorAction Stop

			Stop-Execution -ExitCode 3010 -ExitString "Please restart the computer now"
		}
	}
}




Function Resolve-LdapDnsName {
    param (
        [String] $DomainName
    )
    
    Resolve-DNSName -Type "SRV" -Name "_ldap._tcp.dc._msdcs.$DomainName" |
        Where-Object { $_.Type -eq "A" } |
        Select-Object -Property Name,IPAddress
}



Function Wait-LdapServerAvailable {
    param (
        [String] $DomainName,
        [Int] $PingSeqCountThreshold = 10,
        [Int] $PingSeqPerHostThreshold = 5
    )
    
    $LdapServerList = @( Resolve-LdapDnsName $DomainName )
    Write-Log @( "Ldap server list:", ( $LdapServerList | Out-String ) )
    
    :MainLoop foreach ($LdapServer in $LdapServerList) {
        $PingSeqCount = 0
        $PingSeqPerHost = 0
        while ($PingSeqPerHost -lt $PingSeqPerHostThreshold) {
            if (Test-Connection -ComputerName $LdapServer.IpAddress -Count 1 -Quiet) {
                Write-Log "Ping '$($LdapServer.Name)' OK"
                $PingSeqCount++
            }
            else {
                Write-Log "Ping '$($LdapServer.Name)' FAILED"
                $PingSeqCount = 0
                $PingSeqPerHost++
            }
            
            if ($PingSeqCount -ge $PingSeqCountThreshold) {
                Write-Log "Returning true"
                return $true
            }
            
            Start-Sleep -Seconds 1
        }
    }
    
    Write-Log "Returning false"
    return $false
}



Function Get-ConfigDriveObject {
    [CmdletBinding()]
    param (
        [Parameter(ParameterSetName="MetaData")]
        [Switch] $MetaData,
        
        [Parameter(ParameterSetName="UserData")]
        [Switch] $UserData,
        
        [Parameter(ParameterSetName="CustomObject")]
        [String] $CustomObject,
        
        [String] $Path = "openstack/latest"
    )
    
    $ConfigDrivePrefix = "http://169.254.169.154/$Path"
    
    try {
        switch($PSCmdlet.ParameterSetName) {
            "MetaData" {
                $ConfigDriveObjectUrl = "$ConfigDrivePrefix/meta_data.json"
                $MetaData = Invoke-WebRequest $ConfigDriveObjectUrl
                ConvertFrom-Json $MetaData.Content
            }
            "UserData" {
                $ConfigDriveObjectUrl = "$ConfigDrivePrefix/user_data"
                $UserData = Invoke-WebRequest $ConfigDriveObjectUrl
                $UserData.Content
            }
            "CustomObject" {
                $ConfigDriveObjectUrl = "$ConfigDrivePrefix/$CustomObject"
                $CustomObject = Invoke-WebRequest $ConfigDriveObjectUrl
                $CustomObject.Content
            }
        }
    }
    catch {
        Write-Error "Unable to retrieve object from 'ConfigDriveObjectUrl'"
        return $null
    }
}



Function Update-AgentConfig {
    param (
        [String] $RootPath = "C:\Keero\Agent"
    )
    
    try {
        $MetaData = Get-ConfigDriveObject -MetaData -ErrorAction Stop
        if ($MetaData.meta -ne $null) {
            Stop-Service "Keero Agent" -Force
            Expand-Template -TemplateFile "$RootPath\WindowsAgent.exe.config.template" -OutputFile "$RootPath\WindowsAgent.exe.config" -ReplacementList $MetaData.meta
            Start-Service "Keero Agent"
        }
    }
    catch {
        Write-LogError "Failed to update agent configuration"
    }
}



Function Update-PsModulePath {
    param (
        [String] $AddPath = ""
    )

    $NewPsModulePath = (
            @([Environment]::GetEnvironmentVariable("PsModulePath", [EnvironmentVariableTarget]::Machine) -split ";") + @($AddPath) `
            | Select-Object -Unique
        ) -join ';'
    
    [Environment]::SetEnvironmentVariable("PsModulePath", $NewPsModulePath, [EnvironmentVariableTarget]::Machine)
    
    Invoke-WMSettingsChange
}



Function Get-ModuleHelp {
    param (
        [String] $ModuleName = $__ModuleName,
        [String] $Path = "",
        [Switch] $File,
        [Int] $Width = 80
    )
    
	$sb = {
        $Module = Get-Module $ModuleName
    	
    	"`n"
        "Module: $($Module.Name)"
    	"Module version: $($Module.Version)"
    	"`n"
        "{0} Module Description {0}" -f ('=' * 30)
        "`n"
        
    	Get-Help "about_$($Module.Name)" | Out-String -Width $Width
    	
        "{0} Exported Functions {0}" -f ('=' * 30)
        "`n"
        	
    	foreach ($CommandName in $Module.ExportedCommands.Keys) {
            '-' * 80
    		Get-Help -Name $CommandName -Detailed | Out-String -Width $Width
    	}
    }
    
    if (($File) -and ($Path -eq "")) {
        $Path = [IO.Path]::GetTempFileName()
    }
    
    if ($Path -ne "") {
        & $sb | Out-File -FilePath $Path -Force
    }
    else {
        & $sb | Out-Default
    }
    
    if ($File) {
        notepad.exe "$Path"
    }
}



Function New-ModuleTemplate {
    param (
        [Parameter(Mandatory=$true)]
        [String] $Name,
        
        [String] $Path = "$($Env:USERPROFILE)\Documents\WindowsPowerShell\Modules",
        
        [Switch] $Force
    )
    if ([IO.Directory]::Exists("$Path\$Name")) {
        if ($Force) {
            [IO.Directory]::Delete("$Path\$Name", $true)
        }
        else {
            Write-Error "Folder '$Path\$Name' already exists. Remove it manually or specify -Force switch."
            return
        }
    }
    
    
    [IO.Directory]::CreateDirectory("$Path\$Name")
    [IO.Directory]::CreateDirectory("$Path\$Name\en-US")
    [IO.Directory]::CreateDirectory("$Path\$Name\include")
    
    
    Set-Content -Path "$Path\$Name\en-US\about_$Name.help.txt" -Value @'
'@

    
    Set-Content -Path "$Path\$Name\Config.ps1" -Value @'
$script:__ModulePath = $PsScriptRoot
$script:__ModuleName = $PsScriptRoot.Split("\")[-1]
$script:__DefaultLogPath = [IO.Path]::Combine([IO.Path]::GetTempPath(), "PowerShell_$__ModuleName.log")

$global:__StopExecutionExitsSession__ = $false
'@    
    
    
    Set-Content -Path "$Path\$Name\$Name.psm1" -Value @'
# Import config first
. "$PsScriptRoot\Config.ps1"

# Import functions from 'Include' subfolder
Get-ChildItem "$PsScriptRoot\Include" -Filter "*.ps1" |
    ForEach-Object {
        . "$($_.FullName)"
    }

Export-ModuleMember -Function * -Alias *

Initialize-Logger -ModuleName $__ModuleName -LogPath $__DefaultLogPath

Write-Log "Module loaded from '$PsScriptRoot'"
'@
    
    
    New-ModuleManifest `
        -Path "$Path\$Name\$Name.psd1" `
        -ModuleToProcess "$Name.psm1" `
        -RequiredModules "CoreFunctions"
    
}



function New-SqlServerConnection {
    param (
        [String] $ServerName,
        [String] $UserName = '',
        [String] $Password = '',
        $Credentials,
        [Switch] $SqlAuth
    )

    if ($Credentials -eq $null) {
        if ($UserName -eq '') {
            throw "User name must be provided in order to create credentials object!"
        }
        
        $Credentials = New-Credential -UserName $UserName -Password $Password
    }

    $Server = New-Object `
        -TypeName Microsoft.SqlServer.Management.Smo.Server `
        -ArgumentList $ServerName
    
    $LoginName = $Credentials.UserName -replace("^\\", "")

    try {
        if ($SqlAuth) {
            $Server.ConnectionContext.set_LoginSecure($false)
            $Server.ConnectionContext.set_Login($LoginName)
            $Server.ConnectionContext.set_SecurePassword($Credentials.Password)
        }
        else {
            throw "Not implemented!"
        }
    }
    catch {
        return $null
    }

    $Server
}



function Import-SqlServerAssemblies {
<#
.SYNOPSIS
Import assemblies required to work with Sql Server instance from PowerShell

.DESCRIPTION
Possible assembly list:
    "Microsoft.SqlServer.Management.Common"
    "Microsoft.SqlServer.Smo"
    "Microsoft.SqlServer.Dmf"
    "Microsoft.SqlServer.Instapi"
    "Microsoft.SqlServer.SqlWmiManagement"
    "Microsoft.SqlServer.ConnectionInfo"
    "Microsoft.SqlServer.SmoExtended"
    "Microsoft.SqlServer.SqlTDiagM"
    "Microsoft.SqlServer.SString"
    "Microsoft.SqlServer.Management.RegisteredServers"
    "Microsoft.SqlServer.Management.Sdk.Sfc"
    "Microsoft.SqlServer.SqlEnum"
    "Microsoft.SqlServer.RegSvrEnum"
    "Microsoft.SqlServer.WmiEnum"
    "Microsoft.SqlServer.ServiceBrokerEnum"
    "Microsoft.SqlServer.ConnectionInfoExtended"
    "Microsoft.SqlServer.Management.Collector"
    "Microsoft.SqlServer.Management.CollectorEnum"
    "Microsoft.SqlServer.Management.Dac"
    "Microsoft.SqlServer.Management.DacEnum"
    "Microsoft.SqlServer.Management.Utility"

.LINKS
http://msdn.microsoft.com/en-us/library/cc281962%28v=sql.105%29.aspx
#>
    $AssemblyList = @(
        "Microsoft.SqlServer.Smo"
        "Microsoft.SqlServer.SmoExtended"
    )
        
    foreach ($asm in $AssemblyList) {
        [System.Reflection.Assembly]::LoadWithPartialName($asm) | Out-Null
    }
}



function Import-SqlServerProvider {
    $SqlPsReg="HKLM:\SOFTWARE\Microsoft\PowerShell\1\ShellIds\Microsoft.SqlServer.Management.PowerShell.sqlps"

    if (Get-ChildItem $SqlPsReg -ErrorAction "SilentlyContinue") {
        throw "SQL Server Provider for Windows PowerShell is not installed."
    }
    else {
        $Item = Get-ItemProperty $SqlPsReg
        $SqlPsPath = [System.IO.Path]::GetDirectoryName($Item.Path)
    }

    #
    # Set mandatory variables for the SQL Server provider
    #
    $global:SqlServerMaximumChildItems = 0
    $global:SqlServerConnectionTimeout = 30
    $global:SqlServerIncludeSystemObjects = $false
    $global:SqlServerMaximumTabCompletion = 1000

    #
    # Load the snapins, type data, format data
    #
    Push-Location
    Set-Location $sqlpsPath
    
    Add-PSSnapin SqlServerCmdletSnapin100
    Add-PSSnapin SqlServerProviderSnapin100
    
    Update-TypeData -PrependPath SQLProvider.Types.ps1xml 
    Update-FormatData -PrependPath SQLProvider.Format.ps1xml 
    
    Pop-Location
}

