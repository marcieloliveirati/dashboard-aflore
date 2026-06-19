import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta, date
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Aflore - Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# --- SISTEMA DE SEGURANÇA E LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False

# Tela de Login (A Sala de Espera)
if not st.session_state.logado:
    st.markdown("""
        <style>
            .main { background-color: #0f1116; color: #ffffff; }
        </style>
    """, unsafe_allow_html=True)
    
    # Empurra a tela inteira um pouco para baixo para ficar bem no meio do monitor
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # Truque das Colunas: Uma coluna grande vazia na esquerda, a do meio para o login, e uma grande na direita
    _, col_login, _ = st.columns([1, 1.2, 1])
    
    with col_login:
        # Envelopando os inputs em um Form: Isso cria a função "Apertar Enter para enviar"
        with st.form("form_login", clear_on_submit=False):
            
            # Centraliza a imagem da Aflore dentro do box de login
            col_img1, col_img2, col_img3 = st.columns([1, 1.5, 1])
            with col_img2:
                if os.path.exists("logo_aflore.png"):
                    st.image("logo_aflore.png", use_container_width=True)
                elif os.path.exists("logo.png"):
                    st.image("logo.png", use_container_width=True)
                else:
                    st.markdown("<h3 style='text-align: center; color: #00d48a;'>AFLORE DIGITAL</h3>", unsafe_allow_html=True)
                    
            st.markdown("<h4 style='text-align: center; color: #555; margin-bottom: 20px;'>Acesso Restrito</h4>", unsafe_allow_html=True)
            
            usuario = st.text_input("👤 Usuário")
            senha = st.text_input("🔑 Senha", type="password")
            
            # Botão de Entrar (Agora ele obedece ao Enter porque está dentro do st.form)
            submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                # Dicionário de Acessos Provisório
                usuarios_permitidos = {
                    "diretoria": "aflore2026",
                    "admin": "123789123@@"
                }
                
                if usuario in usuarios_permitidos and usuarios_permitidos[usuario] == senha:
                    st.session_state.logado = True
                    st.rerun() # Libera o acesso
                else:
                    st.error("❌ Usuário ou senha incorretos.")

# A Sala de Comando (O Dashboard) - Só roda se o login for True
else:
    # --- ESTILOS DO DASHBOARD ---
    st.markdown("""
        <style>
            .main { background-color: #0f1116; color: #ffffff; }
            .stMetric { background-color: #1b1e26; padding: 15px; border-radius: 10px; border-left: 5px solid #00d48a; }
            div[data-testid="stSidebarUserContent"] { background-color: #11141c; }
            .stHeading h1 { color: #00d48a; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
            .stHeading h2 { color: #00b4d8; }
            .stHeading h3 { color: #f72585; }
            .welcome-msg { text-align: center; color: #555; margin-top: 100px; font-size: 1.2rem; }
            
            [data-testid="stFileUploader"] label { display: flex; justify-content: center; }
            [data-testid="stFileUploader"] section { align-items: center !important; text-align: center; }
            
            [data-testid="stSidebarUserContent"] h3 { text-align: center; }
            [data-testid="stRadio"] > label { display: flex; justify-content: center; }
            [data-testid="stRadio"] div[role="radiogroup"] { width: fit-content; margin: 0 auto; }
        </style>
    """, unsafe_allow_html=True)

    col_titulo, col_sair = st.columns([8, 1])
    with col_titulo:
        st.title("📊 Vision Sale - Inteligência de Vendas")
        st.subheader("Painel Analítico de Desempenho de Lojas")
    with col_sair:
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.rerun()

    # --- MENU LATERAL (SIDEBAR) ---
    if os.path.exists("logo_aflore.png"):
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        with col2:
            st.image("logo_aflore.png", use_container_width=True)
    elif os.path.exists("logo.png"):
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        with col2:
            st.image("logo.png", use_container_width=True)
    else:
        st.sidebar.markdown("<h2 style='text-align: center; color: #00d48a;'>AFLORE DIGITAL</h2>", unsafe_allow_html=True)
        
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    uploaded_file = st.sidebar.file_uploader("📂 Importar Planilha de Vendas (Excel)", type=["xlsx", "xls"])

