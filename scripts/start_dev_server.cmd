@echo off
cd /d "%~dp0.."
set "NODE_EXE=C:\Users\aruto\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if not exist "%NODE_EXE%" set "NODE_EXE=node.exe"
if not exist "logs" mkdir logs
"%NODE_EXE%" "node_modules\vite\bin\vite.js" --host 127.0.0.1 --port 5173 --strictPort > "logs\vite-direct.out.log" 2> "logs\vite-direct.err.log"
