function Install-WebServer {
    Import-Module ServerManager
    Install-WindowsFeature Web-Server -IncludeManagementTools
}
