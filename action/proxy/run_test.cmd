@echo off
cd /d "%~dp0..\.."
python action/proxy/server.py --test-email monteretroion@gmail.com > action/proxy/_test_output.txt 2>&1
type action/proxy/_test_output.txt
