Import-Module '.\OptionParser.psm1'
Import-Module '.\SQLServerOptionParsers.psm1'

function New-SQLServer {
    <#
    .SYNOPSIS
    Installs new MS SQL Server instance

    .DESCRIPTION
    Installs new MS SQL Server instance in unattended mode.

    .PARAMETER SetupRoot
    MS SQL Server installation files root directory. Normally it is just DVD drive name.
    #>

    param(
        [parameter(Mandatory = $true)]
        [string]$SetupRoot
    )

    $SetupDir = Get-Item $SetupRoot
    $SetupExe = $SetupDir.GetFiles("setup.exe")[0]

    $parser = New-OptionParserInstall
    $ExitCode = $parser.ExecuteBinary($SetupExe.FullName, @{"QS" = $null; "FEATURES" = @("SQLEngine", "Conn", "SSMS", "ADV_SSMS")})

    if ($ExitCode -ne 0) {
        throw "Installation executable exited with code $("{0:X8}" -f $ExitCode)"
    }
}

function Remove-SQLServer {
    <#
    .SYNOPSIS
    Uninstalls MS SQL Server instance installed with New-SQLServer cmdlet

    .DESCRIPTION
    Uninstalls MS SQL Server instance installed with New-SQLServer cmdlet in unattended mode

    .PARAMETER SetupRoot
    MS SQL Server installation files root directory. Normally it is just DVD drive name.
    #>

    param(
        [parameter(Mandatory = $true)]
        [string]$SetupRoot
    )

    $SetupDir = Get-Item $SetupRoot
    $SetupExe = $SetupDir.GetFiles("setup.exe")[0]

    $parser = New-OptionParserUninstall
    $ExitCode = $parser.ExecuteBinary($SetupExe.FullName, @{"Q" = $null; "FEATURES" = @("SQLEngine", "Conn", "SSMS", "ADV_SSMS")})

    if ($ExitCode -ne 0) {
        throw "Installation executable exited with code $("{0:X8}" -f $ExitCode)"
    }
}

function Invoke-SQLText {
    <#
    .SYNOPSIS
    Invokes SQL text

    .DESCRIPTION
    Invokes SQL text

    .PARAMETER SQL
    SQL Text

    .PARAMETER User
    SQL Server user name

    .PARAMETER SQL
    SQL Server user password
    #>
    param(
        [parameter(Mandatory = $true)]
        [string]$SQL,
        [string]$User = $null,
        [string]$Password = $null
    )

    $Binary = Get-Command "sqlcmd.exe"

    $tempFile = [IO.Path]::GetTempFileName()
    $tempFile = Get-Item $tempFile
    Set-Content -Path $tempFile -Value $SQL

    $CommandLine = @('-i', "`"$($tempFile.FullName)`"")
    if (($User -ne $null) -and ($User -ne '')) {
        $CommandLine = $CommandLine + '-U'
        $CommandLine = $CommandLine + $User
        $CommandLine = $CommandLine + '-P'
        $CommandLine = $CommandLine + $Password
    }

    Write-Host "Executing: `"$($Binary.Path)`" $($CommandLine -join ' ')"
    $process = [System.Diagnostics.Process]::Start($Binary, $CommandLine)
    $process.WaitForExit()
    $process.Refresh()

    $ExitCode = $process.ExitCode
    if ($ExitCode -ne 0) {
        throw "SQLCMD.EXE returned with exit code $ExitCode"
    }
   
    Remove-Item $tempFile
}

function Initialize-MirroringEndpoint {
    <#
    .SYNOPSIS
    Prepares SQL Server for database mirroring

    .DESCRIPTION
    ToDo: Describe
    #>

    param(
        [parameter(Mandatory = $true)]
        [String]$EncryptionPassword,
        [parameter(Mandatory = $true)]
        [String]$WorkDir
    )

    $Folder = Get-Item $WorkDir

    $H = $Env:COMPUTERNAME -replace '[^A-Za-z0-9_]', ''
    
    $CreateMasteeKey = "USE master;
                        CREATE MASTER KEY ENCRYPTION BY PASSWORD = '$EncryptionPassword';
                        GO

                        CREATE CERTIFICATE ${H}_cert WITH SUBJECT = '$H certificate';
                        GO

                        CREATE ENDPOINT Endpoint_Mirroring 
                            STATE = STARTED
                            AS TCP (
                                LISTENER_PORT=7024
                                , LISTENER_IP = ALL
                            ) 
                            FOR DATABASE_MIRRORING ( 
                                AUTHENTICATION = CERTIFICATE ${H}_cert
                                , ENCRYPTION = REQUIRED ALGORITHM AES
                                , ROLE = ALL
                            );
                        GO

                        BACKUP CERTIFICATE ${H}_cert TO FILE = '$Folder\certificate.cer';
                        GO
                        "

    Invoke-SQLText -SQL $CreateMasteeKey
}

Export-ModuleMember -Function New-SQLServer
Export-ModuleMember -Function Remove-SQLServer
Export-ModuleMember -Function Invoke-SQLText
Export-ModuleMember -Function Initialize-MirroringEndpoint
