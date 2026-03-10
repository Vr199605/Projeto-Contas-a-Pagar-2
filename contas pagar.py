import streamlit as st
import pandas as pd
import numpy as np

# 1. Configuração de Página e Estilo Dark Premium
st.set_page_config(page_title="CASH FLOW PROJECT - ACCOUNTS PAYABLE", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0E1117; }
    
    /* Cards de Métricas */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 20px;
    }
    div[data-testid="stMetricValue"] { color: #38bdf8; font-weight: 700; }
    
    /* Abas Customizadas */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 10px 10px 0px 0px;
        color: white;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #000 !important; }
    
    /* Botão Sincronizar */
    .stButton>button {
        background: linear-gradient(90deg, #d946ef, #a21caf); border: none; color: white;
        border-radius: 12px; font-weight: bold; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# Função auxiliar para formatar moeda em texto (BR)
def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# 2. Motor de Processamento de Dados
@st.cache_data(ttl=600)
def load_and_process():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?output=csv"
    df = pd.read_csv(url)
    
    def clean_val(v):
        if isinstance(v, str):
            v = v.replace('R$', '').replace('.', '').replace(' ', '').replace(',', '.')
            try: return float(v)
            except: return 0.0
        return v

    col_v = 'Valor categoria/centro de custo'
    df[col_v] = df[col_v].apply(clean_val)
    df['Data de pagamento'] = pd.to_datetime(df['Data de pagamento'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Data de pagamento']).sort_values('Data de pagamento')

    # Criar colunas de período
    df['Mes_Ano'] = df['Data de pagamento'].dt.strftime('%m/%Y')
    df['Periodo_Sort'] = df['Data de pagamento'].dt.to_period('M')

    keywords_imposto = ['ISS', 'IRPJ', 'CSLL', 'PIS', 'COFINS', 'RETIDO', 'IMPOSTO', 'TAXA', 'DARF']
    df['Tipo'] = df['Categoria'].apply(
        lambda x: 'Imposto/Retenção' if any(k in str(x).upper() for k in keywords_imposto) else 'Operacional'
    )
    
    return df

try:
    df_raw = load_and_process()
    col_v = 'Valor categoria/centro de custo'

    # Header Superior
    c1, c2 = st.columns([4, 1])
    with c1:
        st.title("💎 CFO Intelligence: Strategic View")
    with c2:
        if st.button("🔄 Sincronizar Dados"):
            st.cache_data.clear()
            st.rerun()

    # Filtro de Mês no Corpo da Página (Melhor UX)
    lista_meses = sorted(df_raw['Mes_Ano'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))
    lista_meses.insert(0, "Todos os Meses")
    
    f1, f2 = st.columns([1, 3])
    with f1:
        mes_selecionado = st.selectbox("📅 Filtrar Período:", lista_meses)

    if mes_selecionado != "Todos os Meses":
        df = df_raw[df_raw['Mes_Ano'] == mes_selecionado].copy()
    else:
        df = df_raw.copy()

    st.write("---")

    # 3. Métricas de Alto Impacto
    saidas_totais = df[df[col_v] < 0][col_v].sum()
    impostos_totais = df[df['Tipo'] == 'Imposto/Retenção'][col_v].sum()
    operacional_puro = df[df['Tipo'] == 'Operacional'][col_v].sum()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cash Out Total", format_brl(abs(saidas_totais)))
    tax_perc = abs(impostos_totais/saidas_totais)*100 if saidas_totais != 0 else 0
    m2.metric("Carga Tributária", format_brl(abs(impostos_totais)), f"{tax_perc:.1f}% do total")
    m3.metric("Custos Operacionais", format_brl(abs(operacional_puro)))
    m4.metric("Aging (Lançamentos)", len(df))

    st.write("##")

    # 4. Sistema de Abas Estratégicas
    tab_proj, tab_burn, tab_pareto, tab_tax, tab_raw = st.tabs([
        "📊 Projeção Mensal", "🔥 Cash Burn Diário", "🎯 Pareto (80/20)", "🏛️ Fiscal vs Op", "📋 Dados Brutos"
    ])

    # ABA: PROJEÇÃO MENSAL
    with tab_proj:
        st.subheader("Análise Evolutiva: Histórico Mês a Mês")
        # Agrupamento da base completa para ver a evolução
        proj_mensal = df_raw[df_raw[col_v] < 0].groupby('Periodo_Sort')[col_v].sum().abs().reset_index()
        proj_mensal['Mês/Ano'] = proj_mensal['Periodo_Sort'].astype(str)
        
        cp1, cp2 = st.columns([2, 1])
        with cp1:
            st.bar_chart(proj_mensal.set_index('Mês/Ano')[col_v], color="#38bdf8")
        with cp2:
            st.markdown("### Totais por Período")
            # Exibição com formatação de moeda na tabela
            st.dataframe(
                proj_mensal[['Mês/Ano', col_v]].style.format({col_v: "R$ {:,.2f}"}),
                hide_index=True,
                use_container_width=True
            )

    # ABA: CASH BURN
    with tab_burn:
        st.subheader("Evolução do Consumo de Caixa (Acumulado)")
        if not df.empty:
            burn_df = df.groupby('Data de pagamento')[col_v].sum().cumsum().reset_index()
            st.area_chart(burn_df.set_index('Data de pagamento'), color="#f43f5e")
        else:
            st.warning("Sem dados para o período.")

    # ABA: PARETO
    with tab_pareto:
        st.subheader("Análise de Pareto: Maiores Saídas")
        saidas_somente = df[df[col_v] < 0]
        if not saidas_somente.empty:
            resumo_cat = saidas_somente.groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False).reset_index()
            resumo_cat['% Acumulado'] = (resumo_cat[col_v].cumsum() / resumo_cat[col_v].sum()) * 100
            pareto_df = resumo_cat[resumo_cat['% Acumulado'] <= 90] 
            
            c_p1, c_p2 = st.columns([1, 2])
            with c_p1:
                st.dataframe(
                    pareto_df[['Categoria', col_v]].style.format({col_v: "R$ {:,.2f}"}),
                    hide_index=True, use_container_width=True
                )
            with c_p2:
                st.bar_chart(pareto_df.set_index('Categoria')[col_v], color="#38bdf8")

    # ABA: FISCAL VS OPERAÇÃO
    with tab_tax:
        st.subheader("Distribuição por Natureza")
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            dist_tipo = df.groupby('Tipo')[col_v].sum().abs()
            st.bar_chart(dist_tipo, color="#a21caf")
        with c_t2:
            st.dataframe(
                df[df['Tipo'] == 'Imposto/Retenção'][['Data de pagamento', 'Categoria', col_v]].style.format({col_v: "R$ {:,.2f}"}),
                hide_index=True, use_container_width=True
            )

    # ABA: DADOS BRUTOS
    with tab_raw:
        st.subheader("Explorador Geral")
        busca = st.text_input("Filtrar por conta ou categoria...", key="search_raw")
        df_final = df[df['Categoria'].astype(str).str.contains(busca, case=False)]
        
        st.data_editor(
            df_final,
            column_config={
                col_v: st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "Data de pagamento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
            },
            hide_index=True, use_container_width=True
        )

except Exception as e:
    st.error(f"Erro ao carregar dashboard: {e}")

