@echo off
:: 1. Garante que estamos na pasta certa (CRÍTICO)
cd /d "F:\GMaps_Hunter"

:: 2. Inicia o servidor do Streamlit
:: O comando 'run' abre o navegador sozinho
streamlit run main.py

:: O script para aqui e fica rodando. 
:: Se você fechar a janela preta, o site sai do ar.