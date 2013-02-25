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
    
    $__Logger.info("Logger initialized. Log file: '$LogPath'")
}



Function Write-LogInfo {
	param (
		[String[]] $Text
	)
    foreach ($Line in $Text) {
        $__Logger.info($Line)
    }
}
New-Alias -Name Write-Log -Value Write-LogInfo



Function Out-LogInfo {
	param (
		[Parameter(ValueFromPipeline=$true)]
		[String] $Text
	)
	$__Logger.info($Text)
}
New-Alias -Name Out-Log -Value Out-LogInfo



Function Write-LogWarning {
	param (
		[String] $Text
	)
    foreach ($Line in $Text) {
	    $__Logger.warn($Line)
    }
}



Function Out-LogWarning {
	param (
		[Parameter(ValueFromPipeline=$true)]
		[String] $Text
	)
	$__Logger__.warn($Text)
}



Function Write-LogError {
	param (
		[String] $Text
	)
    foreach ($Line in $Text) {
	    $__Logger.error($Line)
    }
}



Function Out-LogError {
	param (
		[Parameter(ValueFromPipeline=$true)]
		[String] $Text
	)
	$__Logger.error($Text)
}



Function Write-LogFatal {
	param (
		[String] $Text
	)
    foreach ($Line in $Text) {
	    $__Logger.fatal($Line)
    }
}



Function Out-LogFatal {
	param (
		[Parameter(ValueFromPipeline=$true)]
		[String] $Text
	)
	$__Logger.fatal($Text)
}



Function Write-LogDebug {
	param (
		[String] $Text
	)
    foreach ($Line in $Text) {
	    $__Logger.debug($Line)
    }
}



Function Out-LogDebug {
	param (
		[Parameter(ValueFromPipeline=$true)]
		[String] $Text
	)
	$__Logger.debug($Text)
}



Initialize-Logger
