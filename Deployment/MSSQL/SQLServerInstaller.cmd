@echo off
cd %~dp0
powershell.exe -ExecutionPolicy Unrestricted .\SQLServerInstaller.ps1 %*
