Function Initialize-Logger {
    param (
        [String] $ModuleName = $__ModuleName,
        [String] $LogPath = $__DefaultLogPath
    )
    
    if (-not ("log4net.LogManager" -as [type])) {
        $FileStream = ([System.IO.FileInfo] (Get-Item "$__ModulePath\log4net.dll")).OpenRead()

        $AssemblyBytes = New-Object Byte[] $FileStream.Length
        [Void] $FileStream.Read($AssemblyBytes, 0, $FileStream.Length)

        $FileStream.Close()

        [Void] [System.Reflection.Assembly]::Load($AssemblyBytes)
    }

    [log4net.GlobalContext]::Properties["LogPath"] = $LogPath
    [log4net.GlobalContext]::Properties["ModuleName"] = $ModuleName

    $script:__Logger = [log4net.LogManager]::GetLogger("PowerShell")

    $Log4NetConfig = New-Object System.IO.FileInfo("$__ModulePath\log4net.config")

    [log4net.Config.XmlConfigurator]::Configure($Log4NetConfig)
    
    $__Logger.info("Logger initialized. Log file: '$LogPath'`n")
}


Function Out-LogInfo {
    param (
        [Parameter(ValueFromPipeline=$true)]
        $InputObject,
        [Switch] $EntireObject
    )
    process {
        if ($EntireObject) {
            $__Logger.info("`n$(Out-String -InputObject $InputObject)")
        }
        else {
            foreach ($Object in $InputObject) {
                $__Logger.info((Out-String -InputObject $Object))
            }
        }
    }
}
New-Alias -Name Out-Log -Value Out-LogInfo
New-Alias -Name Write-Log -Value Out-LogInfo



Function Out-LogWarning {
    param (
        [Parameter(ValueFromPipeline=$true)]
        $InputObject,
        [Switch] $EntireObject
    )
    process {
        if ($EntireObject) {
            $__Logger.warn("`n$(Out-String -InputObject $InputObject)")
        }
        else {
            foreach ($Object in $InputObject) {
                $__Logger.warn((Out-String -InputObject $Object))
            }
        }
    }
}
New-Alias -Name Write-LogWarning -Value Out-LogWarning



Function Out-LogError {
    param (
        [Parameter(ValueFromPipeline=$true)]
        $InputObject,
        [Switch] $EntireObject
    )
    process {
        if ($EntireObject) {
            $__Logger.error("`n$(Out-String -InputObject $InputObject)")
        }
        else {
            foreach ($Object in $InputObject) {
                $__Logger.error((Out-String -InputObject $Object))
            }
        }
    }
}
New-Alias -Name Write-LogError -Value Out-LogError



Function Out-LogFatal {
    param (
        [Parameter(ValueFromPipeline=$true)]
        $InputObject,
        [Switch] $EntireObject
    )
    process {
        if ($EntireObject) {
            $__Logger.fatal("`n$(Out-String -InputObject $InputObject)")
        }
        else {
            foreach ($Object in $InputObject) {
                $__Logger.fatal((Out-String -InputObject $Object))
            }
        }
    }
}
New-Alias -Name Write-LogFatal -Value Out-LogFatal



Function Out-LogDebug {
    param (
        [Parameter(ValueFromPipeline=$true)]
        $InputObject,
        [Switch] $EntireObject
    )
    process {
        if ($EntireObject) {
            $__Logger.debug("`n$(Out-String -InputObject $InputObject)")
        }
        else {
            foreach ($Object in $InputObject) {
                $__Logger.debug((Out-String -InputObject $Object))
            }
        }
    }
}
New-Alias -Name Write-LogDebug -Value Out-LogDebug



Initialize-Logger
