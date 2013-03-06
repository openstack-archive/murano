[Void] [System.Reflection.Assembly]::LoadFrom("$__ModulePath\Ionic.Zip.dll")


Function Compress-Folder {
<#
#>
    [CmdLetBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [String] $Path,

        [String] $ZipFile = "",
        
        [Switch] $TempFile,
        
        [Switch] $ContentOnly
    )
    
    if (-not [IO.Directory]::Exists($Path)) {
        Write-LogError "Directory '$Path' not found."
        return
    }
    
    if ($TempFile) {
        $ZipFile = [IO.Path]::GetTempFileName()
    }
    
    if ($ZipFile -eq "") {
        $ZipFile = "$Path.zip"
    }
    
    if ([IO.File]::Exists($ZipFile)) {
        [IO.File]::Delete($ZipFile)
    }

    $zip = New-Object Ionic.Zip.ZipFile
    if ($ContentOnly) {
        [Void] $zip.AddDirectory($Path)
    }
    else {
        [Void] $zip.AddDirectory($Path, (Split-Path -Path $Path -Leaf))
    }
    $zip.Save($ZipFile)
    $zip.Dispose()
    
    return $ZipFile
}


Function Expand-Zip {
<#
#>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [String] $Path,

        [String] $Destination
    )
    
    if (-not [IO.File]::Exists($Path)) {
        Write-LogError "File not found '$Path'"
        return
    }
    
    $zip = [Ionic.Zip.ZipFile]::Read($Path)
    $zip.ExtractAll($Destination, [Ionic.Zip.ExtractExistingFileAction]::OverwriteSilently)
    $zip.Dispose()
}
