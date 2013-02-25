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

