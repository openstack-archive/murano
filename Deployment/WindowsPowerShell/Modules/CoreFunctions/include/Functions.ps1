Function Stop-Execution {
<#
.SYNOPSIS
Breaks execution with specified error code.

.DESCRIPTION
Function break script execution with error code provided. Error code may be 0 in case of non-error stop.

It also tries to parse ErrorRecord or Exception object (if provided) and logs this information.
#>
    [CmdletBinding(DefaultParameterSetName="Exception")]
    
	param (
        [Parameter(Position=1,ParameterSetName="Exception")]
		$InputObject = $null,
        
        [Parameter(ParameterSetName="ErrorString")]
		[String] $ExitString = "",
        
        [Parameter(ParameterSetName="ErrorString")]
		[Int] $ExitCode = 0,
        
        [Parameter(ParameterSetName="ErrorString")]
		[Switch] $Success
	)
    
    Function Exit-Function {
        if ($ExitCode -eq 0) {
            Write-LogInfo ( "STOP ({0}):`n{1}" -f $ExitCode, $ExitString )
        }
        else {
            Write-LogFatal ( "STOP ({0}):`n{1}" -f $ExitCode,  $ExitString )
        }
        
        Write-Log "__StopExecutionPreference__ = '$__StopExecutionPreference__'"
        switch ("$__StopExecutionPreference__") {
            "Exit" {
                exit $ExitCode
            }
            "ThrowIfException" {
                if ($InputObject -eq $null) {
                    exit $ExitCode
                }
                else {
                    throw $InputObject
                }
            }
            "ThrowAlways" {
                throw $InputObject
            }
            default {
                throw "Unknown value for __StopExecutionPreference__: '$__StopExecutionPreference__'"
            }
        }
    }

    switch($PSCmdlet.ParameterSetName) {
		"Exception" {
            #----------
            if ($InputObject -eq $null) {
		        $ExitString = "***** SCRIPT INTERRUPTED *****"
                $ExitCode = 255
                Exit-Function
            }
            #----------
        
        
            #----------
    		try {
    			$ErrorRecord = [System.Management.Automation.ErrorRecord] $InputObject
<#
                $ExitString = @"
$($ErrorRecord.ToString())

*** Invocation Info ***
$($ErrorRecord.InvocationInfo.PositionMessage)

*** CategoryInfo ***
$($ErrorRecord.CategoryInfo.ToString())

*** FullyQualifiedErrorId ***
$($ErrorRecord.FullyQualifiedErrorId.ToString())

*** ScriptStackTrace ***
$($ErrorRecord.ScriptStackTrace.ToString())
*** *** ***
"@
#>
                $ExitString = Out-String -InputObject $InputObject
                $ExitCode = 255
                Exit-Function
    		}
    		catch {
    			$ErrorRecord = $null
    			Write-LogWarning "Unable to cast InputObject to [System.Management.Automation.ErrorRecord]"
    		}
            #----------
            
            
            #----------
    		try {
    			$Exception = [System.Exception] $InputObject
    			#$ExitString = $Exception.ToString()
                $ExitString = Out-String -InputObject $InputObject
                $ExitCode = 255
                Exit-Function
    		}
    		catch {
    			$Exception = $null
    			Write-LogWarning "Unable to cast InputObject to [System.Exception]"
    		}
            #----------

        
            #----------
    		try {
    			$ExitString = Out-String -InputObject $InputObject
                $ExitCode = 255
                Exit-Function
    		}
    		catch {
    			Write-LogWarning "Unable to cast InputObject of type [$($InputObject.GetType())] to any of supported types."
    		}
            #----------
        }
        "ErrorString" {
            if ($Success) {
                $ExitString = "Script stopped with NO ERROR."
                $ExitCode = 0
            }
            
            Exit-Function
        }
    }
    
    $ExitString = "Unknown error occured in Stop-Execution"
    $ExitCode = 255
    Exit-Function
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



Function Show-EthernetNetworkAdapters {
    Get-WmiObject Win32_NetworkAdapter -Filter "PhysicalAdapter = 'True' AND AdapterTypeId = '0'" |
        Select-Object 'Index','MACAddress','NetConnectionId'
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



Function Get-PasswordAsSecureString {
<#
.SYNOPSIS
Convert to / request password as secure string.
#>
    param (
        [String] $Password,
        [String] $Prompt = "Please enter password"
    )
    
    if ($Password -eq "") {
        Read-Host -Prompt $Prompt -AsSecureString
    }
    else {
        ConvertTo-SecureString -String "$Password" -AsPlainText -Force
    }
}



Function New-Credential {
<#
.SYNOPSIS
Create new creadential object with username and password provided.
#>
	param (
		[Parameter(Mandatory=$true)]
		[String] $UserName,
		
		[String] $Password
	)
	
	$SecurePassword = Get-PasswordAsSecureString -Password "$Password"
	New-Object System.Management.Automation.PSCredential( "$UserName", $SecurePassword )
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



Function Invoke-WMSettingsChange {
    if (-not ("win32.nativemethods" -as [type])) {
        # Import SendMessageTimeout from Win32
        Add-Type -Namespace Win32 -Name NativeMethods -MemberDefinition @"
[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
public static extern IntPtr SendMessageTimeout(
    IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam,
    uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
"@
    }

    $HWND_BROADCAST = [IntPtr]0xFFFF
    $WM_SETTINGCHANGE = 0x001A
    $result = [UIntPtr]::Zero

    # Notify all windows of environment block change
    Write-Log "Executing 'SendMessageTimeout' ..."

    $retval = [Win32.NativeMethods]::SendMessageTimeout($HWND_BROADCAST, $WM_SETTINGCHANGE,
	    [UIntPtr]::Zero, "Environment", 2, 5000, [ref] $result)
    
    Write-Log "'SendMessageTimeout' returned '$retval' (non-zero is OK)"
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



Function Start-Program {
	param (
		[String] $FilePath,
		[String[]] $ArgumentList = @(' '),
		[Int] $Timeout = 0,
		[Switch] $NoWait,
		[Switch] $PassThru
	)

	trap {
		Write-LogError $_.Exception.Message
		return $null
	}

	Write-Log "Starting program: $FilePath $ArgumentList"
		
	$ProcessStartInfo = New-Object System.Diagnostics.ProcessStartInfo
	$ProcessStartInfo.FileName = $FilePath
	$ProcessStartInfo.Arguments = $ArgumentList
	$ProcessStartInfo.CreateNoWindow = $true
	$ProcessStartInfo.RedirectStandardOutput = $true
	$ProcessStartInfo.RedirectStandardError = $true
	$ProcessStartInfo.UseShellExecute = $false
		
	$Process = [System.Diagnostics.Process]::Start($ProcessStartInfo)
		
	if ($NoWait) {
		if ($PassThru) {
			return $Process
		}
		else {
			return $null
		}
	}
	else {
		if ($Timeout -eq 0) {
			$Process.WaitForExit()
		}
		else {
			$Process.WaitForExit($Timeout)
		}
	}
		
	Write-Log ( "STDOUT:`n{0}" -f $Process.StandardOutput.ReadToEnd() )
    Write-Log ":STDOUT"
		
	Write-Log ( "STDERR:`n{0}" -f $Process.StandardError.ReadToEnd() )
    Write-Log ":STDERR"
		
	Write-Log "Program has finished with exit code ($($Process.ExitCode))"

	if ($PassThru) {
		return $Process
	}
	else {
		return $null
	}
}
New-Alias -Name Exec -Value Start-Program



function Test-ModuleVersion {
<#
.SYNOPSIS
Test module version.

.DESCRIPTION
Function specified module (current module by default), and compares it's version to version provided.
Returned values:
* -2 : error occured
* -1 : module's version is lower than one provided
*  0 : module's version is equal to one provided
*  1 : module's version is greater than one provided
#>
    param (
        [String] $Name = "$__ModuleName",
        [String] $Version
    )

    $ModuleVersion = (Get-Module -Name $Name -ListAvailable).Version
    
    if ($ModuleVersion -eq $null) {
        Write-Log "Module '$Name' not found."
        return -2
    }
    
    try {
        $RequiredVersion = [System.Version]::Parse($Version)
    }
    catch {
        Write-Log "'$Version' is not a correct version string."
        return -2
    }
    
    $ModuleVersion.CompareTo($RequiredVersion)
}



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
