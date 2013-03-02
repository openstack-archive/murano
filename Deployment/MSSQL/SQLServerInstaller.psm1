Import-Module '.\OptionParser.psm1'

#RVER /SQLSVCACCOUNT="<DomainName\UserName>" /SQLSVCPASSWORD="<StrongPassword>"
# /SQLSYSADMINACCOUNTS="<DomainName\UserName>" /AGTSVCACCOUNT="NT AUTHORITY\Network Service" /IACCEPTSQLSERVERLICENSETERMS

function New-OptionParserInstall {
    <#
    .SYNOPSIS
    Creates an option parser for MS SQL Server 2012 setup "INSTALL" action.

    .DESCRIPTION
    Use this cmdlet to create an option parser for MS SQL Server 2012 setup "INSTALL" action.
    All documented option are supported. See the following link for details:
    http://msdn.microsoft.com/en-us/library/ms144259.aspx
    #>
    $OptionParserInstall = New-OptionParser

    $OptionParserInstall.AddOption((New-Option "ACTION" -String -Constraints "INSTALL"), $true, "INSTALL")
    $OptionParserInstall.AddOption((New-Option "IACCEPTSQLSERVERLICENSETERMS" -Switch), $true)
    $OptionParserInstall.AddOption((New-Option "ENU" -Switch))
    $OptionParserInstall.AddOption((New-Option "UpdateEnabled" -Switch))
    $OptionParserInstall.AddOption((New-Option "UpdateSource" -String))
    $OptionParserInstall.AddOption((New-Option "CONFIGURATIONFILE" -String))
    $OptionParserInstall.AddOption((New-Option "ERRORREPORTING" -Boolean))
    $OptionParserInstall.AddOption((New-Option "FEATURES" -List -Constraints ("SQL","SQLEngine","Replication","FullText","DQ","AS","RS","DQC","IS","MDS","Tools","BC","BOL","BIDS","Conn","SSMS","ADV_SSMS","DREPLAY_CTLR","DREPLAY_CLT","SNAC_SDK","SDK","LocalDB")))
    $OptionParserInstall.AddOption((New-Option "ROLE" -String -Constraints ("SPI_AS_ExistingFarm", "SPI_AS_NewFarm", "AllFeatures_WithDefaults")))
    $OptionParserInstall.AddOption((New-Option "INDICATEPROGRESS" -Switch))
    $OptionParserInstall.AddOption((New-Option "INSTALLSHAREDDIR" -String))
    $OptionParserInstall.AddOption((New-Option "INSTALLSHAREDWOWDIR" -String))
    $OptionParserInstall.AddOption((New-Option "INSTANCEDIR" -String))
    $OptionParserInstall.AddOption((New-Option "INSTANCEID" -String))
    $OptionParserInstall.AddOption((New-Option "INSTANCENAME" -String), $true, "MSSQLSERVER")
    $OptionParserInstall.AddOption((New-Option "PID" -String))
    $OptionParserInstall.AddOption((New-Option "Q" -Switch))
    $OptionParserInstall.AddOption((New-Option "QS" -Switch))
    $OptionParserInstall.AddOption((New-Option "UIMODE" -String -Constraints ("Normal", "AutoAdvance")))
    $OptionParserInstall.AddOption((New-Option "SQMREPORTING" -Boolean))
    $OptionParserInstall.AddOption((New-Option "HIDECONSOLE" -Switch))
    $OptionParserInstall.AddOption((New-Option "AGTSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParserInstall.AddOption((New-Option "AGTSVCPASSWORD" -String))
    $OptionParserInstall.AddOption((New-Option "AGTSVCSTARTUPTYPE" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParserInstall.AddOption((New-Option "ASBACKUPDIR" -String))
    $OptionParserInstall.AddOption((New-Option "ASCOLLATION" -String))
    $OptionParserInstall.AddOption((New-Option "ASCONFIGDIR" -String))
    $OptionParserInstall.AddOption((New-Option "ASDATADIR" -String))
    $OptionParserInstall.AddOption((New-Option "ASLOGDIR" -String))
    $OptionParserInstall.AddOption((New-Option "ASSERVERMODE" -String -Constraints ("MULTIDIMENSIONAL", "POWERPIVOT", "TABULAR")))
    $OptionParserInstall.AddOption((New-Option "ASSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParserInstall.AddOption((New-Option "ASSVCPASSWORD" -String))
    $OptionParserInstall.AddOption((New-Option "ASSVCSTARTUPTYPE" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParserInstall.AddOption((New-Option "ASSYSADMINACCOUNTS" -String), $true, "$ENV:USERDOMAIN\$ENV:USERNAME")
    $OptionParserInstall.AddOption((New-Option "ASTEMPDIR" -String))
    $OptionParserInstall.AddOption((New-Option "ASPROVIDERMSOLAP" -Boolean))
    $OptionParserInstall.AddOption((New-Option "FARMACCOUNT" -String))
    $OptionParserInstall.AddOption((New-Option "FARMPASSWORD" -String))
    $OptionParserInstall.AddOption((New-Option "PASSPHRASE" -String))
    $OptionParserInstall.AddOption((New-Option "FARMADMINIPORT" -String))
    $OptionParserInstall.AddOption((New-Option "BROWSERSVCSTARTUPTYPE" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParserInstall.AddOption((New-Option "ENABLERANU" -Switch))
    $OptionParserInstall.AddOption((New-Option "INSTALLSQLDATADIR" -String))
    $OptionParserInstall.AddOption((New-Option "SAPWD" -String))
    $OptionParserInstall.AddOption((New-Option "SECURITYMODE" -String -Constrainrs ("SQL")))
    $OptionParserInstall.AddOption((New-Option "SQLBACKUPDIR" -String))
    $OptionParserInstall.AddOption((New-Option "SQLCOLLATION" -String))
    $OptionParserInstall.AddOption((New-Option "ADDCURRENTUSERASSQLADMIN" -Switch))
    $OptionParserInstall.AddOption((New-Option "SQLSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParserInstall.AddOption((New-Option "SQLSVCPASSWORD" -String))
    $OptionParserInstall.AddOption((New-Option "SQLSVCSTARTUPTYPE" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParserInstall.AddOption((New-Option "SQLSYSADMINACCOUNTS" -String), $true, "$ENV:USERDOMAIN\$ENV:USERNAME")
    $OptionParserInstall.AddOption((New-Option "SQLTEMPDBDIR" -String))
    $OptionParserInstall.AddOption((New-Option "SQLTEMPDBLOGDIR" -String))
    $OptionParserInstall.AddOption((New-Option "SQLUSERDBDIR" -String))
    $OptionParserInstall.AddOption((New-Option "SQLUSERDBLOGDIR" -String))
    $OptionParserInstall.AddOption((New-Option "FILESTREAMLEVEL" -String -Constraints ("0", "1", "2", "3")))
    $OptionParserInstall.AddOption((New-Option "FILESTREAMSHARENAME" -String))
    $OptionParserInstall.AddOption((New-Option "FTSVCACCOUNT" -String))
    $OptionParserInstall.AddOption((New-Option "FTSVCPASSWORD" -String))
    $OptionParserInstall.AddOption((New-Option "ISSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParserInstall.AddOption((New-Option "ISSVCPASSWORD" -String))
    $OptionParserInstall.AddOption((New-Option "ISSVCStartupType" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParserInstall.AddOption((New-Option "NPENABLED" -Boolean))
    $OptionParserInstall.AddOption((New-Option "TCPENABLED" -Boolean))
    $OptionParserInstall.AddOption((New-Option "RSINSTALLMODE" -String -Constraints ("SharePointFilesOnlyMode", "DefaultNativeMode", "FilesOnlyMode")))
    $OptionParserInstall.AddOption((New-Option "RSSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParserInstall.AddOption((New-Option "RSSVCPASSWORD" -String))
    $OptionParserInstall.AddOption((New-Option "RSSVCStartupType" -String -Constraints ("Manual", "Automatic", "Disabled")))

    return $OptionParserInstall
}

function New-OptionParserPrepareImage {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserCompleteImage {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserUpgrade {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserEditionUpgrade {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserRepair {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserRebuilddatabase {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserUninstall {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserInstallFailoverCluster {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserPrepareFailoverCluster {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserCompleteFailoverCluster {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserUpgrade {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserAddNode {
    # ToDo: Implement
    throw "Not yet implemented"
}

function New-OptionParserRemoveNode {
    # ToDo: Implement
    throw "Not yet implemented"
}

Export-ModuleMember -Function New-OptionParserInstall
Export-ModuleMember -Function New-OptionParserPrepareImage
Export-ModuleMember -Function New-OptionParserCompleteImage
Export-ModuleMember -Function New-OptionParserUpgrade
Export-ModuleMember -Function New-OptionParserEditionUpgrade
Export-ModuleMember -Function New-OptionParserRepair
Export-ModuleMember -Function New-OptionParserRebuilddatabase
Export-ModuleMember -Function New-OptionParserUninstall
Export-ModuleMember -Function New-OptionParserInstallFailoverCluster
Export-ModuleMember -Function New-OptionParserPrepareFailoverCluster
Export-ModuleMember -Function New-OptionParserCompleteFailoverCluster
Export-ModuleMember -Function New-OptionParserUpgrade
Export-ModuleMember -Function New-OptionParserAddNode
Export-ModuleMember -Function New-OptionParserRemoveNode
