function New-Option ([string]$Name, [switch]$Switch, [switch]$Boolean, [switch]$String, [switch]$List, $Constraints=$null) {
    <#
    .SYNOPSIS
    Creates Option object

    .DESCRIPTION
    Option object is a virtual object represtnting typed command line option. These objects encapsulate escaping and
    validation matters.

    One and only one of the switches 'Name', 'Switch', 'Boolean', 'String' or 'List' should be provided.

    .PARAMETER Name
    Option name as it appears in the command line.

    .PARAMETER Switch
    Use this switch to create valueless option (a switch).

    .PARAMETER Boolean
    Use this switch to create boolean option. Its value is always converted to "1" or "0"

    .PARAMETER String
    Use this switch to create string option. Its value will be properly quoted if necessary.

    .PARAMETER List
    Use this switch to create option with list value. Values will be put into command line using valid value delemiter (a comma)

    .PARAMETER Constraints
    When this parameter is specified, option values are limited to options from that list.

    #>

    $Option = New-Object -TypeName PSObject

    # Fields
    $Option | Add-Member NoteProperty Type -value $null
    $Option | Add-Member NoteProperty Name -value $null
    $Option | Add-Member NoteProperty AllowedValues -value $null

    # Init

    $Option | Add-Member ScriptMethod __init__ {
        param([string]$Name, $Switch, $Boolean, $String, $List)

        $this.Name = $Name
                       
        # With respect for our developers we do not check for double type selected
        if ($Switch) {
            AugmentOptionSwitch($this)
        } elseif ($Boolean) {
            AugmentOptionBoolean($this)
        } elseif ($String) {
            AugmentOptionString($this)
        } elseif ($List) {
            AugmentOptionList($this)
        } else {
            throw "Switch, Boolean, String or List option type must be provided for option '$Name'"
        }
    }

    $Option | Add-Member ScriptMethod __post_init__ {
        param($Constraints=$null)
        if ($Constraints -ne $null) {
            $this.AllowedValues = @()
            $this.AllowedValues = $this.AllowedValues + $Constraints
        } else {
            $Constraints = $null
        }
    }

    # Methods

    $Option | Add-Member -Force ScriptMethod Validate {
        if ($this.AllowedValues -ne $null) {
            if (-not($this.AllowedValues -contains $this.Value)) {
                $Cts = $this.AllowedValues -join ','
                throw "Option '$($this.Name)' may have values ($Cts) but not '$($this.Value)'"
            }
        }
    }

    $Option | Add-Member -Force ScriptMethod ToString {
        return "/$($this.Name)"
    }

    # invoke constructor

    $Option.__init__($Name, $Switch, $Boolean, $String, $List)
    $Option.__post_init__($Constraints)

    return $Option
}

function AugmentOptionSwitch($Option) {
}

function AugmentOptionBoolean($Option) {
    # Fields
    $Option | Add-Member NoteProperty Value -value $false

    # Methods

    $Option | Add-Member -Force ScriptMethod ToString {
        if ($this.Value) {
            return "/$($this.Name)=1"
        } else {
            return "/$($this.Name)=0"
        }
    }
}

