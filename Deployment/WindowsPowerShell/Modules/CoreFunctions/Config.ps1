<#
Naming convention:

== Normal variables
** Set: $NormalVar = 123
** Get: Write-Host $NormalVar

== Script-scope variables
** Set: $script:__ScriptScopeVar = 123
** Get: Write-Host $__ScriptScopeVar

== Global-scope variables
** Set: $global:__GlobalScopeVar__ = 123
** Get: Write-Host $__GlobalScopeVar__
#>

$script:__ModulePath = $PsScriptRoot
$script:__ModuleName = $PsScriptRoot.Split("\")[-1]
$script:__DefaultLogPath = [IO.Path]::Combine([IO.Path]::GetTempPath(), "PowerShell_$__ModuleName.log")


$script:__RequiredModules = @("ServerManager", "DnsClient")
$script:__ImportModulesExplicitely = $true
$script:__ImportModulesErrorAction = "Stop"


$global:__StopExecutionThrowsExeption__ = $true
$global:__StopExecutionExitsSession__ = $false

