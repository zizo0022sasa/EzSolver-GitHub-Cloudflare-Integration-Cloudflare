@echo off
chcp 65001 > nul
title Antigravity Conversation Renamer
python "%~dp0rename_conversation.py"
pause
