@echo off
REM Simple AVL test script
echo Running AVL with uav.avl geometry...
echo.

cd avl_files

REM Create command file for AVL
echo LOAD > avl_commands.txt
echo uav.avl >> avl_commands.txt
echo MASS >> avl_commands.txt
echo uav.mass >> avl_commands.txt
echo OPER >> avl_commands.txt
echo A >> avl_commands.txt
echo A 2.0 >> avl_commands.txt
echo  >> avl_commands.txt
echo M >> avl_commands.txt
echo M 0.25 >> avl_commands.txt
echo  >> avl_commands.txt
echo X >> avl_commands.txt
echo  >> avl_commands.txt
echo QUIT >> avl_commands.txt

REM Run AVL
"C:\Users\bradrothenberg\OneDrive - nTop\Sync\AVL\avl.exe" < avl_commands.txt

echo.
echo AVL run complete.
echo Check avl_files directory for output.
pause
