# Import config first
. "$PsScriptRoot\Config.ps1"

# Import functions from 'Include' subfolder
Get-ChildItem "$PsScriptRoot\Include" -Filter "*.ps1" |
    ForEach-Object {
        . "$($_.FullName)"
    }

trap { Stop-Execution $_ }

Export-ModuleMember -Function * -Alias *

<#
if ($__ImportModulesExplicitely) {
    foreach ($Module in $__RequiredModules) {
        Write-Log "Importing module '$Module' ..."
        Import-Module -Name "$Module" -ErrorAction "$__ImportModulesErrorAction"
    }
}
#>

Write-Log "Module loaded from '$PsScriptRoot'"

#-------------------------------------------------------------------------------

switch ($Args[0]) {
    'installTo' {
        Install-Module -InstallPath $args[1] -ModulePath $PsScriptRoot
    }
    'register' {
        Register-Module "$PsScriptRoot"
    }
    default {
    }
}
