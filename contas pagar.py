import streamlit as st
import pandas as pd
import numpy as np

# 1. Configuração de Página e Layout Dark Luxo
st.set_page_config(page_title="CASH FLOW | AP", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    /* Global Style */
    .main { background-color: #0B0E14; }
    div[data-testid="stMetricValue"] { color: #00D1FF; font-weight: 700; font-size: 1.8rem !important; }
    div[data-testid="stMetricLabel"] { color: #94A3B8; font-weight: 400; }
    
    /* Containers das Métricas */
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    /* Estilização das Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #1E293B;
        border-radius: 8px 8px 0 0;
        color: #94A3B8;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #00D1FF !important; 
        color: #0B0E14 !important; 
    }

    /* Sidebar Custom */
    .css-1d391kg { background-color: #111827; }
    </style>
    """, unsafe_allow_html=True)

def format_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

MAPA_GRUPOS = {
    "Administrativo": ["ALUGUEL", "COMPRA DE ATIVO FIXO", "CONDOMÍNIO", "COWORKING", "CUSTO OPERACIONAL", "DESPESAS FINANCEIRAS", "ENERGIA ELÉTRICA", "ESTORNO", "EVENTOS FUNCIONÁRIOS", "Juros Pagos", "MANUTENÇÃO ESCRITÓRIO", "MATERIAIS DE TI", "MATERIAL DE COPA", "MATERIAL DE ESCRITÓRIO", "MATERIAL DE LIMPEZA", "Multas Pagas", "Não classificado", "OUTRAS DESPESAS", "PAGAMENTO DE EMPRÉSTIMO", "REPRESENTAÇÃO", "SEGUROS", "SERVIÇOS CONTÁBEIS", "SERVIÇOS CONTRATADOS", "SERVIÇOS DE E-MAIL", "SERVIÇOS DE ENTREGA", "SERVIÇOS DE PUBLICIDADE", "SERVIÇOS JURÍDICOS", "SERVIÇOS TI", "SISTEMAS", "TAXAS E CONTRIBUIÇÕES", "TELEFONIA/INTERNET", "TREINAMENTOS", "VAGAS GARAGEM - SÓCIOS","SERVIÇOS DE PUBLICIDADE"],
    "Despesa de pessoal": ["13º SALÁRIO", "ADIANTAMENTO AO FUNCIONÁRIO", "ANTECIPAÇÃO DE RESULTADOS", "ASSISTÊNCIA MÉDICA", "ASSISTÊNCIA ODONTO", "BÔNUS CLT", "BÔNUS PERFORMANCE - G", "CONSULTORIA ESPECIALIZADA - G", "CONSULTORIA ESPECIALIZADA - TI", "DESPESA EVENTUAL DE PESSOAL", "DESPESAS VIAGEM", "ESTAGIÁRIO FOLHA", "EXAMES OCUPACIONAIS", "FÉRIAS", "FGTS", "GRATIFICAÇÕES CLT", "GRATIFICAÇÕES PJ - G", "INSS", "IRRF", "LOCOMOÇÃO", "Multas Pagas", "PRO LABORE", "REPRESENTAÇÃO", "RESCISÃO", "SALÁRIOS CLT", "SEGURO DE VIDA", "SERVIÇOS CONTRATADOS", "VA/VR", "VT"],
    "Operacional": ["BÔNUS - TERCEIROS", "COMISSÕES SEGUROS", "CUSTO OPERACIONAL", "Descontos Recebidos", "EVENTOS CLIENTES", "Multas Pagas", "REBATE COMISSÕES", "REPRESENTAÇÃO"],
    "Tributário": ["COFINS", "COFINS Retido sobre Pagamentos", "CSLL", "CSLL Retido sobre Pagamentos", "DESPESAS FINANCEIRAS", "ESTORNO", "INSS Retido sobre Pagamentos", "IPTU", "IRPJ", "IRPJ Retido sobre Pagamentos", "ISS", "ISS Retido sobre Pagamentos", "Juros Pagos", "Multas Pagas", "Pagamento de ISS Retido", "PARCELAMENTO RECEITA FEDERAL", "PERT CSLL", "PERT IRPJ", "PERT IRRF", "PERT SN", "PIS", "PIS Retido sobre Pagamentos"]
}

@st.cache_data(ttl=600)
def load_and_process():
    url_saidas = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?gid=1959056339&single=true&output=csv"
    url_recebidos = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT7KV7hi8lJHEleaPoPyAKWo7ChUTlLuorbLX9v4aZGXPKI6aeudpF06eUc60hmIPX8Pkz5BrZOhc1G/pub?gid=58078527&single=true&output=csv"
    
    def clean_val(v):
        if isinstance(v, str):
            v = v.replace('R$', '').replace('.', '').replace(' ', '').replace(',', '.')
            try: return float(v)
            except: return 0.0
        return v

    col_v = 'Valor categoria/centro de custo'

    # Processar Saídas
    df_s = pd.read_csv(url_saidas)
    df_s[col_v] = df_s[col_v].apply(clean_val)
    df_s['Data de pagamento'] = pd.to_datetime(df_s['Data de pagamento'], dayfirst=True, errors='coerce')
    df_s = df_s.dropna(subset=['Data de pagamento']).sort_values('Data de pagamento')
    df_s['Mes_Ano'] = df_s['Data de pagamento'].dt.strftime('%m/%Y')
    
    def atribuir_grupo(cat):
        for grupo, categorias in MAPA_GRUPOS.items():
            if cat in categorias: return grupo
        return "Outros"
    df_s['Grupo_Filtro'] = df_s['Categoria'].apply(atribuir_grupo)

    # Processar Recebidos
    df_r = pd.read_csv(url_recebidos)
    df_r[col_v] = df_r[col_v].apply(clean_val)
    df_r['Data de pagamento'] = pd.to_datetime(df_r['Data de pagamento'], dayfirst=True, errors='coerce')
    df_r = df_r.dropna(subset=['Data de pagamento'])
    df_r['Mes_Ano'] = df_r['Data de pagamento'].dt.strftime('%m/%Y')

    return df_s, df_r

try:
    df_raw, df_rec_raw = load_and_process()
    col_v = 'Valor categoria/centro de custo'
    lista_meses = sorted(df_raw['Mes_Ano'].unique(), key=lambda x: pd.to_datetime(x, format='%m/%Y'))

    with st.sidebar:
        st.markdown("<h2 style='color: #00D1FF;'>💎 DASHBOARD</h2>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.write("---")
        meses_sel = st.multiselect("📅 Períodos:", options=lista_meses, default=lista_meses)
        grupos_sel = st.multiselect("📂 Grupos:", options=list(MAPA_GRUPOS.keys()), default=list(MAPA_GRUPOS.keys()))
        
        cats_dinamicas = [cat for g in grupos_sel for cat in MAPA_GRUPOS[g]]
        cats_sel = st.multiselect("🏷️ Categorias:", options=sorted(list(set(cats_dinamicas))), default=sorted(list(set(cats_dinamicas))))

    # Filtros Saídas
    df = df_raw.copy()
    if meses_sel: df = df[df['Mes_Ano'].isin(meses_sel)]
    if grupos_sel: df = df[df['Grupo_Filtro'].isin(grupos_sel)]
    if cats_sel: df = df[df['Categoria'].isin(cats_sel)]

    # Filtros Recebidos
    df_rec = df_rec_raw.copy()
    if meses_sel: df_rec = df_rec[df_rec['Mes_Ano'].isin(meses_sel)]

    # --- HEADER PRINCIPAL ---
    st.title("💸 Cash Flow | Accounts Payable")
    st.markdown(f"<p style='color: #94A3B8;'>Análise detalhada de saídas e projeções financeiras</p>", unsafe_allow_html=True)
    
    saidas_df = df[df[col_v] < 0]
    total_geral = saidas_df[col_v].sum()
    
    cols_m = st.columns(len(grupos_sel) + 1)
    with cols_m[0]:
        st.metric("CASH OUT TOTAL", format_brl(abs(total_geral)))
    
    for i, grupo in enumerate(grupos_sel):
        val_g = df[(df['Grupo_Filtro'] == grupo) & (df[col_v] < 0)][col_v].sum()
        with cols_m[i+1]:
            st.metric(grupo.upper(), format_brl(abs(val_g)))

    st.write("---")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 EVOLUÇÃO", "🔥 CASH BURN", "🎯 PARETO", "📋 DADOS", 
        "💰 RECEBIDOS", "📈 ANÁLISE JAN/26", "💎 LUCRATIVIDADE"
    ])

    with tab1:
        st.subheader("Apresentação do Dashboard Executivo")
        st.markdown(f"""
        Este dashboard foi desenvolvido para fornecer à **Diretoria e Sócios** uma visão clara e objetiva da saúde financeira da operação, focando estritamente no fluxo de saídas (Contas a Pagar). 
        
        **Objetivos desta ferramenta:**
        * **Transparência Total:** Monitoramento em tempo real do destino do capital da empresa.
        * **Análise de Eficiência:** Identificação rápida de custos que excedem o planejado através do ranking de categorias.
        * **Gestão de Queima (Cash Burn):** Acompanhamento diário acumulado para garantir que o fluxo de desembolso esteja alinhado com as metas de liquidez.
        * **Tomada de Decisão Estratégica:** Filtros dinâmicos que permitem isolar grupos como Pessoal, Operacional e Tributário para ajustes precisos na estrutura de custos.
        
        *Utilize os filtros laterais para navegar entre períodos e categorias específicas.*
        """)

    with tab2:
        st.subheader("Queima de Caixa Diária (Acumulada)")
        if not saidas_df.empty:
            burn = saidas_df.groupby('Data de pagamento')[col_v].sum().abs().cumsum().reset_index()
            burn.columns = ['Data', 'Gasto Acumulado']
            st.line_chart(burn.set_index('Data')['Gasto Acumulado'], color="#FF4B4B")
            
            st.write("#### Detalhamento de Saída Diária")
            diario = saidas_df.groupby('Data de pagamento')[col_v].sum().abs().reset_index()
            diario.columns = ['Data', 'Valor do Dia']
            st.dataframe(diario.style.format({'Valor do Dia': "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
        else:
            st.info("Sem saídas registradas para este filtro.")

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Maiores Gastos por Grupo")
            g_pareto = saidas_df.groupby('Grupo_Filtro')[col_v].sum().abs().sort_values(ascending=False).reset_index()
            st.dataframe(g_pareto.style.format({col_v: "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
            st.bar_chart(g_pareto.set_index('Grupo_Filtro')[col_v], color="#00D1FF")

        with c2:
            st.subheader("Top 10 Categorias")
            c_pareto = saidas_df.groupby('Categoria')[col_v].sum().abs().sort_values(ascending=False).head(10).reset_index()
            st.dataframe(c_pareto.style.format({col_v: "R$ {:,.2f}"}), use_container_width=True, hide_index=True)
            st.bar_chart(c_pareto.set_index('Categoria')[col_v], color="#00D1FF")

    with tab4:
        st.subheader("Explorador de Lançamentos")
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab5:
        st.subheader("Explorador de Recebidos")
        st.dataframe(df_rec, use_container_width=True, hide_index=True)

    with tab6:
        st.subheader("Análise Mensal: Janeiro 2026")
        jan_s = abs(df_raw[df_raw['Mes_Ano'] == '01/2026'][col_v].sum())
        jan_e = df_rec_raw[df_rec_raw['Mes_Ano'] == '01/2026'][col_v].sum()
        resultado = jan_e - jan_s
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Entrou (Jan/26)", format_brl(jan_e))
        col_res2.metric("Saiu (Jan/26)", format_brl(jan_s))
        col_res3.metric("Saldo/Déficit", format_brl(resultado), delta=resultado)
        
        df_jan_chart = pd.DataFrame({'Tipo': ['Entradas', 'Saídas'], 'Valores': [jan_e, jan_s]}).set_index('Tipo')
        st.bar_chart(df_jan_chart, color="#00D1FF")

    with tab7:
        st.subheader("Margem de Contribuição e Lucratividade")
        total_e = df_rec[col_v].sum()
        total_s = abs(df[df[col_v] < 0][col_v].sum())
        lucro_abs = total_e - total_s
        margem = (lucro_abs / total_e * 100) if total_e > 0 else 0
        
        cl1, cl2 = st.columns(2)
        cl1.metric("LUCRO LÍQUIDO (CAIXA)", format_brl(lucro_abs))
        cl2.metric("MARGEM DE LUCRO", f"{margem:.1f}%")
        
        st.write("#### Eficiência por Grupo (% Consumo sobre a Receita)")
        if total_e > 0:
            grupo_impacto = (df[df[col_v] < 0].groupby('Grupo_Filtro')[col_v].sum().abs() / total_e * 100).round(1).reset_index()
            grupo_impacto.columns = ['Grupo', '% Receita']
            
            st.bar_chart(grupo_impacto.set_index('Grupo'), color="#00D1FF")
            
            st.write("📊 **Detalhamento de Impacto no Faturamento:**")
            st.dataframe(
                grupo_impacto.assign(Porcentagem=grupo_impacto['% Receita'].apply(lambda x: f"{x:.1f}%"))[['Grupo', 'Porcentagem']],
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Aguardando dados de receita para calcular impacto por grupo.")

except Exception as e:
    st.error(f"Erro ao carregar layout: {e}")


