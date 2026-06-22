import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta, date
import os
import streamlit.components.v1 as components

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
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1.2, 1])
    
    with col_login:
        with st.form("form_login", clear_on_submit=False):
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
            
            submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                usuarios_permitidos = {
                    "diretoria": "aflore2026",
                    "admin": "123789123@@"
                }
                
                if usuario in usuarios_permitidos and usuarios_permitidos[usuario] == senha:
                    st.session_state.logado = True
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")

# A Sala de Comando (O Dashboard)
else:
    # --- ESTILOS DO DASHBOARD (Compatível com Tema Claro/Escuro e Impressão PDF) ---
    st.markdown("""
        <style>
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

            /* --- MÁGICA DO PDF / IMPRESSÃO --- */
            @media print {
                section[data-testid="stSidebar"] { display: none !important; }
                header[data-testid="stHeader"] { display: none !important; }
                .btn-imprimir { display: none !important; }
                .main { background-color: white !important; }
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
        if st.button("🖨️ Gerar PDF Executivo", use_container_width=True):
            components.html("<script>window.parent.print();</script>", height=0, width=0)
            
    with col_sair:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
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
        if '.' in val_str and ',' not in val_str:
            try: return float(val_str)
            except: pass
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
                
                # CAPTURA DINÂMICA DE METAS DA PLANILHA
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
                                    'Meta_Faturamento': metas_dinamicas[nome_loja]['vl'],
                                    'Meta_Clientes': metas_dinamicas[nome_loja]['cli'],
                                    'Meta_TMV': metas_dinamicas[nome_loja]['tmv']
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

            # --- FORMATAÇÃO DOS VALORES PARA AS METAS ---
            str_meta_fat = f"R$ {meta_prop_fat:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            str_meta_cli = f"{int(meta_prop_cli):,}".replace(',', '.')
            str_meta_tmv = f"R$ {meta_prop_tmv:,.2f}".replace('.', ',')

            # --- CARDS VISUAIS DE PREVISTO X REALIZADO ---
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

            st.markdown("---")

            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.subheader("📈 Tendência Diária x Meta")
                df_diario = df_filtrado.groupby('Data_String')['Venda_Liquida'].sum().reset_index()
                
                fig_linha = px.line(df_diario, x='Data_String', y='Venda_Liquida', labels={'Venda_Liquida': 'Faturamento (R$)', 'Data_String': 'Dia'}, markers=True)
                fig_linha.update_traces(line_color='#00b4d8', line_width=3, name='Realizado', showlegend=True)
                
                meta_diaria = meta_global_fat / dias_totais_planilha if dias_totais_planilha > 0 else 0
                fig_linha.add_hline(y=meta_diaria, line_dash="dash", line_color="#f72585", annotation_text="Meta Diária", annotation_position="top right", annotation_font_color="#f72585")
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
                                   labels={'Valor': 'Faturamento (R$)', 'Tipo': 'Métrica'})
                
                fig_barra.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_barra, use_container_width=True, theme="streamlit")

            st.markdown("---")
            col_infra1, col_infra2 = st.columns(2)
            with col_infra1:
                st.subheader("🛒 Eficiência: Ticket Médio vs P.A")
                df_eficiencia = df_filtrado.groupby('Loja').agg({'Ticket_Medio': 'mean', 'PA': 'mean'}).reset_index()
                fig_scatter = px.scatter(df_eficiencia, x='Ticket_Medio', y='PA', text='Loja', size='Ticket_Medio', color='Loja')
                fig_scatter.update_traces(textposition='top center')
                st.plotly_chart(fig_scatter, use_container_width=True, theme="streamlit")

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
        
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="text-align: center; color: #888; font-size: 0.75rem;">
            <b>Vision Sale v1.1 2026/06/22</b><br>
            Automatizado por: <b>Marciel Oliveira</b><br>
            <i>Transformando dados em clareza.</i>
        </div>
        """, 
        unsafe_allow_html=True
    )
