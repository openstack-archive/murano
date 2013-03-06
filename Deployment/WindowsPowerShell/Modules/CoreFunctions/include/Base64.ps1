
Function ConvertTo-Base64String {
<#
#>
    [CmdletBinding(DefaultParameterSetName="FromString")]
    param (
        [Parameter(Position=1,ParameterSetName="FromString")]
        [String] $String,
        
        [Parameter(ParameterSetName="FromFile")]
        [String] $Path,
        
        [Parameter(ParameterSetName="FromFile")]
        [Int] $ChunkSize = 5KB,

        [Parameter(ParameterSetName="FromFile")]
        [Switch] $OneChunk
    )
    switch($PSCmdlet.ParameterSetName) {
        "FromString" {
            [System.Text.Encoding]::UTF8.GetBytes($String)
            [System.Convert]::ToBase64String($Bytes)
        }
        "FromFile" {
            $FileStream = [IO.File]::Open($Path, [System.IO.FileMode]::Open)
            $BytesToRead = $FileStream.Length
            
            if ($OneChunk) {
                $ChunkSize = $BytesToRead
            }
            
            $Bytes = New-Object Byte[] $ChunkSize
            while ($BytesToRead -gt 0) {
                if ($BytesToRead -lt $ChunkSize) {
                    $ChunkSize = $BytesToRead
                    $Bytes = New-Object Byte[] $ChunkSize
                }
                #Write-Host ("BytesToRead: {0}, ChunkSize: {1}" -f $BytesToRead, $ChunkSize )
                $BytesRead = $FileStream.Read($Bytes, 0, $ChunkSize)
                $BytesToRead -= $BytesRead
                
                [System.Convert]::ToBase64String($Bytes)
            }
            $FileStream.Close()
        }
    }
}



Function ConvertFrom-Base64String {
<#
#>
    [CmdletBinding(DefaultParameterSetName="ToByteArray")]
    param (
        [Parameter(Position=1,ValueFromPipeline=$true)]
        [String] $Base64String,
        
        [Parameter(ParameterSetName="ToFile")]
        [String] $Path,
        
        [Parameter(ParameterSetName="ToString")]
        [Switch] $ToString
    )
    begin {
        switch($PSCmdlet.ParameterSetName) {
            "ToFile" {
                if ([IO.File]::Exists($Path)) {
                    [IO.File]::Delete($Path)
                }
                $FileStream = [IO.File]::Open($Path, [IO.FileMode]::Append)
            }
        }
    }
    process {
        foreach( $Line in ($Base64String -split '\n')) {
            $Bytes  = [System.Convert]::FromBase64String($Line)

            switch($PSCmdlet.ParameterSetName) {
                "ToFile" {
                    $FileStream.Write($Bytes, 0, $Bytes.Length)
                }
                "ToString" {
                    [System.Text.Encoding]::UTF8.GetString($Bytes)
                }
                "ToByteArray" {
                    $Bytes
                }
            }
        }
    }
    end {
        switch($PSCmdlet.ParameterSetName) {
            "ToFile" {
                $FileStream.Close()
            }
        }
    }
}
