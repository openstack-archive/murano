function Get-DnsListeningIpAddress {
    Import-Module DnsServer
    (Get-DNSServer -ComputerName localhost).ServerSetting.ListeningIpAddress
}