# --- MOTORES DE LIMPEZA E TRADUÇÃO ---
    def clean_numeric(val):
        if pd.isna(val) or str(val).strip() in ['#VALOR!', '-', '']: return 0.0
        if isinstance(val, (int, float)): return float(val)
        
        val_str = str(val).replace('R$', '').strip()
        
        # Se a pessoa digitou com ponto (32.75) e não tem vírgula, o Python entende nativamente
        if '.' in val_str and ',' not in val_str:
            try: return float(val_str)
            except: pass
            
        # Se está no padrão correto brasileiro (3.200,50 ou 32,75)
        try: return float(val_str.replace('.', '').replace(',', '.'))
        except: return 0.0

    def parse_data(val):
        if pd.isna(val): return pd.NaT
        if isinstance(val, (datetime, date)): return val.date() if isinstance(val, datetime) else val
        val_str = str(val).strip().lower()
        try: return pd.to_datetime(val_str).date()
        except: pass
        try:
            partes = val_str.split('/')
            if len(partes) >= 2:
                dia = int(partes[0][:2])
                mes_texto = partes[1][:3]
                meses_map = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12}
                mes = meses_map.get(mes_texto, 6)
                return date(date.today().year, mes, dia)
        except: pass
        return pd.NaT

    df = pd.DataFrame()

    # --- MOTOR DE LEITURA DO EXCEL ---
    if uploaded_file is not None:
        try:
            df_raw = pd.read_excel(uploaded_file, header=None)
            metas_lojas = {'Loja 01': 1830000, 'Loja 02': 610000, 'Loja 03': 220000, 'Loja 04': 305100, 'Loja 05': 10000}
            
            idx_cabecalho = -1
            for i in range(5):
                valores_linha = [str(val).strip().upper() for val in df_raw.iloc[i].values]
                if 'V.L' in valores_linha or 'V.L.' in valores_linha:
                    idx_cabecalho = i
                    break
                    
            if idx_cabecalho >= 0:
                headers = [str(val).strip().upper() for val in df_raw.iloc[idx_cabecalho].values]
                vl_indices = [i for i, h in enumerate(headers) if 'V.L' in h]
                nomes_lojas = ['Loja 01', 'Loja 02', 'Loja 03', 'Loja 04', 'Loja 05']
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
                            
                            if pd.isna(val_data_crua) or 'TOTAL' in str_data_check or 'META' in str_data_check or str_data_check in ('', 'NAN', 'NAT'):
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
                                    'Meta_Total_Loja': metas_lojas.get(nome_loja, 0)
                                })
                        except Exception: pass
                
                df = pd.DataFrame(all_data)
                
                if not df.empty:
                    df['Data_Real'] = df['Data_Raw'].apply(parse_data)
                    df = df.dropna(subset=['Data_Real']) 
                    df['Data_String'] = df['Data_Real'].apply(lambda d: d.strftime("%d/%m"))
                
            if df.empty:
                st.sidebar.warning("⚠️ Planilha lida, mas sem dados válidos encontrados.")
            else:
                st.sidebar.success("✅ Planilha processada com sucesso!")
                
        except Exception as e:
            st.sidebar.error("❌ Arquivo inválido ou corrompido.")
    else:
        st.sidebar.info("💡 Suba a planilha real para processar os números da operação.")

    # --- CAMADA DE VISUALIZAÇÃO E FILTROS ---
    if not df.empty and 'Loja' in df.columns:
        
        lista_lojas = ['Todas as Lojas'] + list(df['Loja'].unique())
        loja_selecionada = st.selectbox("🏪 Selecione a Unidade:", lista_lojas)

        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 Filtro de Período")
        opcao_data = st.sidebar.radio(
            "Selecione o período de análise:", 
            ["Todo o Período", "Hoje", "Ontem", "Últimos 7 Dias", "Personalizado"]
        )

        hoje = date.today()
        df_filtrado = df.copy()

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

            dias_no_filtro = df_filtrado['Data_Real'].nunique()
            dias_totais_planilha = df['Data_Real'].nunique()
            fator_meta = dias_no_filtro / dias_totais_planilha if dias_totais_planilha > 0 else 1

            meta_global_loja = df_filtrado.drop_duplicates(subset=['Loja'])['Meta_Total_Loja'].sum() if loja_selecionada == 'Todas as Lojas' else df_filtrado['Meta_Total_Loja'].iloc[0]
            meta_proporcional = meta_global_loja * fator_meta
            
            percentual_meta = (total_faturamento / meta_proporcional) * 100 if meta_proporcional > 0 else 0

            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
            with kpi1: st.metric("💰 Faturamento Total", f"R$ {total_faturamento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            with kpi2: st.metric("🎯 Atingimento de Meta", f"{percentual_meta:.1f}%")
            with kpi3: st.metric("👥 Total Atendimentos", f"{total_clientes:,}".replace(',', '.'))
            with kpi4: st.metric("🎟️ Ticket Médio Geral", f"R$ {ticket_medio_geral:.2f}".replace('.', ','))
            with kpi5: st.metric("📦 Peças por Atend. (P.A)", f"{pa_medio:.1f}")

            st.markdown("---")

            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.subheader("📈 Tendência Diária de Faturamento")
                df_diario = df_filtrado.groupby('Data_String')['Venda_Liquida'].sum().reset_index()
                fig_linha = px.line(df_diario, x='Data_String', y='Venda_Liquida', labels={'Venda_Liquida': 'Faturamento (R$)', 'Data_String': 'Dia'}, template='plotly_dark', markers=True)
                fig_linha.update_traces(line_color='#00b4d8', line_width=3)
                st.plotly_chart(fig_linha, use_container_width=True)

            with col_dir:
                st.subheader("🏪 Faturamento por Unidade / Loja")
                df_loja_sum = df_filtrado.groupby('Loja')['Venda_Liquida'].sum().reset_index().sort_values(by='Venda_Liquida', ascending=False)
                fig_barra = px.bar(df_loja_sum, x='Loja', y='Venda_Liquida', labels={'Venda_Liquida': 'Faturamento (R$)'}, template='plotly_dark', color='Venda_Liquida', color_continuous_scale='Viridis')
                st.plotly_chart(fig_barra, use_container_width=True)

            st.markdown("---")
            col_infra1, col_infra2 = st.columns(2)
            with col_infra1:
                st.subheader("🛒 Eficiência: Ticket Médio vs P.A")
                df_eficiencia = df_filtrado.groupby('Loja').agg({'Ticket_Medio': 'mean', 'PA': 'mean'}).reset_index()
                fig_scatter = px.scatter(df_eficiencia, x='Ticket_Medio', y='PA', text='Loja', size='Ticket_Medio', color='Loja', template='plotly_dark')
                fig_scatter.update_traces(textposition='top center')
                st.plotly_chart(fig_scatter, use_container_width=True)

            with col_infra2:
                st.subheader("📋 Tabela de Dados Consolidados")
                st.dataframe(df_filtrado[['Data_String', 'Loja', 'Venda_Liquida', 'Ticket_Medio', 'PA', 'Clientes']].rename(columns={'Data_String': 'Data'}), use_container_width=True, height=300)

    else:
        st.markdown("""
            <div class="welcome-msg">
                <h2>Bem-vindo ao Sistema de Inteligência 🚀</h2>
                <p>O seu painel está pronto e aguardando os dados.<br>
                Faça o upload da planilha Excel no menu lateral esquerdo para visualizar os gráficos.</p>
            </div>
        """, unsafe_allow_html=True)