
trap {
    &$TrapHandler
}


Function Install-RolePrimaryDomainController {
	param (
		[String] $DomainName,
		[String] $SafeModePassword
	)
    begin {
        Show-InvocationInfo $MyInvocation
    }
    end {
        Show-InvocationInfo $MyInvocation -End
    }
    process {
        trap {
            &$TrapHandler
        }

		Add-WindowsFeatureWrapper `
			-Name "DNS","AD-Domain-Services","RSAT-DFS-Mgmt-Con" `
			-IncludeManagementTools `
	        -NotifyRestart

		Write-Log "Creating first domain controller ..."
			
		$SMAP = ConvertTo-SecureString -String $SafeModePassword -AsPlainText -Force
			
		$null = Install-ADDSForest `
			-DomainName $DomainName `
			-SafeModeAdministratorPassword $SMAP `
			-DomainMode Default `
			-ForestMode Default `
			-NoRebootOnCompletion `
			-Force

		Write-Log "Waiting 60 seconds for reboot ..."
		Start-Sleep -Seconds 60
	}
}
