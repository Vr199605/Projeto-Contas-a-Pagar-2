import streamlit as st
import pandas as pd
import numpy as np

# 1. Configuração de Página e Estilo Dark
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

    with st.sidebar:
        st.title("⚙️ Filtros")
        if st.button("🔄 Sincronizar Dados", type="primary"):
            st.cache_data.clear()
            st.rerun()
        st.write("---")
        meses_sel = st.multiselect("📅 Períodos:", options=lista_meses, default=lista_meses, key='ms_meses')
        grupos_sel = st.multiselect("📂 Grupos:", options=list(MAPA_GRUPOS.keys()), default=list(MAPA_GRUPOS.keys()), key='ms_grupos')
        
        cats_dinamicas = sorted(list(set([cat for g in grupos_sel for cat in MAPA_GRUPOS[g]])))
        cats_sel = st.multiselect("🏷️ Categorias:", options=cats_dinamicas, default=cats_dinamicas, key='ms_cats')

    # Aplicação dos Filtros
    df = df_raw.copy()
    if meses_sel: df = df[df['Mes_Ano'].isin(meses_sel)]
    if grupos_sel: df = df[df['Grupo_Filtro'].isin(grupos_sel)]
    if cats_sel: df = df[df['Categoria'].isin(cats_sel)]

    st.title("💎 CASH FLOW PROJECT - ACCOUNTS PAYABLE")
    
    # --- MÉTRICAS ---
    saidas_only = df[df[col_v] < 0].copy()
    total_geral = saidas_only[col_v].sum()
    valor_tributario = saidas_only[saidas_only['Grupo_Filtro'] == 'Tributário'][col_v].sum()
    valor_operacional = saidas_only[saidas_only['Grupo_Filtro'] == 'Operacional'][col_v].sum()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Cash Out Total", format_brl(abs(total_geral)))
    with m2:
        perc_trib = (abs(valor_tributario) / abs(total_geral) * 100) if total_geral != 0 else 0
        st.metric("Carga Tributária", format_brl(abs(valor_tributario)), f"↑ {perc_trib:.1f}% do total")
    with m3:
        st.metric("Custos Operacionais", format_brl(abs(valor_operacional)))
    with m4:
        st.metric("Aging (Lançamentos)", len(df))

    st.write("---")

    tab_proj, tab_burn, tab_pareto, tab_raw = st.tabs(["📊 Projeção Mensal", "🔥 Cash Burn Diário", "🎯 Pareto (80/20)", "📋 Dados Brutos"])

    with tab_proj:
        st.subheader("📈 Evolução Mensal")
        saidas_only['Mês/Ano'] = saidas_only['Data de pagamento'].dt.strftime('%m/%Y')
        proj_m = saidas_only.groupby('Periodo_Sort')[col_v].sum().abs().reset_index()
        proj_m['Mês/Ano_Label'] = proj_m['Periodo_Sort'].astype(str)
        st.bar_chart(proj_m.set_index('Mês/Ano_Label')[col_v], color="#38bdf8")
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Por Grupo**")
            st.line_chart(saidas_only.groupby(['Mês/Ano', 'Grupo_Filtro'])[col_v].sum().abs().unstack().fillna(0))
        with c2:
            st.write("**Top 5 Categorias**")
            top5 = saidas_only.groupby('Categoria')[col_v].sum().abs().nlargest(5).index
            st.line_chart(saidas_only[saidas_only['Categoria'].isin(top5)].groupby(['Mês/Ano', 'Categoria'])[col_v].sum().abs().unstack().fillna(0))

    with tab_burn:
        st.subheader("🔥 Queima de Caixa Acumulada")
        if not saidas_only.empty:
            burn = saidas_only.groupby('Data de pagamento')[col_v].sum().abs().cumsum()
            st.area_chart(burn, color="#f43f5e")

    with tab_pareto:
        st.subheader("🎯 Análise de Pareto")
        if not saidas_only.empty:
            col_p1, col_p2 = st.columns(2)
            
            def render_donut(data, label_col, value_col, color_scheme):
                spec = {
                    "mark": {"type": "arc", "innerRadius": 50, "tooltip": True},
                    "encoding": {
                        "theta": {"field": value_col, "type": "quantitative"},
                        "color": {"field": label_col, "type": "nominal", "scale": {"scheme": color_scheme}},
                    },
                    "view": {"stroke": None}
                }
                return st.vega_lite_chart(data, spec, use_container_width=True)

            with col_p1:
                st.write("### 📂 Gastos por Grupo")
                df_g = saidas_only.groupby('Grupo_Filtro')[col_v].sum().abs().reset_index()
                df_g.columns = ['Grupo', 'Valor']
                render_donut(df_g, 'Grupo', 'Valor', 'reds')
                st.dataframe(df_g.sort_values('Valor', ascending=False).style.format({'Valor': "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
                st.bar_chart(df_g.set_index('Grupo')['Valor'], color="#f43f5e")

            with col_p2:
                st.write("### 🏷️ Top 10 Categorias")
                df_c = saidas_only.groupby('Categoria')[col_v].sum().abs().reset_index()
                df_c.columns = ['Categoria', 'Valor']
                df_c_top = df_c.sort_values('Valor', ascending=False).head(10)
                render_donut(df_c_top, 'Categoria', 'Valor', 'blues')
                st.dataframe(df_c.sort_values('Valor', ascending=False).style.format({'Valor': "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
                st.bar_chart(df_c_top.set_index('Categoria')['Valor'], color="#38bdf8")

    with tab_raw:
        st.data_editor(df, column_config={
                col_v: st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "Data de pagamento": st.column_config.DateColumn("Data de Pagamento", format="DD/MM/YYYY")
            }, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro: {e}")







