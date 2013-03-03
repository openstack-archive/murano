Import-Module '.\OptionParser.psm1'

function New-OptionParserInstall {
    <#
    .SYNOPSIS
    Creates an option parser for MS SQL Server 2012 setup "INSTALL" action.

    .DESCRIPTION
    Use this cmdlet to create an option parser for MS SQL Server 2012 setup "INSTALL" action.
    All documented option are supported. See the following link for details:
    http://msdn.microsoft.com/en-us/library/ms144259.aspx
    #>
    $OptionParser = New-OptionParser

    $OptionParser.AddOption((New-Option "ACTION" -String -Constraints "INSTALL"), $true, "INSTALL")
    $OptionParser.AddOption((New-Option "IACCEPTSQLSERVERLICENSETERMS" -Switch), $true)
    $OptionParser.AddOption((New-Option "ENU" -Switch))
    $OptionParser.AddOption((New-Option "UpdateEnabled" -Switch))
    $OptionParser.AddOption((New-Option "UpdateSource" -String))
    $OptionParser.AddOption((New-Option "CONFIGURATIONFILE" -String))
    $OptionParser.AddOption((New-Option "ERRORREPORTING" -Boolean))
    $OptionParser.AddOption((New-Option "FEATURES" -List -Constraints ("SQL","SQLEngine","Replication","FullText","DQ","AS","RS","DQC","IS","MDS","Tools","BC","BOL","BIDS","Conn","SSMS","ADV_SSMS","DREPLAY_CTLR","DREPLAY_CLT","SNAC_SDK","SDK","LocalDB")))
    $OptionParser.AddOption((New-Option "ROLE" -String -Constraints ("SPI_AS_ExistingFarm", "SPI_AS_NewFarm", "AllFeatures_WithDefaults")))
    $OptionParser.AddOption((New-Option "INDICATEPROGRESS" -Switch))
    $OptionParser.AddOption((New-Option "INSTALLSHAREDDIR" -String))
    $OptionParser.AddOption((New-Option "INSTALLSHAREDWOWDIR" -String))
    $OptionParser.AddOption((New-Option "INSTANCEDIR" -String))
    $OptionParser.AddOption((New-Option "INSTANCEID" -String))
    $OptionParser.AddOption((New-Option "INSTANCENAME" -String), $true, "MSSQLSERVER")
    $OptionParser.AddOption((New-Option "PID" -String))
    $OptionParser.AddOption((New-Option "Q" -Switch))
    $OptionParser.AddOption((New-Option "QS" -Switch))
    $OptionParser.AddOption((New-Option "UIMODE" -String -Constraints ("Normal", "AutoAdvance")))
    $OptionParser.AddOption((New-Option "SQMREPORTING" -Boolean))
    $OptionParser.AddOption((New-Option "HIDECONSOLE" -Switch))
    $OptionParser.AddOption((New-Option "AGTSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParser.AddOption((New-Option "AGTSVCPASSWORD" -String))
    $OptionParser.AddOption((New-Option "AGTSVCSTARTUPTYPE" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParser.AddOption((New-Option "ASBACKUPDIR" -String))
    $OptionParser.AddOption((New-Option "ASCOLLATION" -String))
    $OptionParser.AddOption((New-Option "ASCONFIGDIR" -String))
    $OptionParser.AddOption((New-Option "ASDATADIR" -String))
    $OptionParser.AddOption((New-Option "ASLOGDIR" -String))
    $OptionParser.AddOption((New-Option "ASSERVERMODE" -String -Constraints ("MULTIDIMENSIONAL", "POWERPIVOT", "TABULAR")))
    $OptionParser.AddOption((New-Option "ASSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParser.AddOption((New-Option "ASSVCPASSWORD" -String))
    $OptionParser.AddOption((New-Option "ASSVCSTARTUPTYPE" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParser.AddOption((New-Option "ASSYSADMINACCOUNTS" -String), $true, "$ENV:USERDOMAIN\$ENV:USERNAME")
    $OptionParser.AddOption((New-Option "ASTEMPDIR" -String))
    $OptionParser.AddOption((New-Option "ASPROVIDERMSOLAP" -Boolean))
    $OptionParser.AddOption((New-Option "FARMACCOUNT" -String))
    $OptionParser.AddOption((New-Option "FARMPASSWORD" -String))
    $OptionParser.AddOption((New-Option "PASSPHRASE" -String))
    $OptionParser.AddOption((New-Option "FARMADMINIPORT" -String))
    $OptionParser.AddOption((New-Option "BROWSERSVCSTARTUPTYPE" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParser.AddOption((New-Option "ENABLERANU" -Switch))
    $OptionParser.AddOption((New-Option "INSTALLSQLDATADIR" -String))
    $OptionParser.AddOption((New-Option "SAPWD" -String))
    $OptionParser.AddOption((New-Option "SECURITYMODE" -String -Constrainrs ("SQL")))
    $OptionParser.AddOption((New-Option "SQLBACKUPDIR" -String))
    $OptionParser.AddOption((New-Option "SQLCOLLATION" -String))
    $OptionParser.AddOption((New-Option "ADDCURRENTUSERASSQLADMIN" -Switch))
    $OptionParser.AddOption((New-Option "SQLSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParser.AddOption((New-Option "SQLSVCPASSWORD" -String))
    $OptionParser.AddOption((New-Option "SQLSVCSTARTUPTYPE" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParser.AddOption((New-Option "SQLSYSADMINACCOUNTS" -String), $true, "$ENV:USERDOMAIN\$ENV:USERNAME")
    $OptionParser.AddOption((New-Option "SQLTEMPDBDIR" -String))
    $OptionParser.AddOption((New-Option "SQLTEMPDBLOGDIR" -String))
    $OptionParser.AddOption((New-Option "SQLUSERDBDIR" -String))
    $OptionParser.AddOption((New-Option "SQLUSERDBLOGDIR" -String))
    $OptionParser.AddOption((New-Option "FILESTREAMLEVEL" -String -Constraints ("0", "1", "2", "3")))
    $OptionParser.AddOption((New-Option "FILESTREAMSHARENAME" -String))
    $OptionParser.AddOption((New-Option "FTSVCACCOUNT" -String))
    $OptionParser.AddOption((New-Option "FTSVCPASSWORD" -String))
    $OptionParser.AddOption((New-Option "ISSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParser.AddOption((New-Option "ISSVCPASSWORD" -String))
    $OptionParser.AddOption((New-Option "ISSVCStartupType" -String -Constraints ("Manual", "Automatic", "Disabled")))
    $OptionParser.AddOption((New-Option "NPENABLED" -Boolean))
    $OptionParser.AddOption((New-Option "TCPENABLED" -Boolean))
    $OptionParser.AddOption((New-Option "RSINSTALLMODE" -String -Constraints ("SharePointFilesOnlyMode", "DefaultNativeMode", "FilesOnlyMode")))
    $OptionParser.AddOption((New-Option "RSSVCACCOUNT" -String), $true, "NT AUTHORITY\Network Service")
    $OptionParser.AddOption((New-Option "RSSVCPASSWORD" -String))
    $OptionParser.AddOption((New-Option "RSSVCStartupType" -String -Constraints ("Manual", "Automatic", "Disabled")))

    return $OptionParser
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
    <#
    .SYNOPSIS
    Creates an option parser for MS SQL Server 2012 setup "INSTALL" action.

    .DESCRIPTION
    Use this cmdlet to create an option parser for MS SQL Server 2012 setup "INSTALL" action.
    All documented option are supported. See the following link for details:
    http://msdn.microsoft.com/en-us/library/ms144259.aspx
    #>
    $OptionParser = New-OptionParser

    $OptionParser.AddOption((New-Option "ACTION" -String -Constraints "UNINSTALL"), $true, "UNINSTALL")
    $OptionParser.AddOption((New-Option "CONFIGURATIONFILE" -String))
    $OptionParser.AddOption((New-Option "FEATURES" -List -Constraints ("SQL","SQLEngine","Replication","FullText","DQ","AS","RS","DQC","IS","MDS","Tools","BC","BOL","BIDS","Conn","SSMS","ADV_SSMS","DREPLAY_CTLR","DREPLAY_CLT","SNAC_SDK","SDK","LocalDB")), $true)
    $OptionParser.AddOption((New-Option "INDICATEPROGRESS" -Switch))
    $OptionParser.AddOption((New-Option "INSTANCENAME" -String), $true, "MSSQLSERVER")
    $OptionParser.AddOption((New-Option "Q" -Switch))
    $OptionParser.AddOption((New-Option "HIDECONSOLE" -Switch))

    return $OptionParser
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
