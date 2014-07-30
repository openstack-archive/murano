
trap {
    &$TrapHandler
}


Function Set-LocalUserPassword {
    param (
        [String] $UserName,
        [String] $Password,
        [Switch] $Force
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
        
        if ((Get-WmiObject Win32_UserAccount -Filter "LocalAccount = 'True' AND Name='$UserName'") -eq $null) {
            throw "Unable to find local user account '$UserName'"
        }
        
        if ($Force) {
            Write-Log "Changing password for user '$UserName' to '*****'" # :)
            $null = ([ADSI] "WinNT://./$UserName").SetPassword($Password)
        }
        else {
            Write-LogWarning "You are trying to change password for user '$UserName'. To do this please run the command again with -Force parameter."
        }
    }
}

