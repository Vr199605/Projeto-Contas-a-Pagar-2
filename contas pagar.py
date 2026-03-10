import streamlit as st
import pandas as pd
import numpy as np

# 1. Configuração de Página e Estilo Dark Premium
st.set_page_config(page_title="CFO Strategic Intelligence", layout="wide", initial_sidebar_state="collapsed")

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
            return float(v)
        return v

    col_v = 'Valor categoria/centro de custo'
    df[col_v] = df[col_v].apply(clean_val)
    df['Data de pagamento'] = pd.to_datetime(df['Data de pagamento'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Data de pagamento']).sort_values('Data de pagamento')

    keywords_imposto = ['ISS', 'IRPJ', 'CSLL', 'PIS', 'COFINS', 'RETIDO', 'IMPOSTO', 'TAXA', 'DARF']
    df['Tipo'] = df['Categoria'].apply(
        lambda x: 'Imposto/Retenção' if any(k in str(x).upper() for k in keywords_imposto) else 'Operacional'
    )
    
    return df

try:
    df = load_and_process()
    col_v = 'Valor categoria/centro de custo'

    # Header Superior
    c1, c2 = st.columns([4, 1])
    with c1:
        st.title("💎 CFO Intelligence: Strategic View")
    with c2:
        if st.button("🔄 Sincronizar Dados"):
            st.cache_data.clear()
            st.rerun()

    # 3. Métricas de Alto Impacto (Formatadas em Moeda)
    saidas_totais = df[df[col_v] < 0][col_v].sum()
    impostos_totais = df[df['Tipo'] == 'Imposto/Retenção'][col_v].sum()
    operacional_puro = df[df['Tipo'] == 'Operacional'][col_v].sum()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cash Out Total", format_brl(abs(saidas_totais)))
    m2.metric("Carga Tributária", format_brl(abs(impostos_totais)), f"{abs(impostos_totais/saidas_totais)*100:.1f}% do total")
    m3.metric("Custos Operacionais", format_brl(abs(operacional_puro)))
    m4.metric("Aging (Lançamentos)", len(df))

    st.write("##")

    # 4. Sistema de Abas Estratégicas
    tab_burn, tab_pareto, tab_tax, tab_raw, tab_guide = st.tabs([
        "🔥 Cash Burn Diário", "🎯 Pareto (80/20)", "🏛️ Fiscal vs Op", "📋 Dados Brutos", "📖 Guia de Uso"
    ])

    # ABA: CASH BURN
    with tab_burn:
        st.subheader("Evolução do Consumo de Caixa (Acumulado)")
        burn_df = df.groupby('Data de pagamento')[col_v].sum().cumsum().reset_index()
        st.area_chart(burn_df.set_index('Data de pagamento'), color="#f43f5e")
        

    # ABA: PARETO
    with tab_pareto:
        st.subheader("Análise de Pareto: Foco no que importa")
        resumo_cat = df[df[col_v] < 0].groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False).reset_index()
        resumo_cat['% Acumulado'] = (resumo_cat[col_v].cumsum() / resumo_cat[col_v].sum()) * 100
        pareto_df = resumo_cat[resumo_cat['% Acumulado'] <= 85] 
        
        c_p1, c_p2 = st.columns([1, 2])
        with c_p1:
            st.info("Regra 80/20: Estas categorias representam o maior peso financeiro.")
            # Formatando a exibição da tabela de Pareto
            st.dataframe(
                pareto_df[['Categoria', col_v]].style.format({col_v: "R$ {:,.2f}"}),
                hide_index=True, use_container_width=True
            )
        with c_p2:
            st.bar_chart(pareto_df.set_index('Categoria')[col_v], color="#38bdf8")

    # ABA: FISCAL VS OPERAÇÃO
    with tab_tax:
        st.subheader("Distribuição Financeira por Natureza")
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            dist_tipo = df.groupby('Tipo')[col_v].sum().abs()
            st.bar_chart(dist_tipo, color="#a21caf")
        with c_t2:
            st.markdown("### Listagem de Tributos/Retenções")
            st.dataframe(
                df[df['Tipo'] == 'Imposto/Retenção'][['Data de pagamento', 'Categoria', col_v]].style.format({col_v: "R$ {:,.2f}"}),
                hide_index=True, use_container_width=True
            )

    # ABA: DADOS BRUTOS (Filtros e Edição)
    with tab_raw:
        st.subheader("Explorador Geral")
        busca = st.text_input("Filtrar por conta ou categoria...")
        df_final = df[df['Categoria'].str.contains(busca, case=False)]
        
        st.data_editor(
            df_final,
            column_config={
                col_v: st.column_config.NumberColumn(
                    "Valor", 
                    format="R$ %.2f", # Formatação direta no componente Streamlit
                    help="Valor financeiro do lançamento"
                ),
                "Data de pagamento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
            },
            hide_index=True, use_container_width=True
        )

    # ABA: GUIA DE USO
    with tab_guide:
        st.markdown("## 🧭 Guia do Executivo Financeiro")
        with st.expander("🔥 O que é o Cash Burn Diário?"):
            st.write("Representa a velocidade de consumo do caixa. Degraus fundos indicam alta concentração de pagamentos no dia.")
        with st.expander("🎯 Como usar o Pareto (80/20)?"):
            st.write("Foca nos 20% das categorias que geram 80% do custo. Ideal para cortes estratégicos.")
        with st.expander("🏛️ Fiscal vs Operação"):
            st.write("Separa o que é custo de atividade do que é obrigação tributária direta.")

except Exception as e:
    st.error(f"Erro ao carregar dashboard: {e}")