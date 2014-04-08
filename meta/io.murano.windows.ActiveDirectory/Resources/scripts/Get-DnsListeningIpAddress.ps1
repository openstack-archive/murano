
function Get-DnsListeningIpAddress {
    Import-Module DnsServer

    (Get-DNSServer -ComputerName localhost).ServerSetting.ListeningIpAddress |
        Where-Object { $_ -match "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}" }
}
