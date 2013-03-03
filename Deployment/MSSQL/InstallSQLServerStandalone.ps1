param(
    [parameter(Mandatory = $true)]
    [string]$SetupRoot
)

Import-Module '.\SQLServerInstaller.psm1'

$ErrorActionPreference = 'Stop'

New-SQLServer $SetupRoot
