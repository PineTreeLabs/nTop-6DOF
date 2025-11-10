@echo off
REM Quick AVL test - just load geometry and execute analysis
echo Testing AVL geometry...
echo.

cd avl_files

REM Create simplified command file
(
echo LOAD
echo uav.avl
echo OPER
echo X
echo.
echo QUIT
) > avl_test.txt

REM Run AVL
"C:\Users\bradrothenberg\OneDrive - nTop\Sync\AVL\avl.exe" < avl_test.txt

echo.
echo ============================================================
echo AVL test complete!
echo.
echo If you see "Trefftz drag" output above, the geometry is valid.
echo ============================================================
pause
