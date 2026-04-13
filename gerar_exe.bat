@echo off
title Gerando EXE - PDV Padaria Da Laine
color 0A
echo.
echo ================================================
echo   PDV Padaria Da Laine
echo   Gerando executavel final...
echo ================================================
echo.

cd /d C:\pdv_padaria

:: Verificar Python
echo [1/5] Verificando Python...
python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    pause & exit /b 1
)

:: Instalar dependencias
echo.
echo [2/5] Instalando dependencias...
python -m pip install customtkinter pillow pyinstaller --quiet --upgrade

:: Limpar builds anteriores
echo.
echo [3/5] Limpando builds anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist PDV_Padaria_DaLaine.spec del /q PDV_Padaria_DaLaine.spec
if exist logo.ico del /q logo.ico

:: Criar logo.ico
echo.
echo [4/5] Gerando icone...
python gerar_icone.py
if not exist logo.ico (
    echo Aviso: icone nao gerado, continuando sem icone...
)

:: Gerar EXE — ONEDIR para atualizacao automatica funcionar!
echo.
echo [5/5] Gerando EXE (aguarde 5-10 minutos)...
echo.

if exist logo.ico (
    python -m PyInstaller ^
        --onedir ^
        --windowed ^
        --name "PDV_Padaria_DaLaine" ^
        --icon "logo.ico" ^
        --add-data "logo.png;." ^
        --add-data "logo.ico;." ^
        --add-data "tema.py;." ^
        --add-data "versao.json;." ^
        --add-data "banco;banco" ^
        --add-data "telas;telas" ^
        --add-data "utils;utils" ^
        --add-data "fiscal;fiscal" ^
        --hidden-import customtkinter ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import sqlite3 ^
        --hidden-import tkinter ^
        --hidden-import tkinter.messagebox ^
        --hidden-import hashlib ^
        --hidden-import json ^
        --hidden-import threading ^
        --hidden-import urllib.request ^
        --hidden-import ssl ^
        --hidden-import base64 ^
        --hidden-import logging ^
        --collect-all customtkinter ^
        --noconfirm ^
        main.py
) else (
    python -m PyInstaller ^
        --onedir ^
        --windowed ^
        --name "PDV_Padaria_DaLaine" ^
        --add-data "logo.png;." ^
        --add-data "tema.py;." ^
        --add-data "versao.json;." ^
        --add-data "banco;banco" ^
        --add-data "telas;telas" ^
        --add-data "utils;utils" ^
        --add-data "fiscal;fiscal" ^
        --hidden-import customtkinter ^
        --hidden-import PIL ^
        --hidden-import PIL.Image ^
        --hidden-import sqlite3 ^
        --hidden-import tkinter ^
        --collect-all customtkinter ^
        --noconfirm ^
        main.py
)

if errorlevel 1 (
    echo.
    echo ERRO ao gerar EXE!
    pause & exit /b 1
)

:: ── Copiar arquivos necessarios para dist ──
echo.
echo Copiando arquivos para dist...

if exist licenca.key copy /y licenca.key dist\PDV_Padaria_DaLaine\licenca.key >nul
if exist logo.png    copy /y logo.png    dist\PDV_Padaria_DaLaine\logo.png    >nul
if exist logo.ico    copy /y logo.ico    dist\PDV_Padaria_DaLaine\logo.ico    >nul

:: IMPORTANTE: copia versao.json para fora do _internal (necessario para atualizacao automatica)
copy /y versao.json dist\PDV_Padaria_DaLaine\versao.json >nul
echo versao.json copiado para dist!

:: Mostra versao gerada
echo.
for /f "tokens=2 delims=:" %%a in ('findstr "versao" versao.json') do (
    echo Versao gerada: %%a
    goto :fim_versao
)
:fim_versao

echo.
echo ================================================
echo   EXE GERADO COM SUCESSO!
echo ================================================
echo   Pasta: dist\PDV_Padaria_DaLaine\
echo   EXE:   dist\PDV_Padaria_DaLaine\PDV_Padaria_DaLaine.exe
echo.
echo   IMPORTANTE: Substitua a licenca.key da padaria!
echo   licenca da padaria: 09FD6BA46D10D137
echo.
echo   Copie a PASTA INTEIRA para pendrive
echo   e leve para a padaria!
echo ================================================
echo.
set /p abrir="Abrir pasta dist\? (S/N): "
if /i "%abrir%"=="S" explorer dist\PDV_Padaria_DaLaine
pause
