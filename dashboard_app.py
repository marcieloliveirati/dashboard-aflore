import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta, date
import os
import streamlit.components.v1 as components
import time
import calendar 
import gspread
from google.oauth2.service_account import Credentials

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira linha do Streamlit)
st.set_page_config(page_title="Aflore - Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# MOTORES DE MEMÓRIA (CACHE) PARA BLINDAR O SERVIDOR
# ==========================================
@st.cache_data(ttl=900) # Guarda os dados por 15 minutos
def carregar_dados_visao_geral(url_planilha, secrets_dict):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(secrets_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    planilha = client.open_by_url(url_planilha)
    
    xls_dict = {}
    for aba in planilha.worksheets():
        valores = aba.get_all_values()
        if valores:
            xls_dict[aba.title] = pd.DataFrame(valores)
    return xls_dict

@st.cache_data(ttl=900) # Guarda os dados por 15 minutos
def carregar_dados_tabloides(url_tabloides, secrets_dict):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(secrets_dict, scopes=scopes)
    client = gspread.authorize(credentials)
    
    planilha_tab = client.open_by_url(url_tabloides)
    aba_efetividade = planilha_tab.worksheet("efetividade")
    
    dados_brutos = aba_efetividade.get_all_values()
    df_tab = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
    
    # Limpeza básica e imediata
    df_tab = df_tab[df_tab['SKU'].astype(str).str.strip() != '']
    df_tab = df_tab[df_tab['TABLOIDE'].astype(str).str.strip() != '']
    
    return df_tab

# ==========================================
# --- SISTEMA DE SEGURANÇA E LOGIN ---
# ==========================================
if "logado" not in st.session_state:
    st.session_state.logado = False

# Tela de Login (A Sala de Espera)
if not st.session_state.logado:
    st.markdown("""
        <style>
            .main { background-color: #0f1116; color: #ffffff; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1.2, 1])
    
    with col_login:
        with st.form("form_login", clear_on_submit=False):
            col_img1, col_img2, col_img3 = st.columns([1, 1.5, 1])
            with col_img2:
                if os.path.exists("logo_aflore.png"):
                    st.image("logo_aflore.png", use_column_width=True)
                elif os.path.exists("logo.png"):
                    st.image("logo.png", use_column_width=True)
                else:
                    st.markdown("<h3 style='text-align: center; color: #00d48a;'>AFLORE DIGITAL</h3>", unsafe_allow_html=True)
                    
            st.markdown("<h4 style='text-align: center; color: #555; margin-bottom: 20px;'>Acesso Restrito</h4>", unsafe_allow_html=True)
            
            usuario = st.text_input("👤 Usuário")
            senha = st.text_input("🔑 Senha", type="password")
            
            submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                usuarios_permitidos = {
                    "diretoria": "aflore2026",
                    "admin": "123"
                }
                
                if usuario in usuarios_permitidos and usuarios_permitidos[usuario] == senha:
                    st.session_state.logado = True
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")

        # --- ASSINATURA NA TELA DE LOGIN ---
        st.markdown("""
            <div style="text-align: center; color: #888; font-size: 0.75rem; margin-top: 15px;">
                <b>Vision Sale v1.9</b><br>
                Automatizado por: <b>Marciel Oliveira</b><br>
                <i>Transformando dados em clareza.</i>
            </div>
        """, unsafe_allow_html=True)

# A Sala de Comando (O Dashboard)
else:
    # --- ESTILOS DO DASHBOARD (TELA LIVRE / PDF SEMPRE LIGHT MODE) ---
    st.markdown("""
        <style>
            /* === ESTILOS PARA A TELA === */
            .stMetric { background-color: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #00d48a; }
            .stHeading h1 { color: #00d48a; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
            .stHeading h2 { color: #00b4d8; }
            .stHeading h3 { color: #f72585; }
            .welcome-msg { text-align: center; color: #555; margin-top: 100px; font-size: 1.2rem; }
            
            [data-testid="stFileUploader"] label { display: flex; justify-content: center; }
            [data-testid="stFileUploader"] section { align-items: center !important; text-align: center; }
            [data-testid="stSidebarUserContent"] h3 { text-align: center; }
            [data-testid="stRadio"] > label { display: flex; justify-content: center; }
            [data-testid="stRadio"] div[role="radiogroup"] { width: fit-content; margin: 0 auto; }

            div[data-testid="stMetricValue"] > div { font-size: 1.5rem !important; white-space: nowrap !important; }

            /* --- Oculta as divs exclusivas do PDF e forçadores no modo TELA --- */
            .print-only { display: none; }
            .page-break { display: none; }

            /* === MÁGICA DO PDF: FORÇAR LIGHT MODE ABSOLUTO E PAGINAÇÃO === */
            @media print {
                * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }

                html, body, [class*="stApp"], [data-testid="stAppViewContainer"], .main {
                    background-color: #ffffff !important;
                    background-image: none !important;
                }

                p, span, div, h1, h2, h3, h4, h5, h6, text, label, li {
                    color: #000000 !important;
                }

                [data-baseweb="select"] > div, [data-testid="stSelectbox"] div {
                    background-color: #ffffff !important;
                    border-color: #cccccc !important;
                }

                .stHeading h1 { color: #00d48a !important; }
                .stHeading h2 { color: #00b4d8 !important; }
                .stHeading h3 { color: #f72585 !important; }
                .gps-box h4 { color: #f72585 !important; }
                [data-testid="stMetricDelta"] *, [data-testid="stMetricDelta"] svg { color: inherit !important; }

                [data-testid="metric-container"], .gps-box {
                    background-color: #f8f9fa !important;
                    border-left: 5px solid #00d48a !important;
                    border-radius: 8px !important;
                    padding: 10px !important; margin-bottom: 10px !important;
                    page-break-inside: avoid !important;
                    break-inside: avoid !important;
                }
                div[data-testid="stMetricValue"] > div { font-size: 1.2rem !important; }

                /* Forçar Transparência e Evitar Corte nos Gráficos */
                [data-testid="stPlotlyChart"], [data-testid="stPlotlyChart"] > div, 
                .js-plotly-plot, .js-plotly-plot .main-svg {
                    background-color: transparent !important;
                    background: transparent !important;
                    page-break-inside: avoid !important;
                    break-inside: avoid !important;
                }
                .js-plotly-plot .plotly .bg { fill: transparent !important; }
                .js-plotly-plot .plotly text { fill: #000000 !important; }
                .js-plotly-plot .plotly .gridlayer path { stroke: #e0e0e0 !important; }
                .js-plotly-plot .plotly .zerolinelayer path { stroke: #cccccc !important; }

                /* QUEBRA DE PÁGINA INTELIGENTE E CAMUFLAGEM DE ELEMENTOS DE TELA */
                .hide-on-print { display: none !important; }

                .page-break {
                    display: block !important;
                    page-break-before: always !important;
                    break-before: page !important;
                    height: 0 !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }

                /* Esconde Tabelas Streamlit Nativas no PDF e Mostra a Tabela HTML Customizada */
                [data-testid="stDataFrame"] { display: none !important; } 
                .print-only { display: block !important; page-break-inside: avoid !important; }

                /* Estilização da Tabela de Impressão */
                .tabela-pdf { 
                    width: 100%; border-collapse: collapse; font-family: 'Helvetica Neue', sans-serif; 
                    font-size: 0.85rem; margin-top: 10px; background-color: #ffffff !important; color: #000000 !important;
                }
                .tabela-pdf th, .tabela-pdf td { 
                    border: 1px solid #e0e0e0 !important; padding: 8px !important; text-align: left !important; 
                    background-color: #ffffff !important; color: #000000 !important;
                }
                .tabela-pdf th { background-color: #f8f9fa !important; color: #00d48a !important; font-weight: bold !important; }

                /* Esconder Menus e Botões Inúteis para o papel */
                section[data-testid="stSidebar"], header[data-testid="stHeader"], .btn-imprimir, .stButton {
                    display: none !important;
                }
                .block-container { padding-top: 0rem !important; }
            }
        </style>
    """, unsafe_allow_html=True)

    # --- CABEÇALHO COM BOTÕES DE PDF E SAIR ---
    col_titulo, col_imprimir, col_sair = st.columns([7, 2, 1])
    
    with col_titulo:
        st.title("📊 Vision Sale - Inteligência de Vendas")
        st.subheader("Painel Analítico de Desempenho de Lojas")
        
    with col_imprimir:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🖨️ Gerar PDF", use_container_width=True):
            components.html(
                f"<script>setTimeout(function() {{ window.parent.print(); }}, 1000);</script><span style='display:none'>{time.time()}</span>", 
                height=0, 
                width=0
            )
            
    with col_sair:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.rerun()

    # --- MENU LATERAL (SIDEBAR) ---
    if os.path.exists("logo_aflore.png"):
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        with col2:
            st.image("logo_aflore.png", use_column_width=True)
    elif os.path.exists("logo.png"):
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        with col2:
            st.image("logo.png", use_column_width=True)
    else:
        st.sidebar.markdown("<h2 style='text-align: center; color: #00d48a;'>AFLORE DIGITAL</h2>", unsafe_allow_html=True)
        
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    # --- BOTÃO DE ATUALIZAÇÃO MANUAL (LIMPA O CACHE) ---
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Atualizar Dados Agora", use_container_width=True):
        st.cache_data.clear() # Limpa a memória para buscar dados novos do Sheets
        st.rerun()

    # ==========================================
    # 🧭 INÍCIO DO SISTEMA DE NAVEGAÇÃO
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧭 Navegação do Sistema")
    
    modulo_selecionado = st.sidebar.radio(
        "Selecione o módulo de análise:",
        ["📈 Visão Geral de Lojas", "🔥 Inteligência de Tabloides"]
    )
    st.sidebar.markdown("---")

    # ==========================================
    # MÓDULO 1: VISÃO GERAL DE LOJAS
    # ==========================================
    if modulo_selecionado == "📈 Visão Geral de Lojas":
        
        # --- MOTORES DE LIMPEZA E TRADUÇÃO ---
        def clean_numeric(val):
            if pd.isna(val) or str(val).strip() in ['#VALOR!', '-', '']: return 0.0
            if isinstance(val, (int, float)): return float(val)
            val_str = str(val).replace('R$', '').strip()
            if '.' in val_str and ',' not in val_str:
                try: return float(val_str)
                except: pass
            try: return float(val_str.replace('.', '').replace(',', '.'))
            except: return 0.0

        # NOVO MOTOR ROBUSTO DE DATAS (Força o retorno de datetime.date puro)
        def parse_data(val):
            if pd.isna(val): return pd.NaT
            if isinstance(val, (datetime, date)): return val.date() if isinstance(val, datetime) else val
            val_str = str(val).strip().lower().replace('-', '/')
            try:
                partes = val_str.split('/')
                if len(partes) >= 2:
                    dia = int(''.join(filter(str.isdigit, partes[0])))
                    mes_str = partes[1][:3]
                    meses_map = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12}
                    if mes_str in meses_map:
                        mes = meses_map[mes_str]
                    else:
                        mes = int(''.join(filter(str.isdigit, partes[1])))
                        
                    ano = date.today().year
                    if len(partes) >= 3:
                        ano_str = ''.join(filter(str.isdigit, partes[2]))
                        if len(ano_str) == 4:
                            ano = int(ano_str)
                        elif len(ano_str) == 2:
                            ano = 2000 + int(ano_str)
                    return date(ano, mes, dia)
            except: pass
            return pd.NaT
            
        df = pd.DataFrame()

        # --- CONEXÃO COM CACHE VIA GOOGLE SHEETS API ---
        st.sidebar.markdown("### 🔄 Sincronização de Dados")
        
        try:
            url_planilha = st.secrets.get("URL_PLANILHA", "")
            
            if not url_planilha:
                st.sidebar.warning("⚠️ URL da planilha não configurada no Streamlit Secrets.")
            else:
                with st.sidebar.status("Conectando ao Drive...", expanded=False) as status:
                    secrets_dict = dict(st.secrets["gcp_service_account"])
                    xls_dict = carregar_dados_visao_geral(url_planilha, secrets_dict)
                    status.update(label="Conexão Estabelecida!", state="complete")

                if xls_dict:
                    lista_abas = list(xls_dict.keys())
                    st.sidebar.markdown("---")
                    
                    # ----------------------------------------------------
                    # RASTREADOR DO MÊS VIGENTE (Seleciona a aba correta automaticamente)
                    # ----------------------------------------------------
                    meses_nomes = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
                    mes_atual_nome = meses_nomes.get(date.today().month, "")
                    
                    index_padrao = 0
                    for i, aba in enumerate(lista_abas):
                        if mes_atual_nome.lower() in aba.lower():
                            index_padrao = i
                            break
                            
                    aba_selecionada = st.sidebar.selectbox("📅 Selecione o Mês/Guia:", lista_abas, index=index_padrao)
                    
                    df_raw = xls_dict[aba_selecionada]
                    
                    idx_cabecalho = -1
                    for i in range(min(5, len(df_raw))):
                        valores_linha = [str(val).strip().upper() for val in df_raw.iloc[i].values]
                        if 'V.L' in valores_linha or 'V.L.' in valores_linha:
                            idx_cabecalho = i
                            break
                            
                    if idx_cabecalho >= 0:
                        headers = [str(val).strip().upper() for val in df_raw.iloc[idx_cabecalho].values]
                        vl_indices = [i for i, h in enumerate(headers) if 'V.L' in h]
                        nomes_lojas = ['Loja 01', 'Loja 02', 'Loja 03', 'Loja 04', 'Loja 05']
                        
                        metas_dinamicas = {}
                        for num_loja, col_vl in enumerate(vl_indices):
                            if num_loja >= len(nomes_lojas): break
                            nome_loja = nomes_lojas[num_loja]
                            col_data = col_vl - 1
                            
                            meta_vl, meta_cli = 0.0, 0.0
                            if col_data >= 0:
                                for _, r in df_raw.iterrows():
                                    if str(r[col_data]).strip().upper() == 'META':
                                        meta_vl = clean_numeric(r[col_vl])
                                        meta_cli = clean_numeric(r[col_vl + 3])
                                        break
                            meta_tmv = meta_vl / meta_cli if meta_cli > 0 else 0.0
                            metas_dinamicas[nome_loja] = {'vl': meta_vl, 'cli': meta_cli, 'tmv': meta_tmv}
                        
                        all_data = []
                        for idx, row in df_raw.iterrows():
                            if idx <= idx_cabecalho: continue 
                            
                            for num_loja, col_vl in enumerate(vl_indices):
                                if num_loja >= len(nomes_lojas): break 
                                nome_loja = nomes_lojas[num_loja]
                                
                                try:
                                    col_data = col_vl - 1 
                                    if col_data < 0: continue
                                    
                                    val_data_crua = row[col_data]
                                    str_data_check = str(val_data_crua).strip().upper()
                                    
                                    if pd.isna(val_data_crua) or 'TOTAL' in str_data_check or 'META' in str_data_check or str_data_check in ('', 'NAN', 'NAT', 'NONE'):
                                        continue
                                        
                                    vl = clean_numeric(row[col_vl])
                                    tmv = clean_numeric(row[col_vl + 1])
                                    pa = clean_numeric(row[col_vl + 2])
                                    clientes = clean_numeric(row[col_vl + 3])
                                    
                                    if vl > 0 or clientes > 0:
                                        all_data.append({
                                            'Data_Raw': val_data_crua, 
                                            'Loja': nome_loja,
                                            'Venda_Liquida': vl, 
                                            'Ticket_Medio': tmv,
                                            'PA': pa, 
                                            'Clientes': int(clientes),
                                            'Meta_Faturamento': metas_dinamicas[nome_loja]['vl'],
                                            'Meta_Clientes': metas_dinamicas[nome_loja]['cli'],
                                            'Meta_TMV': metas_dinamicas[nome_loja]['tmv']
                                        })
                                except Exception: pass
                        
                        df = pd.DataFrame(all_data)
                        
                        if not df.empty:
                            df['Data_Real'] = df['Data_Raw'].apply(parse_data)
                            df = df.dropna(subset=['Data_Real']) 
                            df['Data_String'] = df['Data_Real'].apply(lambda d: d.strftime("%d/%m") if pd.notnull(d) else "")
                        
                    if df.empty:
                        st.sidebar.warning(f"⚠️ Aba: {aba_selecionada} sem dados válidos.")
                    else:
                        st.sidebar.success(f"✅ Aba '{aba_selecionada}' lida com sucesso!")
                        
        except Exception as e:
            st.sidebar.error(f"❌ Erro de conexão: {str(e)}")
            st.sidebar.info("Verifique suas credenciais no Streamlit Secrets.")

        # --- CAMADA DE VISUALIZAÇÃO E FILTROS ---
        if not df.empty and 'Loja' in df.columns:
            
            lista_lojas = ['Todas as Lojas'] + list(df['Loja'].unique())
            st.sidebar.markdown("---")
            loja_selecionada = st.selectbox("🏪 Selecione a Unidade:", lista_lojas)

            st.sidebar.markdown("---")
            st.sidebar.subheader("📅 Filtro de Período")
            opcao_data = st.sidebar.radio(
                "Selecione o período de análise:", 
                ["Todo o Período", "Hoje", "Ontem", "Últimos 7 Dias", "Personalizado"]
            )

            # Usa o relógio nativo puro do Python para bater 100% com o Streamlit DatePicker
            hoje = date.today()
            df_filtrado = df.copy()

            # --- MOTOR DE INTELIGÊNCIA: GPS DE VENDAS ---
            df_contexto = df.copy()
            if loja_selecionada != 'Todas as Lojas':
                df_contexto = df_contexto[df_contexto['Loja'] == loja_selecionada]

            meta_mes_total = df_contexto.drop_duplicates(subset=['Loja'])['Meta_Faturamento'].sum()
            faturado_mes_total = df_contexto['Venda_Liquida'].sum()

            max_data_planilha = df_contexto['Data_Real'].max()
            nova_meta_diaria, meta_diaria_original, dias_uteis_restantes, dias_uteis_passados = 0, 0, 0, 0
            
            if pd.notna(max_data_planilha):
                ano_ref = max_data_planilha.year
                mes_ref = max_data_planilha.month
                _, num_dias = calendar.monthrange(ano_ref, mes_ref)

                dias_uteis_total = sum(1 for d in range(1, num_dias + 1) if date(ano_ref, mes_ref, d).weekday() < 6)
                dias_uteis_passados = sum(1 for d in range(1, max_data_planilha.day + 1) if date(ano_ref, mes_ref, d).weekday() < 6)
                dias_uteis_restantes = dias_uteis_total - dias_uteis_passados

                meta_restante = max(0, meta_mes_total - faturado_mes_total)
                
                if dias_uteis_restantes > 0:
                    nova_meta_diaria = meta_restante / dias_uteis_restantes
                else:
                    nova_meta_diaria = 0 if meta_restante <= 0 else meta_restante
                    
                meta_diaria_original = meta_mes_total / dias_uteis_total if dias_uteis_total > 0 else 0

            # --- APLICAÇÃO DOS FILTROS (BLINDADO COM DATE NATIVO) ---
            if opcao_data == "Hoje":
                df_filtrado = df_filtrado[df_filtrado['Data_Real'] == hoje]
            elif opcao_data == "Ontem":
                ontem = hoje - timedelta(days=1)
                df_filtrado = df_filtrado[df_filtrado['Data_Real'] == ontem]
            elif opcao_data == "Últimos 7 Dias":
                sete_dias_atras = hoje - timedelta(days=7)
                df_filtrado = df_filtrado[(df_filtrado['Data_Real'] >= sete_dias_atras) & (df_filtrado['Data_Real'] <= hoje)]
            elif opcao_data == "Personalizado":
                datas_selecionadas = st.sidebar.date_input("Escolha o intervalo:", [hoje - timedelta(days=7), hoje], format="DD/MM/YYYY")
                if len(datas_selecionadas) == 2:
                    data_inicio, data_fim = datas_selecionadas
                    df_filtrado = df_filtrado[(df_filtrado['Data_Real'] >= data_inicio) & (df_filtrado['Data_Real'] <= data_fim)]
                else:
                    st.sidebar.warning("Selecione a data de Início e de Fim.")

            if loja_selecionada != 'Todas as Lojas':
                df_filtrado = df_filtrado[df_filtrado['Loja'] == loja_selecionada]

            if df_filtrado.empty:
                st.warning(f"Nenhuma venda encontrada para o período selecionado.")
            else:
                total_faturamento = df_filtrado['Venda_Liquida'].sum()
                total_clientes = df_filtrado['Clientes'].sum()
                ticket_medio_geral = total_faturamento / total_clientes if total_clientes > 0 else 0
                pa_medio = df_filtrado['PA'].mean()

                # --- LÓGICA DE METAS PROPORCIONAIS ---
                dias_no_filtro = df_filtrado['Data_Real'].nunique()
                dias_totais_planilha = df['Data_Real'].nunique()
                fator_meta = dias_no_filtro / dias_totais_planilha if dias_totais_planilha > 0 else 1

                if loja_selecionada == 'Todas as Lojas':
                    df_unicas = df_filtrado.drop_duplicates(subset=['Loja'])
                    meta_global_fat = df_unicas['Meta_Faturamento'].sum()
                    meta_global_cli = df_unicas['Meta_Clientes'].sum()
                    meta_global_tmv = meta_global_fat / meta_global_cli if meta_global_cli > 0 else 0
                else:
                    meta_global_fat = df_filtrado['Meta_Faturamento'].iloc[0]
                    meta_global_cli = df_filtrado['Meta_Clientes'].iloc[0]
                    meta_global_tmv = df_filtrado['Meta_TMV'].iloc[0]

                meta_prop_fat = meta_global_fat * fator_meta
                meta_prop_cli = meta_global_cli * fator_meta
                meta_prop_tmv = meta_global_tmv

                perc_fat = (total_faturamento / meta_prop_fat) * 100 if meta_prop_fat > 0 else 0
                perc_cli = (total_clientes / meta_prop_cli) * 100 if meta_prop_cli > 0 else 0
                perc_tmv = (ticket_medio_geral / meta_prop_tmv) * 100 if meta_prop_tmv > 0 else 0

                str_meta_fat = f"R$ {meta_prop_fat:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                str_meta_cli = f"{int(meta_prop_cli):,}".replace(',', '.')
                str_meta_tmv = f"R$ {meta_prop_tmv:,.2f}".replace('.', ',')

                # --- CARDS VISUAIS ---
                st.markdown("### 🎯 Acompanhamento de Metas")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                with kpi1: 
                    st.metric("💰 Faturamento", f"R$ {total_faturamento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), f"{perc_fat:.1f}% da Meta")
                    st.markdown(f"<div style='font-size: 1rem; font-weight: 700; color: #f77f00; margin-top: -15px; margin-bottom: 10px;'>🎯 Previsto: {str_meta_fat}</div>", unsafe_allow_html=True)
                    st.progress(min(perc_fat / 100, 1.0))
                    
                with kpi2: 
                    st.metric("👥 Clientes", f"{int(total_clientes):,}".replace(',', '.'), f"{perc_cli:.1f}% da Meta")
                    st.markdown(f"<div style='font-size: 1rem; font-weight: 700; color: #f77f00; margin-top: -15px; margin-bottom: 10px;'>🎯 Previsto: {str_meta_cli}</div>", unsafe_allow_html=True)
                    st.progress(min(perc_cli / 100, 1.0))
                    
                with kpi3: 
                    st.metric("🎟️ Ticket Médio", f"R$ {ticket_medio_geral:,.2f}".replace('.', ','), f"{perc_tmv:.1f}% da Meta")
                    st.markdown(f"<div style='font-size: 1rem; font-weight: 700; color: #f77f00; margin-top: -15px; margin-bottom: 10px;'>🎯 Previsto: {str_meta_tmv}</div>", unsafe_allow_html=True)
                    st.progress(min(perc_tmv / 100, 1.0))
                    
                with kpi4: 
                    st.metric("📦 Peças por Atend. (P.A)", f"{pa_medio:.1f}")
                    st.markdown("<div style='font-size: 1rem; font-weight: 600; color: #888888; margin-top: -15px; margin-bottom: 10px;'>Média do período</div>", unsafe_allow_html=True)

                # --- BANNER: GPS DE VENDAS ---
                str_nova_meta = f"R$ {nova_meta_diaria:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                str_meta_orig = f"R$ {meta_diaria_original:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                cor_alerta = "#00d48a" if nova_meta_diaria <= meta_diaria_original else "#f72585"
                mensagem_status = "Meta sob controle." if nova_meta_diaria <= meta_diaria_original else "Aceleração necessária."
                
                st.markdown(f"""
                <div class="gps-box" style='background-color: rgba(128,128,128, 0.1); padding: 20px; border-radius: 10px; border-left: 8px solid {cor_alerta}; margin-bottom: 25px; margin-top: 15px;'>
                    <h4 style='margin:0 0 10px 0; color: {cor_alerta};'>🧭 GPS de Vendas: Recálculo de Rota Diário</h4>
                    <div style='display: flex; justify-content: space-between; flex-wrap: wrap;'>
                        <div style='flex: 1; min-width: 200px;'>
                            <p class="gps-label" style='margin:0; font-size: 0.9rem; color: #888888;'>Meta Diária Original</p>
                            <p class="gps-val" style='margin:0; font-size: 1.4rem; font-weight: bold;'>{str_meta_orig}</p>
                        </div>
                        <div style='flex: 1; min-width: 200px;'>
                            <p class="gps-label" style='margin:0; font-size: 0.9rem; color: #888888;'>Meta Diária Exigida (Hoje)</p>
                            <p style='margin:0; font-size: 1.4rem; font-weight: bold; color: {cor_alerta};'>{str_nova_meta}</p>
                        </div>
                        <div style='flex: 1; min-width: 200px;'>
                            <p class="gps-label" style='margin:0; font-size: 0.9rem; color: #888888;'>Status do Mês</p>
                            <p class="gps-val" style='margin:0; font-size: 1.1rem;'>Restam <b>{dias_uteis_restantes} dias úteis</b>. {mensagem_status}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # --- MOTOR DE CÁLCULO PARA GRÁFICOS DIÁRIOS E ACUMULADOS ---
                df_diario = df_filtrado.groupby('Data_Real')['Venda_Liquida'].sum().sort_index().reset_index()
                df_diario['Data_String'] = df_diario['Data_Real'].apply(lambda d: d.strftime("%d/%m"))
                
                # Cálculo dos Acumulados
                df_diario['Realizado_Acumulado'] = df_diario['Venda_Liquida'].cumsum()
                
                if pd.notna(max_data_planilha):
                    def get_working_days_up_to(d):
                        try: return sum(1 for day in range(1, d.day + 1) if date(d.year, d.month, day).weekday() < 6)
                        except: return 1
                    df_diario['Dias_Uteis_Ate_Hoje'] = df_diario['Data_Real'].apply(get_working_days_up_to)
                    df_diario['Meta_Acumulada'] = df_diario['Dias_Uteis_Ate_Hoje'] * meta_diaria_original
                else:
                    df_diario['Meta_Acumulada'] = (np.arange(len(df_diario)) + 1) * meta_diaria_original

                col_esq, col_dir = st.columns(2)
                with col_esq:
                    st.subheader("📈 Tendência Diária x Meta")
                    fig_linha = px.line(df_diario, x='Data_String', y='Venda_Liquida', labels={'Venda_Liquida': 'Faturamento (R$)', 'Data_String': 'Dia'}, markers=True)
                    fig_linha.update_traces(line_color='#00b4d8', line_width=3, name='Realizado', showlegend=True)
                    fig_linha.add_hline(y=meta_diaria_original, line_dash="solid", line_color="#00d48a", annotation_text="Meta Original", annotation_position="bottom right")
                    if nova_meta_diaria > 0 and nova_meta_diaria != meta_diaria_original:
                        fig_linha.add_hline(y=nova_meta_diaria, line_dash="dash", line_color="#f72585", annotation_text="Meta Exigida", annotation_position="top right")
                    fig_linha.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_linha, use_container_width=True, theme="streamlit")

                with col_dir:
                    st.subheader("🏪 Previsto x Realizado por Unidade")
                    df_loja_sum = df_filtrado.groupby('Loja').agg({'Venda_Liquida': 'sum', 'Meta_Faturamento': 'first'}).reset_index()
                    df_loja_sum['Meta_Proporcional'] = df_loja_sum['Meta_Faturamento'] * fator_meta
                    df_barras = df_loja_sum.melt(id_vars='Loja', value_vars=['Venda_Liquida', 'Meta_Proporcional'], var_name='Tipo', value_name='Valor')
                    df_barras['Tipo'] = df_barras['Tipo'].map({'Venda_Liquida': 'Realizado', 'Meta_Proporcional': 'Previsto'})
                    
                    fig_barra = px.bar(df_barras, x='Loja', y='Valor', color='Tipo', barmode='group', 
                                       color_discrete_map={'Realizado': '#00b4d8', 'Previsto': '#a8a8a8'},
                                       labels={'Valor': 'Faturamento (R$)', 'Tipo': 'Métrica'},
                                       category_orders={'Tipo': ['Previsto', 'Realizado']})
                    
                    fig_barra.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_barra, use_container_width=True, theme="streamlit")

                # =========================================================================
                # --- INJEÇÃO DA QUEBRA DE PÁGINA PARA O RELATÓRIO PDF (FIM DA PÁG 1) ---
                # =========================================================================
                st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)
                st.markdown('<hr class="hide-on-print">', unsafe_allow_html=True)
                
                # --- NOVO GRÁFICO DO CMO: LINHA DE FUGA ACUMULADA (PÁGINA 2) ---
                st.subheader("📈 Faturamento Acumulado vs Meta Projetada")
                
                df_plot_acumulado = df_diario.rename(columns={
                    'Realizado_Acumulado': 'Realizado Acumulado',
                    'Meta_Acumulada': 'Meta Projetada Acumulada'   
                })
                
                fig_acumulado = px.line(df_plot_acumulado, x='Data_String', y=['Realizado Acumulado', 'Meta Projetada Acumulada'],
                                        labels={'value': 'Volume Financeiro (R$)', 'Data_String': 'Dia do Mês', 'variable': 'Indicador'},
                                        markers=True, color_discrete_map={'Realizado Acumulado': '#00b4d8', 'Meta Projetada Acumulada': '#00d48a'})
                
                fig_acumulado.update_traces(patch={"line": {"width": 4}}, selector={"name": "Realizado Acumulado"})
                fig_acumulado.update_traces(patch={"line": {"width": 3, "dash": "dash"}}, selector={"name": "Meta Projetada Acumulada"})
                fig_acumulado.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_acumulado, use_container_width=True, theme="streamlit")

                st.markdown('<hr class="hide-on-print">', unsafe_allow_html=True)
                
                # --- GRÁFICO FULL-WIDTH: EFICIÊNCIA ---
                st.subheader("🛒 Eficiência: Ticket Médio vs P.A")
                df_eficiencia = df_filtrado.groupby('Loja').agg({'Ticket_Medio': 'mean', 'PA': 'mean'}).reset_index()
                fig_scatter = px.scatter(df_eficiencia, x='Ticket_Medio', y='PA', text='Loja', size='Ticket_Medio', color='Loja')
                fig_scatter.update_traces(textposition='top center')
                st.plotly_chart(fig_scatter, use_container_width=True, theme="streamlit")

                # =========================================================================
                # --- SEÇÃO DE RANKING (PÁGINA 3 NO PDF) ---
                # =========================================================================
                
                # Preparando os Dados
                df_base = df_filtrado[['Data_String', 'Loja', 'Venda_Liquida', 'Ticket_Medio', 'PA', 'Clientes']].rename(columns={'Data_String': 'Data'})
                df_top10 = df_base.nlargest(10, 'Venda_Liquida').copy()
                df_bottom10 = df_base.nsmallest(10, 'Venda_Liquida').copy()

                for d in [df_top10, df_bottom10]:
                    d['Venda_Liquida'] = d['Venda_Liquida'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    d['Ticket_Medio'] = d['Ticket_Medio'].apply(lambda x: f"R$ {x:,.2f}".replace('.', ','))
                    d['PA'] = d['PA'].apply(lambda x: f"{x:.1f}")

                # --- EXIBIÇÃO NA TELA (Invisível no PDF) ---
                st.markdown('<hr class="hide-on-print">', unsafe_allow_html=True)
                st.markdown('<h3 class="hide-on-print" style="padding-bottom: 1rem; color: #00d48a; font-family: \'Helvetica Neue\', sans-serif; font-weight: 700;">📋 Ranking Consolidado: Extremos de Faturamento Diário</h3>', unsafe_allow_html=True)
                
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.markdown("<h4 class='hide-on-print' style='color: #00d48a; margin-bottom: 10px; font-size: 1.1rem;'>🏆 Dias de Maior Faturamento (Picos)</h4>", unsafe_allow_html=True)
                    st.dataframe(df_top10, use_container_width=True, hide_index=True)
                with col_t2:
                    st.markdown("<h4 class='hide-on-print' style='color: #f72585; margin-bottom: 10px; font-size: 1.1rem;'>⚠️ Dias de Menor Faturamento (Vales)</h4>", unsafe_allow_html=True)
                    st.dataframe(df_bottom10, use_container_width=True, hide_index=True)

                # --- EXIBIÇÃO NO PDF (Bloco Compacto Forçado na Pág 3) ---
                html_top = df_top10.to_html(index=False, classes="tabela-pdf")
                html_bottom = df_bottom10.to_html(index=False, classes="tabela-pdf")
                
                html_final_pdf = f"""
                <div class="print-only" style="page-break-before: always;">
                    <h3 style="color: #000000; margin-bottom: 20px; font-family: 'Helvetica Neue', sans-serif; font-size: 1.5rem; font-weight: 600;">📋 Ranking Consolidado: Extremos de Faturamento Diário</h3>
                    <div style="display: flex; gap: 20px;">
                        <div style="flex: 1; min-width: 0;">
                            <h4 style="color: #00d48a; margin-bottom: 10px; font-size: 1rem;">🏆 Dias de Maior Faturamento (Picos)</h4>
                            {html_top}
                        </div>
                        <div style="flex: 1; min-width: 0;">
                            <h4 style="color: #f72585; margin-bottom: 10px; font-size: 1rem;">⚠️ Dias de Menor Faturamento (Vales)</h4>
                            {html_bottom}
                        </div>
                    </div>
                    <p style="font-size: 0.8rem; color: #666; margin-top: 5px;">* Exibindo ranking filtrado por Venda Líquida acumulada.</p>
                </div>
                """
                st.markdown(html_final_pdf, unsafe_allow_html=True)

        else:
            st.markdown("""
                <div class="welcome-msg">
                    <h2>Bem-vindo ao Sistema de Inteligência 🚀</h2>
                    <p>O seu painel está conectado à nuvem.<br>
                    Insira as credenciais no menu lateral esquerdo para sincronizar com o Google Drive.</p>
                </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # MÓDULO 2: INTELIGÊNCIA DE TABLOIDES (YoY & MoM)
    # ==========================================
    elif modulo_selecionado == "🔥 Inteligência de Tabloides":
        st.title("🔥 Inteligência Promocional")
        st.subheader("Análise de Efetividade: Ano Anterior (YoY) vs Mês Anterior (MoM)")

        url_tabloides = st.secrets.get("URL_TABLOIDES", "") 

        if not url_tabloides:
            st.warning("⚠️ Adicione a 'URL_TABLOIDES' no seu arquivo secrets do Streamlit.")
        else:
            with st.spinner("Conectando ao banco de dados de tabloides..."):
                try:
                    # Usa o Cérebro de Memória (Cache) para carregar a planilha apenas 1 vez
                    secrets_dict = dict(st.secrets["gcp_service_account"])
                    df_tab = carregar_dados_tabloides(url_tabloides, secrets_dict)

                    if df_tab.empty:
                        st.info("Nenhum dado de tabloide encontrado ou colunas vazias.")
                        st.stop()

                    # ----------------------------------------------------
                    # FUNÇÃO PARA LIMPAR MOEDA E PERCENTUAL DO GOOGLE SHEETS
                    # ----------------------------------------------------
                    def limpar_numerico(coluna, is_percentage=False):
                        s = df_tab[coluna].astype(str).str.replace('R$', '', regex=False)
                        s = s.str.replace('%', '', regex=False).str.replace('.', '', regex=False)
                        s = s.str.replace(',', '.', regex=False).str.strip()
                        valores = pd.to_numeric(s, errors='coerce').fillna(0.0)
                        if is_percentage:
                            return valores / 100.0
                        return valores

                    # Convertendo colunas críticas para números reais no Python
                    df_tab['QTD_MES_ANT'] = limpar_numerico('QTD VENDIDA (Mês Anterior)')
                    df_tab['QTD_ATUAL'] = limpar_numerico('QTD VENDIDA (Tabloide Atual)')
                    df_tab['QTD_ANO_ANT'] = limpar_numerico('QTD VENDIDA (Ano Anterior)')
                    
                    df_tab['FAT_ANO_ANT'] = limpar_numerico('VENDA BRUTA (Ano Anterior)')
                    df_tab['FAT_MES_ANT'] = limpar_numerico('VENDA BRUTA (Mês Anterior)')
                    df_tab['FAT_ATUAL'] = limpar_numerico('VENDA BRUTA (Tabloide Atual)')
                    df_tab['P_POR'] = limpar_numerico('PREÇO "POR"')

                    # ----------------------------------------------------
                    # FILTROS DINÂMICOS NA TELA
                    # ----------------------------------------------------
                    st.markdown("### 🎯 Parâmetros de Análise")
                    col_f1, col_f2 = st.columns(2)
                    
                    with col_f1:
                        lista_tabloides = sorted(df_tab['TABLOIDE'].unique().tolist())
                        tab_selecionado = st.selectbox("Selecione a Campanha:", lista_tabloides)
                        
                    with col_f2:
                        lista_lojas = ['Visão Geral (Rede)'] + sorted(df_tab['LOJA'].unique().tolist())
                        loja_selecionada = st.selectbox("Filtrar por Unidade:", lista_lojas)

                    # Aplicando os filtros no DataFrame do dashboard
                    df_filtrado = df_tab[df_tab['TABLOIDE'] == tab_selecionado]
                    if loja_selecionada != 'Visão Geral (Rede)':
                        df_filtrado = df_filtrado[df_filtrado['LOJA'] == loja_selecionada]

                    # ----------------------------------------------------
                    # CÁLCULO DOS METRIC CARDS (KPIs GERAIS)
                    # ----------------------------------------------------
                    total_fat_atual = df_filtrado['FAT_ATUAL'].sum()
                    total_fat_mes_ant = df_filtrado['FAT_MES_ANT'].sum()
                    total_fat_ano_ant = df_filtrado['FAT_ANO_ANT'].sum()

                    total_qtd_atual = df_filtrado['QTD_ATUAL'].sum()
                    total_qtd_mes_ant = df_filtrado['QTD_MES_ANT'].sum()
                    total_qtd_ano_ant = df_filtrado['QTD_ANO_ANT'].sum()

                    # Cálculos de crescimento macro (Rede ou Loja)
                    cres_fat_yoy = (total_fat_atual / total_fat_ano_ant - 1) if total_fat_ano_ant > 0 else 0.0
                    cres_fat_mom = (total_fat_atual / total_fat_mes_ant - 1) if total_fat_mes_ant > 0 else 0.0
                    
                    cres_qtd_yoy = (total_qtd_atual / total_qtd_ano_ant - 1) if total_qtd_ano_ant > 0 else 0.0
                    cres_qtd_mom = (total_qtd_atual / total_qtd_mes_ant - 1) if total_qtd_mes_ant > 0 else 0.0

                    st.markdown("---")
                    st.markdown(f"## 📊 Desempenho Consolidado: {tab_selecionado}")
                    
                    # Primeira Linha de Cards: Faturamento
                    st.markdown("#### 💰 Desempenho Financeiro (Faturamento)")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Faturamento Atual", f"R$ {total_fat_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    c2.metric("Crescimento YoY (vs Ano Ant.)", f"{cres_fat_yoy*100:+.2f}%", delta=f"{cres_fat_yoy*100:+.2f}%")
                    c3.metric("Crescimento MoM (vs Mês Ant.)", f"{cres_fat_mom*100:+.2f}%", delta=f"{cres_fat_mom*100:+.2f}%")

                    # Segunda Linha de Cards: Volume
                    st.markdown("#### 📦 Desempenho Operacional (Volume de Peças)")
                    c4, c5, c6 = st.columns(3)
                    c4.metric("Total Itens Vendidos", f"{int(total_qtd_atual):,}".replace(',', '.'))
                    c5.metric("Uplift YoY (Volume)", f"{cres_qtd_yoy*100:+.2f}%", delta=f"{cres_qtd_yoy*100:+.2f}%")
                    c6.metric("Uplift MoM (Volume)", f"{cres_qtd_mom*100:+.2f}%", delta=f"{cres_qtd_mom*100:+.2f}%")

                    # ----------------------------------------------------
                    # VISUALIZAÇÕES E GRÁFICOS
                    # ----------------------------------------------------
                    st.markdown("---")
                    col_g1, col_g2 = st.columns(2)

                    with col_g1:
                        st.markdown("#### 🏆 Top 5 Categorias Mais Vendidas (R$)")
                        cat_chart = df_filtrado.groupby('CATEGORIA')['FAT_ATUAL'].sum().reset_index()
                        cat_chart = cat_chart.sort_values(by='FAT_ATUAL', ascending=False).head(5)
                        st.bar_chart(data=cat_chart, x='CATEGORIA', y='FAT_ATUAL', use_container_width=True)

                    with col_g2:
                        st.markdown("#### 🚀 Maiores Crescimentos de Faturamento YoY")
                        
                        # 1. Agrupar por SKU para evitar duplicidade na Visão Geral (Soma todas as lojas)
                        df_agrupado = df_filtrado.groupby(['SKU', 'DESCRIÇÃO'])[['FAT_ATUAL', 'FAT_ANO_ANT']].sum().reset_index()
                        
                        # 2. Filtra itens com histórico para não distorcer com 100% infinitos
                        df_prod_growth = df_agrupado[df_agrupado['FAT_ANO_ANT'] > 50].copy()
                        
                        # 3. Calcula o crescimento matemático bruto
                        df_prod_growth['Crescimento_Bruto'] = ((df_prod_growth['FAT_ATUAL'] / df_prod_growth['FAT_ANO_ANT']) - 1) * 100
                        
                        # 4. Ordena e pega os top 5
                        top_produtos = df_prod_growth.sort_values(by='Crescimento_Bruto', ascending=False).head(5)
                        
                        if not top_produtos.empty:
                            # 5. Formata os números para o padrão Brasileiro na tela final
                            top_produtos['🔥 Cresc. YoY (%)'] = top_produtos['Crescimento_Bruto'].apply(
                                lambda x: f"{x:,.2f}%".replace(',', 'X').replace('.', ',').replace('X', '.')
                            )
                            
                            st.dataframe(
                                top_produtos[['SKU', 'DESCRIÇÃO', '🔥 Cresc. YoY (%)']], 
                                hide_index=True, 
                                use_container_width=True
                            )
                        else:
                            st.caption("Dados históricos insuficientes nesta seleção para gerar o ranking de produtos.")

                    # ----------------------------------------------------
                    # TABELA DETALHADA COM OS DADOS FIÉIS DA PLANILHA
                    # ----------------------------------------------------
                    st.markdown("---")
                    st.markdown("### 🔍 Visão Aberta por SKU (Auditoria Comercial)")
                    
                    # Mantém as colunas originais formatadas para exibição final limpa
                    colunas_exibicao = [
                        'LOJA', 'SKU', 'DESCRIÇÃO', 'CATEGORIA', 'PREÇO "POR"', 
                        'QTD VENDIDA (Ano Anterior)', 'QTD VENDIDA (Mês Anterior)', 'QTD VENDIDA (Tabloide Atual)',
                        'CRES. VOLUME YoY', 'CRES. VOLUME MoM',
                        'VENDA BRUTA (Ano Anterior)', 'VENDA BRUTA (Mês Anterior)', 'VENDA BRUTA (Tabloide Atual)'
                    ]
                    
                    st.dataframe(df_filtrado[colunas_exibicao], use_container_width=True, hide_index=True)

                except Exception as e:
                    st.error(f"Erro ao processar o Dashboard de Tabloides: {e}")

    # --- ASSINATURA INFERIOR DO MENU LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="text-align: center; color: #888; font-size: 0.75rem;">
            <b>Vision Sale v1.9</b><br>
            Automatizado por: <b>Marciel Oliveira</b><br>
            <i>Transformando dados em clareza.</i>
        </div>
        """, 
        unsafe_allow_html=True
    )
