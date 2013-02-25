
Function Install-RolePrimaryDomainController
{
<#
.SYNOPSIS
Configure node's network adapters.
Create first domain controller in the forest.

.EXAMPLE
PS> Install-RolePrimaryDomainController -DomainName acme.local -SafeModePassword "P@ssw0rd"

Install DNS and ADDS, create forest and domain 'acme.local'.
Set DC recovery mode password to 'P@ssw0rd'.
#>
	
	param
	(
		[String]
		# New domain name.
		$DomainName,
		
		[String]
		# Domain controller recovery mode password.
		$SafeModePassword
	)

	trap { Stop-Execution $_ }

        # Add required windows features
	Add-WindowsFeatureWrapper `
		-Name "DNS","AD-Domain-Services","RSAT-DFS-Mgmt-Con" `
		-IncludeManagementTools `
        -NotifyRestart


	Write-Log "Creating first domain controller ..."
		
	$SMAP = ConvertTo-SecureString -String $SafeModePassword -AsPlainText -Force
		
	Install-ADDSForest `
		-DomainName $DomainName `
		-SafeModeAdministratorPassword $SMAP `
		-DomainMode Default `
		-ForestMode Default `
		-NoRebootOnCompletion `
		-Force `
		-ErrorAction Stop | Out-Null

	Write-Log "Waiting for reboot ..."		
#	Stop-Execution -ExitCode 3010 -ExitString "Computer must be restarted to finish domain controller promotion."
#	Write-Log "Restaring computer ..."
#	Restart-Computer -Force
}
