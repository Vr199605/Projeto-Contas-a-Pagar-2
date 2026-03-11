import streamlit as st
import pandas as pd
import numpy as np

# 1. Configuração de Página
st.set_page_config(page_title="CASH FLOW PROJECT", layout="wide", initial_sidebar_state="expanded")

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
    </style>
    """, unsafe_allow_html=True)

def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
    
    def atribuir_grupo(cat):
        for grupo, categorias in MAPA_GRUPOS.items():
            if cat in categorias: return grupo
        return "Outros"
    df['Grupo_Filtro'] = df['Categoria'].apply(atribuir_grupo)
    return df

try:
    df_raw = load_and_process()
    col_v = 'Valor categoria/centro de custo'
    lista_meses = sorted(df_raw['Mes_Ano'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))
    todas_cats = sorted(list(set([c for sub in MAPA_GRUPOS.values() for c in sub])))

    with st.sidebar:
        st.title("⚙️ Filtros")
        if st.button("🔄 Sincronizar Dados", type="primary"):
            st.cache_data.clear()
            st.rerun()
        st.write("---")
        meses_sel = st.multiselect("📅 Períodos:", options=lista_meses, default=lista_meses, key='ms_meses')
        grupos_sel = st.multiselect("📂 Grupos:", options=list(MAPA_GRUPOS.keys()), default=list(MAPA_GRUPOS.keys()), key='ms_grupos')
        
        cats_dinamicas = []
        for g in grupos_sel:
            cats_dinamicas.extend(MAPA_GRUPOS[g])
        cats_dinamicas = sorted(list(set(cats_dinamicas)))
        cats_sel = st.multiselect("🏷️ Categorias:", options=cats_dinamicas, default=cats_dinamicas, key='ms_cats')
        
        if st.button("🧹 Limpar Filtros"):
            st.session_state.ms_meses = lista_meses
            st.session_state.ms_grupos = list(MAPA_GRUPOS.keys())
            st.session_state.ms_cats = todas_cats
            st.rerun()

    # Aplicação dos Filtros
    df = df_raw.copy()
    if meses_sel: df = df[df['Mes_Ano'].isin(meses_sel)]
    if grupos_sel: df = df[df['Grupo_Filtro'].isin(grupos_sel)]
    if cats_sel: df = df[df['Categoria'].isin(cats_sel)]

    st.title("💎 CASH FLOW PROJECT - ACCOUNTS PAYABLE")
    
    # --- MÉTRICAS DINÂMICAS ---
    saidas_only = df[df[col_v] < 0]
    total_geral = saidas_only[col_v].sum()
    cols_metricas = st.columns(len(grupos_sel) + 1)
    with cols_metricas[0]:
        st.metric("Cash Out Total", format_brl(abs(total_geral)))
    for i, grupo in enumerate(grupos_sel):
        valor_grupo = df[df['Grupo_Filtro'] == grupo][col_v].sum()
        with cols_metricas[i+1]:
            st.metric(grupo, format_brl(abs(valor_grupo)))

    st.write("---")

    # --- ABAS ---
    tab_proj, tab_burn, tab_pareto, tab_raw = st.tabs(["📊 Projeção Mensal", "🔥 Cash Burn Diário", "🎯 Pareto (80/20)", "📋 Dados Brutos"])

    with tab_proj:
        st.subheader("📈 Evolução Mensal do Desembolso")
        proj_mensal = saidas_only.groupby('Periodo_Sort')[col_v].sum().abs().reset_index()
        proj_mensal['Mês/Ano'] = proj_mensal['Periodo_Sort'].astype(str)
        st.bar_chart(proj_mensal.set_index('Mês/Ano')[col_v], color="#38bdf8")
        
        c_proj1, c_proj2 = st.columns(2)
        with c_proj1:
            st.subheader("📂 Projeção por Grupo")
            proj_grupo = saidas_only.groupby(['Mês/Ano', 'Grupo_Filtro'])[col_v].sum().abs().unstack().fillna(0)
            st.line_chart(proj_grupo)
            
        with c_proj2:
            st.subheader("🏷️ Projeção por Categoria (Top 5)")
            top_5_cats = saidas_only.groupby('Categoria')[col_v].sum().abs().nlargest(5).index
            proj_cat = saidas_only[saidas_only['Categoria'].isin(top_5_cats)].groupby(['Mês/Ano', 'Categoria'])[col_v].sum().abs().unstack().fillna(0)
            st.line_chart(proj_cat)

    with tab_burn:
        st.subheader("🔥 Queima de Caixa Diária")
        if not saidas_only.empty:
            burn_diario = saidas_only.groupby('Data de pagamento')[col_v].sum().abs().reset_index()
            burn_diario['Acumulado'] = burn_diario[col_v].cumsum()
            st.area_chart(burn_diario.set_index('Data de pagamento')['Acumulado'], color="#f43f5e")

    with tab_pareto:
        st.subheader("🎯 Ranking de Maiores Gastos")
        if not saidas_only.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 📂 Maiores Gastos por Grupo")
                pareto_grupo = saidas_only.groupby('Grupo_Filtro')[col_v].sum().abs().reset_index()
                pareto_grupo.columns = ['Grupo', 'Total Gasto']
                pareto_grupo = pareto_grupo.sort_values('Total Gasto', ascending=False)
                st.dataframe(pareto_grupo.style.format({'Total Gasto': "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
                st.bar_chart(pareto_grupo.set_index('Grupo')['Total Gasto'], color="#f43f5e")

            with c2:
                st.markdown("### 🏷️ Maiores Gastos por Categoria")
                pareto_cat = saidas_only.groupby('Categoria')[col_v].sum().abs().reset_index()
                pareto_cat.columns = ['Categoria', 'Total Gasto']
                pareto_cat = pareto_cat.sort_values('Total Gasto', ascending=False)
                st.dataframe(pareto_cat.style.format({'Total Gasto': "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
                st.bar_chart(pareto_cat.head(10).set_index('Categoria')['Total Gasto'], color="#38bdf8")

    with tab_raw:
        st.subheader("📋 Lista de Lançamentos")
        # Formatando as datas para dd/mm/aaaa no editor de dados
        st.data_editor(
            df, 
            column_config={
                col_v: st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "Data de pagamento": st.column_config.DateColumn("Data de Pagamento", format="DD/MM/YYYY")
            }, 
            use_container_width=True, 
            hide_index=True
        )

except Exception as e:
    st.error(f"Erro: {e}")




