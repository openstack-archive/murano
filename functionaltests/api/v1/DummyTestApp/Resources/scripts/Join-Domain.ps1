
trap {
    &$TrapHandler
}


Function Join-Domain {
<#
.SYNOPSIS
Executes "Join domain" action.

Requires 'CoreFunctions' module
#>
	param (
		[String] $DomainName = '',
		[String] $UserName = '',
		[String] $Password = '',
		[String] $OUPath = '',
        [Switch] $AllowRestart
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
	
    	if ($UserName -eq '') {
    		$UserName = 'Administrator'
    	}

    	$Credential = New-Credential -UserName "$DomainName\$UserName" -Password $Password


    	if (Test-ComputerName -DomainName $DomainName -ErrorAction 'SilentlyContinue') {
            Write-LogWarning "Computer already joined to domain '$DomainName'"
    	}
    	else {
    		Write-Log "Joining computer to domain '$DomainName' ..."
    		
    		if ($OUPath -eq '') {
    			Add-Computer -DomainName $DomainName -Credential $Credential -Force
    		}
    		else {
    			Add-Computer -DomainName $DomainName -Credential $Credential -OUPath $OUPath -Force
    		}

            $null = Exec 'ipconfig' @('/registerdns') -RedirectStreams

            Write-Log "Waiting 30 seconds to restart ..."
            Start-Sleep -Seconds 30
    		<#
            if ($AllowRestart) {
                Write-Log "Restarting computer ..."
                Restart-Computer -Force
            }
            else {
                Write-Log "Please restart the computer now."
            }
            #>
    	}
    }
}
