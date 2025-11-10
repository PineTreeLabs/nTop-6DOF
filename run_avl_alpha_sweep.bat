@echo off
REM Run AVL alpha sweep to get CL, CD curves
echo Running AVL alpha sweep...
echo.

cd avl_files

REM Create command file for alpha sweep from -5 to 15 degrees
(
echo LOAD
echo uav.avl
echo MASS
echo uav.mass
echo OPER
echo A
echo A -5
echo
echo X
echo FT
echo alpha_-5.ft
echo A
echo A 0
echo
echo X
echo FT
echo alpha_0.ft
echo A
echo A 2
echo
echo X
echo FT
echo alpha_2.ft
echo A
echo A 5
echo
echo X
echo FT
echo alpha_5.ft
echo A
echo A 10
echo
echo X
echo FT
echo alpha_10.ft
echo A
echo A 15
echo
echo X
echo FT
echo alpha_15.ft
echo
echo QUIT
) > avl_sweep.txt

REM Run AVL
"C:\Users\bradrothenberg\OneDrive - nTop\Sync\AVL\avl.exe" < avl_sweep.txt > avl_sweep_output.txt

echo.
echo ============================================================
echo AVL alpha sweep complete!
echo.
echo Output files created:
echo   alpha_-5.ft, alpha_0.ft, alpha_2.ft, alpha_5.ft,
echo   alpha_10.ft, alpha_15.ft
echo.
echo Full output saved to: avl_sweep_output.txt
echo ============================================================
echo.

REM Parse and display results
echo Alpha    CL      CD      L/D
echo -----    -----   -----   -----
findstr /C:"Alpha" /C:"CLtot" /C:"CDtot" alpha_-5.ft | find /V "CDvis" > temp.txt
type temp.txt
del temp.txt

pause
