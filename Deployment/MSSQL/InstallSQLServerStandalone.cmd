@echo off
cd %~dp0
powershell.exe -ExecutionPolicy Unrestricted .\InstallSQLServerStandalone.ps1 %*
