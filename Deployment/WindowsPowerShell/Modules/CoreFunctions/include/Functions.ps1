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



Function Get-PasswordAsSecureString {
<#
.SYNOPSIS
Convert to / request password as secure string.
#>
    [CmdletBinding()]
    param (
        [String] $Password = "",
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
    [CmdletBinding()]
	param (
		[Parameter(Mandatory=$true)]
		[String] $UserName,
		
		[String] $Password
	)
	
	$SecurePassword = Get-PasswordAsSecureString -Password "$Password"
	New-Object System.Management.Automation.PSCredential( "$UserName", $SecurePassword )
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



Function Start-Program {
	param (
		[String] $FilePath,
		[String[]] $ArgumentList = @(' '),
		[Int] $Timeout = 0,
		[Switch] $NoWait,
		[Switch] $PassThru,
        [String] $WorkingDir = (Get-Location).ProviderPath
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
    $ProcessStartInfo.WorkingDirectory = $WorkingDir
		
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
	
    $ProcessResult = New-Object PSObject |
        Add-Member -Name "ExitCode" -MemberType NoteProperty -Value $Process.ExitCode -PassThru |
        Add-Member -Name "StdOut" -MemberType NoteProperty -Value $Process.StandardOutput.ReadToEnd() -PassThru |
        Add-Member -Name "StdErr" -MemberType NoteProperty -Value $Process.StandardError.ReadToEnd() -PassThru
    
	$Process = $null
    
    Write-Log ( "STDOUT:`n{0}" -f $ProcessResult.StdOut )
    Write-Log ":STDOUT"
		
	Write-Log ( "STDERR:`n{0}" -f $ProcessResult.StdErr )
    Write-Log ":STDERR"
		
	Write-Log "Program has finished with exit code ($($ProcessResult.ExitCode))"

	if ($PassThru) {
		return $ProcessResult
	}
	else {
		return $null
	}
}
New-Alias -Name Exec -Value Start-Program



Function Backup-File {
    param (
        [String] $Path
    )

    $BackupFile = "$Path.bak"
    
    if (-not [IO.File]::Exists($Path)) {
        Write-LogError "Unable to backup file '$Path': file not exists."
        return
    }
    
    if ([IO.File]::Exists($BackupFile)) {
        try {
            [IO.File]::Delete($BackupFile)
        }
        catch {
            Write-LogError "Unable to delete existing .bak file '$BackupFile'."
            return
        }
    }

    Write-Log "Backing up file '$Path' to '$BackupFile'"
    [IO.File]::Copy($Path, $BackupFile, $true)
}



Function Install-Module {
    param (
        [String] $InstallPath,
        [String] $ModulePath,
        [String] $ModuleName
    )

    if ($ModuleName -eq "") {
        if ($ModulePath -eq "") {
            Stop-Execution -ExitString "Don't know which module should be installed."
        }
        else {
             $ModuleName = $ModulePath.Split("\")[-1]
        }
    }
    
    if ($InstallPath -eq "") {
        Stop-Execution -ExitString "To install the module destination path must be provided."
    }
    else {
        Write-Log "Installing the module to '$InstallPath'"
        
        $NewModulePath = [IO.Path]::Combine($InstallPath, $ModuleName)
        if ([IO.Directory]::Exists($NewModulePath)) {
            [IO.Directory]::Delete($NewModulePath, $true)
        }
            
        Copy-Item -Path $ModulePath -Destination $InstallPath -Recurse -Force -ErrorAction Stop
            
        Update-PsModulePath -AddPath "$InstallPath"
    }
}



Function Register-Module {
    param (
        [String] $ModulePath
    )
    $ModuleRoot = Split-Path -Path $ModulePath -Parent
    Write-Log "Registering the module at '$ModuleRoot'"
    Update-PsModulePath -AddPath "$ModuleRoot"
}



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
