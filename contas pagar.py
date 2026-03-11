import streamlit as st
import pandas as pd
import numpy as np

# 1. Configuração de Página e Estilo Dark Premium
st.set_page_config(page_title="CASH FLOW PROJECT - ACCOUNTS PAYABLE", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0E1117; }
    
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 20px;
    }
    div[data-testid="stMetricValue"] { color: #38bdf8; font-weight: 700; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 10px 10px 0px 0px;
        color: white;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #000 !important; }
    
    .stButton>button {
        background: linear-gradient(90deg, #d946ef, #a21caf); border: none; color: white;
        border-radius: 12px; font-weight: bold; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Dicionário de Mapeamento de Grupos e Categorias
MAPA_GRUPOS = {
    "Administrativo": ["ALUGUEL", "COMPRA DE ATIVO FIXO", "CONDOMÍNIO", "COWORKING", "CUSTO OPERACIONAL", "DESPESAS FINANCEIRAS", "ENERGIA ELÉTRICA", "ESTORNO", "EVENTOS FUNCIONÁRIOS", "Juros Pagos", "MANUTENÇÃO ESCRITÓRIO", "MATERIAIS DE TI", "MATERIAL DE COPA", "MATERIAL DE ESCRITÓRIO", "MATERIAL DE LIMPEZA", "Multas Pagas", "Não classificado", "OUTRAS DESPESAS", "PAGAMENTO DE EMPRÉSTIMO", "REPRESENTAÇÃO", "SEGUROS", "SERVIÇOS CONTÁBEIS", "SERVIÇOS CONTRATADOS", "SERVIÇOS DE E-MAIL", "SERVIÇOS DE ENTREGA", "SERVIÇOS DE PUBLICIDADE", "SERVIÇOS JURÍDICOS", "SERVIÇOS TI", "SISTEMAS", "TAXAS E CONTRIBUIÇÕES", "TELEFONIA/INTERNET", "TREINAMENTOS", "VAGAS GARAGEM - SÓCIOS"],
    "Despesa de pessoal": ["13º SALÁRIO", "ADIANTAMENTO AO FUNCIONÁRIO", "ANTECIPAÇÃO DE RESULTADOS", "ASSISTÊNCIA MÉDICA", "ASSISTÊNCIA ODONTO", "BÔNUS CLT", "BÔNUS PERFORMANCE - G", "CONSULTORIA ESPECIALIZADA - G", "CONSULTORIA ESPECIALIZADA - TI", "DESPESA EVENTUAL DE PESSOAL", "DESPESAS VIAGEM", "ESTAGIÁRIO FOLHA", "EXAMES OCUPACIONAIS", "FÉRIAS", "FGTS", "GRATIFICAÇÕES CLT", "GRATIFICAÇÕES PJ - G", "INSS", "IRRF", "LOCOMOÇÃO", "MATERIAL DE COPA", "Multas Pagas", "PRO LABORE", "REPRESENTAÇÃO", "RESCISÃO", "SALÁRIOS CLT", "SEGURO DE VIDA", "SERVIÇOS CONTRATADOS", "VA/VR", "VT"],
    "Operacional": ["BÔNUS - TERCEIROS", "COMISSÕES SEGUROS", "CUSTO OPERACIONAL", "Descontos Recebidos", "EVENTOS CLIENTES", "Multas Pagas", "REBATE COMISSÕES", "REPRESENTAÇÃO"],
    "Tributário": ["COFINS", "COFINS Retido sobre Pagamentos", "CSLL", "CSLL Retido sobre Pagamentos", "DESPESAS FINANCEIRAS", "ESTORNO", "INSS Retido sobre Pagamentos", "IPTU", "IRPJ", "IRPJ Retido sobre Pagamentos", "ISS", "ISS Retido sobre Pagamentos", "Juros Pagos", "Multas Pagas", "Pagamento de ISS Retido", "PARCELAMENTO RECEITA FEDERAL", "PERT CSLL", "PERT IRPJ", "PERT IRRF", "PERT SN", "PIS", "PIS Retido sobre Pagamentos", "SERVIÇOS DE PUBLICIDADE"]
}

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

    c1, c2 = st.columns([4, 1])
    with c1:
        st.title("💎 CASH FLOW PROJECT - ACCOUNTS PAYABLE")
    with c2:
        if st.button("🔄 Sincronizar Dados"):
            st.cache_data.clear()
            st.rerun()

    # --- SEÇÃO DE FILTROS ---
    lista_meses = sorted(df_raw['Mes_Ano'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))
    
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        meses_sel = st.multiselect("📅 Períodos:", options=lista_meses, default=lista_meses)
    with f2:
        grupos_sel = st.multiselect("📂 Grupos:", options=list(MAPA_GRUPOS.keys()), default=list(MAPA_GRUPOS.keys()))
    with f3:
        # Categorias filtradas de acordo com os grupos escolhidos
        cats_possiveis = []
        for g in grupos_sel:
            cats_possiveis.extend(MAPA_GRUPOS[g])
        cats_possiveis = sorted(list(set(cats_possiveis))) # Remove duplicatas entre grupos
        cats_sel = st.multiselect("🏷️ Categorias:", options=cats_possiveis, default=cats_possiveis)

    # Aplicação Cascata dos Filtros
    df = df_raw.copy()
    if meses_sel:
        df = df[df['Mes_Ano'].isin(meses_sel)]
    if cats_sel:
        df = df[df['Categoria'].isin(cats_sel)]

    st.write("---")

    # 3. Métricas Dinâmicas
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

    tab_proj, tab_burn, tab_pareto, tab_tax, tab_raw = st.tabs([
        "📊 Projeção Mensal", "🔥 Cash Burn Diário", "🎯 Pareto (80/20)", "🏛️ Fiscal vs Op", "📋 Dados Brutos"
    ])

    with tab_proj:
        st.subheader("Análise Evolutiva: Histórico Mês a Mês")
        # Aqui ele agrupa os dados já filtrados por categoria/grupo
        proj_mensal = df[df[col_v] < 0].groupby('Periodo_Sort')[col_v].sum().abs().reset_index()
        proj_mensal['Mês/Ano'] = proj_mensal['Periodo_Sort'].astype(str)
        
        cp1, cp2 = st.columns([2, 1])
        with cp1:
            if not proj_mensal.empty:
                st.bar_chart(proj_mensal.set_index('Mês/Ano')[col_v], color="#38bdf8")
            else:
                st.info("Ajuste os filtros para visualizar o gráfico.")
        with cp2:
            st.markdown("### Totais por Período")
            st.dataframe(
                proj_mensal[['Mês/Ano', col_v]].style.format({col_v: "R$ {:,.2f}"}),
                hide_index=True, use_container_width=True
            )

    with tab_burn:
        st.subheader("Evolução do Consumo de Caixa (Acumulado)")
        if not df.empty:
            burn_df = df.groupby('Data de pagamento')[col_v].sum().cumsum().reset_index()
            st.area_chart(burn_df.set_index('Data de pagamento'), color="#f43f5e")
        else:
            st.warning("Sem dados para os filtros selecionados.")

    with tab_pareto:
        st.subheader("Análise de Pareto: Maiores Saídas")
        saidas_somente = df[df[col_v] < 0]
        if not saidas_somente.empty:
            resumo_cat = saidas_somente.groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False).reset_index()
            resumo_cat['% Acumulado'] = (resumo_cat[col_v].cumsum() / resumo_cat[col_v].sum()) * 100
            pareto_df = resumo_cat[resumo_cat['% Acumulado'] <= 90] 
            c_p1, c_p2 = st.columns([1, 2])
            with c_p1:
                st.dataframe(pareto_df[['Categoria', col_v]].style.format({col_v: "R$ {:,.2f}"}), hide_index=True, use_container_width=True)
            with c_p2:
                st.bar_chart(pareto_df.set_index('Categoria')[col_v], color="#38bdf8")

    with tab_tax:
        st.subheader("Distribuição por Natureza")
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            dist_tipo = df.groupby('Tipo')[col_v].sum().abs()
            if not dist_tipo.empty: st.bar_chart(dist_tipo, color="#a21caf")
        with c_t2:
            st.dataframe(
                df[df['Tipo'] == 'Imposto/Retenção'][['Data de pagamento', 'Categoria', col_v]].style.format({col_v: "R$ {:,.2f}"}),
                hide_index=True, use_container_width=True
            )

    with tab_raw:
        st.subheader("Explorador Geral")
        busca = st.text_input("Filtrar por texto livre na categoria...", key="search_raw")
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
