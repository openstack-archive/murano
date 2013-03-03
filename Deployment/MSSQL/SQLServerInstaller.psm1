Import-Module '.\OptionParser.psm1'
Import-Module '.\SQLServerOptionParsers.psm1'

function New-SQLServer {
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
Export-ModuleMember -Function New-SQLServer
Export-ModuleMember -Function Remove-SQLServer
