@echo off
chcp 866 > nul
if not exist log mkdir log
cd C:\1C_Base\repository\FITOLAN2012
.\gcomp_bin_2.2.15\Release\gcomp.exe -vv  -d  -F .\1CV7.md -D .\conf > .\log\decompile.log 2>&1
type .\log\decompile.log
del .\1CV7.md
git add .
git commit
.\gcomp_bin_2.2.15\Release\gcomp.exe -vv  -c -F .\MD_compile\1Cv7.MD  -DD .\conf > .\log\compile.log 2>&1
type .\log\compile.log
git push
