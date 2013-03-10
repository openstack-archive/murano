function Get-DnsListeningIpAddresses {
    (Get-DNSServer -ComputerName localhost).ServerSetting.ListeningIpAddress
}
