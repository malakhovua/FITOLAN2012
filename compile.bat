@echo off
chcp 866 > nul
if not exist log mkdir log
.\gcomp_bin_2.2.15\Release\gcomp.exe -vv  -c -F .\MD_compile\1Cv7.MD  -DD .\conf > .\log\compile.log 2>&1
type .\log\compile.log
