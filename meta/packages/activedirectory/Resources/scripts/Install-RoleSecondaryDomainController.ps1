
trap {
    &$TrapHandler
}


Function Install-RoleSecondaryDomainController
{
<#
.SYNOPSIS
Install additional (secondary) domain controller.

#>
	param
	(
		[String]
		# Domain name to join to.
		$DomainName,
		
		[String]
		# Domain user who is allowed to join computer to domain.
		$UserName,
		
		[String]
		# User's password.
		$Password,
		
		[String]
		# Domain controller recovery mode password.
		$SafeModePassword
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
	
		$Credential = New-Credential -UserName "$DomainName\$UserName" -Password $Password
			
		# Add required windows features
		Add-WindowsFeatureWrapper `
			-Name "DNS","AD-Domain-Services","RSAT-DFS-Mgmt-Con" `
			-IncludeManagementTools `
	                -NotifyRestart
			
		
	    Write-Log "Adding secondary domain controller ..."
	    
		$SMAP = ConvertTo-SecureString -String $SafeModePassword -AsPlainText -Force

		Install-ADDSDomainController `
			-DomainName $DomainName `
			-SafeModeAdministratorPassword $SMAP `
			-Credential $Credential `
			-NoRebootOnCompletion `
			-Force `
			-ErrorAction Stop | Out-Null

		Write-Log "Waiting for restart ..."
	#	Stop-Execution -ExitCode 3010 -ExitString "Computer must be restarted to finish domain controller promotion."
	#	Write-Log "Restarting computer ..."
	#	Restart-Computer -Force
	}
}
