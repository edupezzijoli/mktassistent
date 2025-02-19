import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Carregar a planilha
def load_data(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        meta_ads_df = pd.read_excel(xls, 'Meta Ads')
        google_ads_df = pd.read_excel(xls, 'Google Ads')
        return meta_ads_df, google_ads_df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None

# Processamento dos dados
def process_data(df):
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df = df.dropna(subset=['Data'])  # Remover valores nulos
    df['Dia da Semana'] = df['Data'].dt.day_name()
    df['Data Simplificada'] = df['Data'].dt.strftime('%d/%m')  # Apenas dia e mês
    return df

# Funções de cálculo

def conversion_rate(df, platform):
    if platform == "Meta Ads":
        return df['Compras'].sum() / df['Carrinhos'].sum() if df['Carrinhos'].sum() > 0 else 0
    elif platform == "Google Ads":
        return df['Compras'].sum() / df['Impressões'].sum() if df['Impressões'].sum() > 0 else 0

def highest_revenue_day(df):
    if df['Receita'].sum() > 0:
        faturamento_por_dia = df.groupby('Data Simplificada')['Receita'].sum()
        return faturamento_por_dia.idxmax(), faturamento_por_dia.max()
    return "Nenhum dado", 0

def highest_ticket_day(df):
    if df['Compras'].sum() > 0:
        ticket_medio_por_dia = df.groupby('Data Simplificada').apply(lambda x: x['Receita'].sum() / x['Compras'].sum())
        return ticket_medio_por_dia.idxmax(), ticket_medio_por_dia.max()
    return "Nenhum dado", 0

def checkout_performance(df, platform):
    if platform == "Meta Ads" and df['Carrinhos'].sum() > 0:
        return df['Finalização de compra'].sum() / df['Carrinhos'].sum()
    return None

def investment_roas(df):
    investimento_total = df['Custo'].sum()
    roas_total = df['Receita'].sum() / investimento_total if investimento_total > 0 else 0
    return investimento_total, roas_total

def investment_faturamento(df):
    faturamento_total = df['Receita'].sum()
    return faturamento_total

def lowest_cac_day(df):
    if df['Compras'].sum() > 0:
        cac_por_dia = df.groupby('Dia da Semana').apply(lambda x: x['Custo'].sum() / x['Compras'].sum())
        return cac_por_dia.idxmin(), cac_por_dia.min()
    return "Nenhum dado", 0

def conversion_rate_last_7_days(df, platform):
    # Últimos 7 dias
    ultimos_7_dias = df['Data'].max() - pd.Timedelta(days=6)
    df_ultimos_7_dias = df[df['Data'] >= ultimos_7_dias]

    # 7 dias anteriores
    periodo_anterior = ultimos_7_dias - pd.Timedelta(days=7)
    df_periodo_anterior = df[(df['Data'] >= periodo_anterior) & (df['Data'] < ultimos_7_dias)]

    # Calcular a taxa de conversão de acordo com a plataforma
    if platform == "Meta Ads":
        taxa_ultimos_7_dias = df_ultimos_7_dias['Compras'].sum() / df_ultimos_7_dias['Carrinhos'].sum() if df_ultimos_7_dias['Carrinhos'].sum() > 0 else 0
        taxa_periodo_anterior = df_periodo_anterior['Compras'].sum() / df_periodo_anterior['Carrinhos'].sum() if df_periodo_anterior['Carrinhos'].sum() > 0 else 0
    elif platform == "Google Ads":
        taxa_ultimos_7_dias = df_ultimos_7_dias['Compras'].sum() / df_ultimos_7_dias['Impressões'].sum() if df_ultimos_7_dias['Impressões'].sum() > 0 else 0
        taxa_periodo_anterior = df_periodo_anterior['Compras'].sum() / df_periodo_anterior['Impressões'].sum() if df_periodo_anterior['Impressões'].sum() > 0 else 0

    # Comparação
    if taxa_ultimos_7_dias > taxa_periodo_anterior:
        status = "🟢 Aumentou"
    elif taxa_ultimos_7_dias < taxa_periodo_anterior:
        status = "🔴 Diminuiu"
    else:
        status = "🟡 Manteve-se estável"

    return taxa_ultimos_7_dias, taxa_periodo_anterior, status

# Interface Streamlit
st.set_page_config(layout="wide")
st.sidebar.title("⚙️ Configurações")

file_path = "acompanhamento.xlsx"
meta_ads_df, google_ads_df = load_data(file_path)

if meta_ads_df is not None and google_ads_df is not None:
    plataforma = st.sidebar.selectbox("Escolha a plataforma", ["Meta Ads", "Google Ads"])
    
    df = meta_ads_df if plataforma == "Meta Ads" else google_ads_df
    df = process_data(df)
    
    ultima_data = df['Data'].max().strftime('%d/%m/%Y')  # Última data disponível
    st.sidebar.write(f"**Última data disponível:** {ultima_data}")
    
    data_inicio = st.sidebar.date_input("Data de Início", df['Data'].min().date())
    data_fim = st.sidebar.date_input("Data de Fim", df['Data'].max().date())
    
    df = df[(df['Data'] >= pd.to_datetime(data_inicio)) & (df['Data'] <= pd.to_datetime(data_fim))]
    
    if df.empty:
        st.warning("Nenhum dado disponível para o período selecionado.")
    else:
        results = {
            'taxa_conversao': conversion_rate(df, plataforma),
            'dia_maior_faturamento': highest_revenue_day(df)[0],
            'maior_faturamento': highest_revenue_day(df)[1],
            'dia_maior_ticket_medio': highest_ticket_day(df)[0],
            'maior_ticket_medio': highest_ticket_day(df)[1],
            'checkout_ratio': checkout_performance(df, plataforma),
            'investimento_total': investment_roas(df)[0],
            'faturamento_total': investment_faturamento(df),
            'roas_total': investment_roas(df)[1],
            'dia_menor_cac': lowest_cac_day(df)[0],
            'menor_cac': lowest_cac_day(df)[1],
        }

        # Calcular a taxa de conversão dos últimos 7 dias para Meta Ads
        taxa_meta_ultimos_7_dias, taxa_meta_periodo_anterior, status_meta = conversion_rate_last_7_days(meta_ads_df, "Meta Ads")
        
        # Calcular a taxa de conversão dos últimos 7 dias para Google Ads
        taxa_google_ultimos_7_dias, taxa_google_periodo_anterior, status_google = conversion_rate_last_7_days(google_ads_df, "Google Ads")

        st.subheader("🔢 Análise da Performance ")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Taxa de Conversão", f"{results['taxa_conversao']:.2%}")
            st.metric("Conversão 7 Dias (Meta Ads)", 
                      f"{taxa_meta_ultimos_7_dias:.2%} (vs {taxa_meta_periodo_anterior:.2%})", 
                      status_meta)
            st.metric("Conversão 7 Dias (Google Ads)", 
                      f"{taxa_google_ultimos_7_dias:.2%} (vs {taxa_google_periodo_anterior:.2%})", 
                      status_google)
            st.metric("Maior Faturamento", f"🗓️ {results['dia_maior_faturamento']} (R$ {results['maior_faturamento']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + ")")
            st.metric("Faturamento Total", f"💵 R$ {results['faturamento_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        with col2:
            st.metric("ROAS", f"{results['roas_total']:.2f}")
            st.metric("Maior Ticket Médio", f"🗓️ {results['dia_maior_ticket_medio']} (R$ {results['maior_ticket_medio']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + ")")
            st.metric("Investimento Total", f"💵 R$ {results['investimento_total']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))     

    st.markdown("---")  

    st.subheader("📊 Gráficos de Performance")

    col3, col4 = st.columns(2)  # Criando duas colunas para os gráficos

    # Gráfico de Receita ao longo do tempo
    fig, ax = plt.subplots(figsize=(3, 1.5))  # Reduzindo o tamanho do gráfico
    df.groupby("Data Simplificada")['Receita'].sum().plot(kind='line', ax=ax, title="Receita ao Longo do Tempo", linewidth=0.5)

    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, fontsize=4)  # Reduzindo tamanho das legendas do eixo X
    ax.set_yticklabels(ax.get_yticks(), fontsize=4)  # Reduzindo tamanho das legendas do eixo Y
    ax.title.set_size(6)  # Reduzindo tamanho do título
    ax.set_xlabel("")  # Removendo o rótulo do eixo X
    ax.set_ylabel("")  # Removendo o rótulo do eixo Y

    col3.pyplot(fig)

    # Gráfico de Compras por Dia da Semana
    fig, ax = plt.subplots(figsize=(3, 1.5))  # Reduzindo o tamanho do gráfico
    df.groupby("Dia da Semana")['Compras'].sum().plot(kind='bar', ax=ax, title="Compras por Dia da Semana")

    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, fontsize=4)  # Reduzindo tamanho das legendas do eixo X
    ax.set_yticklabels(ax.get_yticks(), fontsize=4)  # Reduzindo tamanho das legendas do eixo Y
    ax.title.set_size(6)  # Reduzindo tamanho do título
    ax.set_xlabel("")  # Removendo o rótulo do eixo X
    ax.set_ylabel("")  # Removendo o rótulo do eixo Y

    col4.pyplot(fig)

# -------------------- NOVO GRÁFICO PERSONALIZADO --------------------
st.markdown("---")
st.subheader("📈 Gráfico Personalizado")

# Seleção das métricas para o gráfico personalizado (agora múltiplas colunas)
colunas_disponiveis = ['Receita', 'Compras', 'Custo', 'Impressões', 'Carrinhos', 'Finalização de compra', 'CPC', 'CPM', 'Visualizações', 'Alcance', 'CAC', 'ROAS']
colunas_selecionadas = st.multiselect("Selecione as métricas para visualizar no gráfico", colunas_disponiveis, default=['Receita'])

if colunas_selecionadas:
    # Cálculo do maior valor e da média para cada métrica selecionada
    col5, col6 = st.columns(2)
    with col5:
        maiores_valores = {col: df[col].max() for col in colunas_selecionadas}
        st.write("📌 **Maior Valor por Métrica**")
        for col, val in maiores_valores.items():
            st.write(f"**{col}:** {val:,.2f}")

    with col6:
        medias_valores = {col: df[col].mean() for col in colunas_selecionadas}
        st.write("📊 **Média por Métrica**")
        for col, val in medias_valores.items():
            st.write(f"**{col}:** {val:,.2f}")

    # Criando o gráfico dinâmico para múltiplas colunas
    fig, ax = plt.subplots(figsize=(8, 4))

    for coluna in colunas_selecionadas:
        df.groupby("Data Simplificada")[coluna].sum().plot(kind='line', ax=ax, linewidth=1, label=coluna)

    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, fontsize=6)
    ax.set_xlabel("Data")
    ax.set_ylabel("Valores")
    ax.set_title("Comparação das métricas ao longo do tempo", fontsize=8)
    ax.legend(fontsize=6)

    st.pyplot(fig)
