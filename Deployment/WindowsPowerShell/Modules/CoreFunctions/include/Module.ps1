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



function Update-PsModulePath {
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
