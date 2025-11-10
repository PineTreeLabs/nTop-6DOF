@echo off
REM Run AVL analysis and show results
echo Running AVL analysis...
echo.

cd avl_files

REM Create command file with analysis
(
echo LOAD
echo uav.avl
echo MASS
echo uav.mass
echo OPER
echo A
echo A 5
echo.
echo X
echo.
echo ST
echo results.st
echo.
echo FT
echo results.ft
echo.
) > run_analysis.txt

REM Run AVL
"C:\Users\bradrothenberg\OneDrive - nTop\Sync\AVL\avl.exe" < run_analysis.txt

echo.
echo ============================================================
echo ANALYSIS RESULTS
echo ============================================================
echo.

REM Display key results
findstr /C:"CLtot" /C:"CDtot" /C:"Cmtot" /C:"Strips" /C:"Vortices" results.ft

echo.
echo ============================================================
echo Full results saved to:
echo   results.ft  (forces and moments)
echo   results.st  (stability derivatives)
echo ============================================================
pause
