param(
    [parameter(Mandatory = $true)]
    [string]$Mode,
    [parameter(Mandatory = $true)]
    [string]$SetupRoot
)

$ErrorActionPreference = 'Stop'

Import-Module '.\SQLServerInstaller.psm1'

$SupportedModes = @('STANDALONE')

if (-not ($SupportedModes -contains $Mode)) {
    throw "Installation mode '$Mode' is not supported. Supported modes are: $($SupportedModes -join ', ')"
}

$SetupDir = Get-Item $SetupRoot
$SetupExe = $SetupDir.GetFiles("setup.exe")[0]

$parser = New-OptionParserInstall

if ($Mode -eq 'STANDALONE') {
    $parser.ExecuteBinary($SetupExe.FullName, @{"QS" = $null})
}

