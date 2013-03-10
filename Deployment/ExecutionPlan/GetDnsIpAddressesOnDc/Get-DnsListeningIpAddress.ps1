function Get-DnsListeningIpAddresses {
    Import-Module DnsServer
    (Get-DNSServer -ComputerName localhost).ServerSetting.ListeningIpAddress
}
