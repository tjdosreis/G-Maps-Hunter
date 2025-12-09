import asyncio
import sys

# --- CORREÇÃO CRÍTICA PARA WINDOWS ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# -------------------------------------

import streamlit as st
from playwright.sync_api import sync_playwright
import pandas as pd
import time
import random

# --- CONFIGURAÇÃO DA UI ---
st.set_page_config(page_title="G-Maps Hunter v3.0", page_icon="🎯", layout="wide")

st.title("🎯 G-Maps Hunter v3.0 (Deep Dive)")
st.markdown("**Extração Completa:** Nome + Link + 📞 Telefone + 🌐 Site + ⭐ Nota")

with st.sidebar:
    st.header("⚙️ Configurações da Missão")
    termo_busca = st.text_input("Alvo:", placeholder="Ex: Pizzaria em Centro, BH")
    qtd_scrolls = st.slider("Profundidade (Scrolls)", 1, 20, 5)
    botao_iniciar = st.button("🚀 Iniciar Mineração", type="primary")

# --- MOTOR DE INTELIGÊNCIA ---
def extrair_detalhes(page):
    """Função auxiliar que tenta achar os dados dentro da página de detalhes"""
    dados = {"Telefone": "N/A", "Site": "N/A", "Nota": "N/A"}
    
    try:
        # 1. Extrai Telefone (Procura botão que começa com 'phone:')
        # O seletor procura um botão que tenha o atributo data-item-id começando com phone
        try:
            btn_phone = page.locator("button[data-item-id^='phone:']").first
            if btn_phone.count() > 0:
                # O texto do botão geralmente é o número. Às vezes tem rótulo, então pegamos o aria-label
                dados["Telefone"] = btn_phone.get_attribute("aria-label").replace("Ligar para: ", "").strip()
        except: pass

        # 2. Extrai Site (Procura botão que começa com 'authority')
        try:
            btn_site = page.locator("a[data-item-id='authority']").first
            if btn_site.count() > 0:
                dados["Site"] = btn_site.get_attribute("href")
        except: pass

        # 3. Extrai Nota (Geralmente num span com aria-label de estrelas)
        try:
            # Tenta pegar o número grande (ex: 4,8)
            nota_element = page.locator("div[role='img']").get_attribute("aria-label") 
            # Às vezes o Maps muda, vamos tentar um seletor genérico de texto de review
            if not nota_element:
                 ele = page.locator("span.fontBodyMedium > span").first
                 if ele.count() > 0:
                     dados["Nota"] = ele.inner_text()
            else:
                dados["Nota"] = nota_element.split(" ")[0] # Pega só o "4,8"
        except: pass

    except Exception as e:
        print(f"Erro ao extrair detalhes: {e}")
    
    return dados

def rodar_robo(termo, scrolls):
    # Área de Status Dinâmico
    status_main = st.status("🔧 Inicializando Robô...", expanded=True)
    lista_preliminar = []
    lista_final = []

    with sync_playwright() as p:
        # Inicia Navegador
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # --- FASE 1: ARRASTÃO (Coleta de Links) ---
        status_main.write(f"🌍 Fase 1: Mapeando terreno para '{termo}'...")
        page.goto("https://www.google.com/maps", timeout=60000)
        
        # Busca
        page.wait_for_selector("input#searchboxinput")
        page.fill("input#searchboxinput", termo)
        page.keyboard.press("Enter")
        
        # Espera carregar feed
        status_main.write("⏳ Aguardando resultados...")
        page.wait_for_selector("div[role='feed']", timeout=15000)
        
        # Scroll Infinito
        for i in range(scrolls):
            page.hover("div[role='feed']")
            page.mouse.wheel(0, 3000)
            time.sleep(random.uniform(2, 3))
            status_main.write(f"   📜 Scroll {i+1}/{scrolls}...")
        
        # Coleta os Links Básicos
        status_main.write("👀 Listando alvos...")
        elementos = page.locator("div[role='feed'] > div > div > a").all()
        
        for el in elementos:
            link = el.get_attribute("href")
            nome = el.get_attribute("aria-label")
            if nome and link and "google.com" not in nome:
                lista_preliminar.append({"Empresa": nome, "Link": link})
        
        total_leads = len(lista_preliminar)
        status_main.write(f"✅ Fase 1 Concluída: {total_leads} leads potenciais identificados.")
        
        # --- FASE 2: ENRIQUECIMENTO (Deep Dive) ---
        status_main.write(f"🕵️‍♂️ Fase 2: Extraindo dados de contato (Isso pode demorar)...")
        
        progress_bar = status_main.progress(0)
        
        for i, item in enumerate(lista_preliminar):
            # Navega direto para o link da empresa
            try:
                page.goto(item["Link"], timeout=30000)
                page.wait_for_load_state("domcontentloaded") # Espera carregar um pouco
                
                # Extrai os dados novos
                detalhes = extrair_detalhes(page)
                
                # Junta tudo
                item_completo = {
                    "Empresa": item["Empresa"],
                    "Telefone": detalhes["Telefone"],
                    "Site": detalhes["Site"],
                    "Nota": detalhes["Nota"],
                    "Link Maps": item["Link"]
                }
                lista_final.append(item_completo)
                
                # Feedback Visual
                status_main.write(f"   📞 {item['Empresa']} -> {detalhes['Telefone']}")
                
                # Atualiza barra
                progress_bar.progress((i + 1) / total_leads)
                
            except Exception as e:
                status_main.write(f"   ❌ Falha ao acessar {item['Empresa']}")
        
        browser.close()
        status_main.update(label="🎉 Mineração Completa!", state="complete", expanded=False)

    return pd.DataFrame(lista_final)

# --- EXECUÇÃO ---
if botao_iniciar and termo_busca:
    try:
        df = rodar_robo(termo_busca, qtd_scrolls)
        
        # Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Leads Totais", len(df))
        c2.metric("Com Telefone", len(df[df["Telefone"] != "N/A"]))
        c3.metric("Com Site", len(df[df["Site"] != "N/A"]))
        
        st.dataframe(df, use_container_width=True)
        
        # Exportação Otimizada
        csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig') # Ponto e vírgula para Excel BR
        st.download_button(
            label="💰 Baixar Planilha Rica (CSV)",
            data=csv,
            file_name=f"leads_ricos_{termo_busca.replace(' ', '_')}.csv",
            mime="text/csv",
        )
        
    except Exception as e:
        st.error(f"Erro Crítico: {e}")