function AugmentOptionString($Option) {
    # Fields
    $Option | Add-Member NoteProperty Value -value ""

    # Methods

    $Option | Add-Member -Force ScriptMethod ToString {
        $v = "$($this.Value)"
        if ($v -match '.* .*') {
            # TODO: Escape double quote characters if possible
            return "/$($this.Name)=`"$v`""
        } else {
            return "/$($this.Name)=$v"
        }
    }
}

function AugmentOptionList($Option) {
    # Fields
    $Option | Add-Member NoteProperty Value -value @()

    # Methods

    $Option | Add-Member -Force ScriptMethod Validate {
        if ($this.AllowedValues -ne $null) {
            foreach ($V in $this.Value) {
                if (-not($this.AllowedValues -contains $V)) {
                    $Cts = $this.AllowedValues -join ','
                    throw "Option '$($this.Name)' may have values ($Cts) but not '$V'"
                }
            }
        }
    }

    $Option | Add-Member -Force ScriptMethod ToString {
        return "/$($this.Name)=$($this.Value -join ',')"
    }
}

function New-OptionParser() {
    <#
    .SYNOPSIS
    Creates OptionParser object.

    .DESCRIPTION
    OptionParser object leverages Option objects capabilities and builds valid command line using specified options.
    An application may also be invoked with OptionParser.

    #>

    $OptionParser = New-Object -TypeName PSObject

    # Fields
    $OptionParser | Add-Member NoteProperty Options -value @{}
    $OptionParser | Add-Member NoteProperty Defaults -value @{}
    $OptionParser | Add-Member NoteProperty RequiredOptions -value @()

    # Methods

    $OptionParser | Add-Member ScriptMethod AddOption {
        <#
        .SYNOPSIS
        Adds supported option into OptionParser.
        
        .DESCRIPTION
        OptionParser does not allow using unrecognized options. Use this method to fill OptionParser with recognized options

        .PARAMETER Option
        Option object

        .PARAMETER Required
        Required option switch

        .PARAMETER Default
        Option default value
        #>
        param($Option, [bool]$Required=$false, $Default=$null)
        $this.Options.Add($Option.Name, $Option)
        if ($Required) {
            $this.RequiredOptions = $this.RequiredOptions + $Option.Name
            if ($Option | Get-Member "Value") {
                if ($Default) {
                    $this.Defaults.Add($Option.Name, $Default)
                }
            } else {
                $this.Defaults.Add($Option.Name, $null)
            }
        }
    }

    $OptionParser | Add-Member ScriptMethod Parse {
        <#
        .SYNOPSIS
        Parses supplied options and returns command line parameters array.
        
        .DESCRIPTION
        This method verifies that only supported options are provided, all mandatory options are in place, 
        all option meet constraints if any. Unspecified options with default values are added to command line.
        So, mandatory option with default value never causes exception.

        .PARAMETER Options
        A hash map of options to parse. Option names should be mapped to corresponding values.
        #>
        param([hashtable]$Options)

        $CommandLine = @()
        foreach ($RequiredOptionName in $this.RequiredOptions) {
            if (-not $Options.ContainsKey($RequiredOptionName)) {
                $Default = $this.Defaults.Get_Item($RequiredOptionName)
                if ($this.Defaults.ContainsKey($RequiredOptionName)) {
                    $Options.Add($RequiredOptionName, $this.Defaults.Get_Item($RequiredOptionName))
                } else {
                    throw "Required option '$RequiredOptionName' is missing"
                }
            }
        }

        foreach ($OptionName in $($Options.keys)) {
            $Option = $this.Options.Get_Item($OptionName)
            if ($Option -eq $null) {
                throw "Option '$OptionName' is not allowed"
            }
            if ($Option | Get-Member "Value") {
                $Option.Value = $Options.Get_Item($OptionName)
            }
            $Option.Validate()
            $CommandLine = $CommandLine + $Option.ToString()
        }
        return $CommandLine
    }

    $OptionParser | Add-Member ScriptMethod ExecuteBinary {
        param($Binary, [hashtable]$Options = @{}, $CommandLineSuffix = @())
        <#
        .SYNOPSIS
        Executes binary with a command line constructed from provided options. An arbitrary suffix may be 
        appended to the command line.
        
        .DESCRIPTION
        This method uses OptionParser.Parse method to construct command line. If there a command line suffix 
        was supplied, it is appended to the end of command line. Normally command line suffix should contain
        leading space character.

        Method waits for executable process to complete and returns its exit code.

        .PARAMETER Binary
        Full or relative path to the executable to run.

        .PARAMETER Options
        A hash map of options to pass to the executable.

        .PARAMETER CommandLineSuffix
        Arbitrary command line suffix. Normally it shoud have leading space character.
        #>

        $Binary = Get-Item $Binary
        $CommandLine = $this.Parse($Options)
        if ($CommandLineSuffix) {
            $CommandLine = $CommandLine + $CommandLineSuffix
        }

        Write-Host "Executing: $($Binary.FullName) $($CommandLine -join ' ')"
        $process = [System.Diagnostics.Process]::Start($Binary, $CommandLine)
        $process.WaitForExit()
        $process.Refresh()
        return $process.ExitCode
    }

    return $OptionParser
}

Export-ModuleMember -Function New-OptionParser
Export-ModuleMember -Function New-Option