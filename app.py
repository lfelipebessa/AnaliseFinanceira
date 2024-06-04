import streamlit as st
import pandas as pd
import openpyxl
import re
from datetime import datetime
import plotly.express as px
from PIL import Image


# Configuração da página
st.set_page_config(layout="wide",
                   page_title="Análise de Dados")

# Função para corrigir a formatação dos nomes completos dos clientes


def corrigir_nome_completo(nome_completo):
    padrao = re.compile(r'([A-Za-z]+)\.,\s([A-Za-z]+)')
    return padrao.sub(r'\2 \1.', nome_completo)

# Função para calcular a idade com base na data de nascimento


def calcular_idade(data_nascimento):
    hoje = datetime.now()
    idade = hoje.year - data_nascimento.year - \
        ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
    return idade

# Função para formatar a data das vendas


def formatar_data_venda(data_venda):
    return data_venda.strftime('%b/%Y')

# Função para carregar dados dos arquivos Excel


@st.cache_data
def load_data():
    clientes_df = pd.read_excel('Cadastro Clientes.xlsx', engine='openpyxl')
    lojas_df = pd.read_excel('Cadastro Lojas.xlsx',
                             engine='openpyxl', skiprows=2, header=1)  # Pegando o nome correto das tabelas
    lojas_df = lojas_df.drop(lojas_df.columns[4], axis=1, errors='ignore')
    lojas_df = lojas_df.dropna()  # Remover linhas em branco
    produtos_df = pd.read_excel('Cadastro Produto.xlsx', engine='openpyxl')
    # vendas_2021 = pd.read_excel('Base Vendas - 2021.xlsx', engine='openpyxl')
    vendas_2022 = pd.read_excel('Base Vendas - 2022.xlsx', engine='openpyxl')
    vendas_2023 = pd.read_excel('Base Vendas - 2023.xlsx', engine='openpyxl')

    # Corrigir a formatação da data de naScimento
    # Na tabela do excel a coluna data de naCimento está escrita de maneira errada,
    # por isso o erro gramatical no código
    clientes_df['Data de Nacimento'] = pd.to_datetime(
        clientes_df['Data de Nacimento'], format='%d/%m/%Y')

    # Tratamento dos dados dos clientes
    clientes_df['Nome Completo'] = clientes_df['Nome Completo'].apply(
        corrigir_nome_completo)
    clientes_df['Idade'] = pd.to_datetime(
        clientes_df['Data de Nacimento']).apply(calcular_idade)
    clientes_df = clientes_df.drop(columns=['Data de Nacimento'])

    # Formatação da data das vendas
    # vendas_2021['Data Venda'] = vendas_2021['Data Venda'].apply(
    # formatar_data_venda)
    vendas_2022['Data Venda'] = vendas_2022['Data Venda'].apply(
        formatar_data_venda)
    vendas_2023['Data Venda'] = vendas_2023['Data Venda'].apply(
        formatar_data_venda)

    return clientes_df, lojas_df, produtos_df, vendas_2022, vendas_2023


# Função para concatenar dados
def concatenate_data(vendas_2022, vendas_2023):
    all_sales = pd.concat([vendas_2022, vendas_2023])
    return all_sales


# Carregar dados
clientes_df, lojas_df, produtos_df, vendas_2022, vendas_2023 = load_data()

# Concatenar dados de vendas
all_sales = concatenate_data(vendas_2022, vendas_2023)

# Separar a coluna Localidade em duas colunas: País e Continente
lojas_df[['País', 'Continente']] = lojas_df['Localidade'].str.split(
    ' - ', expand=True)

# Remover a coluna Localidade original
lojas_df.drop(columns=['Localidade'], inplace=True)

# Reorganizar a ordem das colunas
lojas_df = lojas_df.reindex(
    columns=['Id Loja', 'Cidade', 'País', 'Continente', 'Tipo Loja'])

# Relacionar tabelas
all_sales = all_sales.merge(produtos_df, how='left', on='Id Produto')
all_sales = all_sales.merge(clientes_df, how='left', on='Id Cliente')
all_sales = all_sales.merge(lojas_df, how='left', on='Id Loja')

st.title('📊 Análise de Vendas')

# st.write('## Dados das Lojas')
# st.dataframe(lojas_df)

# st.write('## Dados dos Clientes')
# st.dataframe(clientes_df)

# st.write('## Dados dos Produtos')
# st.dataframe(produtos_df)

# st.write('## Dados das Vendas')
# st.dataframe(all_sales)

# Converter 'Data Venda' para datetime
all_sales['Data Venda'] = pd.to_datetime(
    all_sales['Data Venda'], format='%b/%Y')

with st.sidebar:
    st.subheader("Feito por: Luiz Felipe Bessa")
    logo_teste = Image.open("Logo.jpg")
    st.image(logo_teste, use_column_width=True)
    st.subheader("SELEÇÃO DE FILTROS")
    # Adicionar uma barra lateral para seleção do tipo de loja
    fTipoLoja = st.selectbox(
        'Selecione o Tipo da Loja:', options=['Ambas', 'Física', 'Online']
    )

    # Adicionar uma barra lateral para seleção do continente
    fContinente = st.multiselect(
        'Selecione o Continente da Loja:', options=['Todos'] + list(all_sales['Continente'].unique()), default='Todos'
    )
    fDataInicio, fDataFim = st.date_input("Selecione o Período: (Jan/2022 - Dez/2023)", [
                                          all_sales['Data Venda'].min(), all_sales['Data Venda'].max()])

    # Adicionar uma barra lateral para seleção da marca
    fMarca = st.multiselect(
        "Selecione a Marca: ", options=['Todas'] + list(all_sales['Marca'].unique()), default='Todas'
    )

# Aplicar o filtro com base na seleção do usuário
# Filtro Tipo Loja
if fTipoLoja == "Ambas":
    all_sales = all_sales
else:
    all_sales = all_sales.loc[all_sales['Tipo Loja'] == fTipoLoja]

# Filtro Continente
if 'Todos' not in fContinente:
    all_sales = all_sales[all_sales['Continente'].isin(fContinente)]

# Filtro período de tempo
all_sales = all_sales[(all_sales['Data Venda'] >= pd.to_datetime(
    fDataInicio)) & (all_sales['Data Venda'] <= pd.to_datetime(fDataFim))]

# Filtro por marca
if 'Todas' not in fMarca:
    all_sales = all_sales[all_sales['Marca'].isin(fMarca)]


col1, col2, col3 = st.columns([1, 2, 2])

with col1:
    with st.container():
        st.header(" ")
        # Passando o Preço Unit. para Numérico
        all_sales['Preço Unit.'] = pd.to_numeric(
            all_sales['Preço Unit.'], errors='coerce')

        # Calculo do faturamento total
        faturamento_total = (
            (all_sales['Preço Unit.'] * (all_sales['Qtd. Vendida'] -
             all_sales['Qtd. Devolvida'])).sum()
        )

        # Calcular o custo total
        custo_total = (
            (all_sales['Custo Unit.'] * (all_sales['Qtd. Vendida'] -
             all_sales["Qtd. Devolvida"])).sum()
        )

        # Calcular o lucro total
        lucro_total = faturamento_total - custo_total

        # Converter o faturamento e o lucro  total para milhões
        custo_total_milhoes = custo_total / 1e6
        faturamento_total_milhoes = faturamento_total / 1e6
        lucro_total_milhoes = lucro_total / 1e6

        # Arredondar o faturamento total e o lucro total para duas casas decimais
        custo_total_milhoes_formatado = round(custo_total_milhoes, 2)
        faturamento_total_milhoes_formatado = round(
            faturamento_total_milhoes, 2)
        lucro_total_milhoes_formatado = round(lucro_total_milhoes, 2)

     # Exibir o custo, faturamento e lucro em milhões
    st.metric(label="Custo Total",
              value=f"${custo_total_milhoes_formatado} M")
    st.metric(label="Faturamento Total",
              value=f"${faturamento_total_milhoes_formatado} M")
    st.metric(label="Lucro Total",
              value=f"${lucro_total_milhoes_formatado} M")


with col2:
    with st.container():
        # Garantir que a coluna 'Data Venda' está no formato datetime
        all_sales['Data Venda'] = pd.to_datetime(
            all_sales['Data Venda'], format='%b/%Y')

        # Calcular o faturamento total por linha
        all_sales['Faturamento'] = all_sales['Preço Unit.'] * \
            (all_sales['Qtd. Vendida'] - all_sales['Qtd. Devolvida'])

        # Criar a coluna 'Mês/Ano' no formato desejado
        all_sales['Mês/Ano'] = all_sales['Data Venda'].dt.strftime('%b/%Y')

        # Agrupar os dados de vendas por mês/ano e calcular o faturamento total
        faturamento_por_mes = all_sales.groupby(
            'Mês/Ano')['Faturamento'].sum().reset_index()

        # Ordenar os dados por data para garantir que o gráfico será contínuo
        faturamento_por_mes['Data'] = pd.to_datetime(
            faturamento_por_mes['Mês/Ano'], format='%b/%Y')
        faturamento_por_mes = faturamento_por_mes.sort_values('Data')

        # Criar o gráfico com Plotly Express
        fig = px.line(faturamento_por_mes, x='Data', y='Faturamento',
                      title='Faturamento Total por Mês/Ano',
                      labels={'Data': 'Data',
                              'Faturamento': 'Faturamento Total'},
                      markers=True,)

        # Ajustar a cor da linha
        fig.update_traces(line_color="#B95BF5")

        # Exibir o gráfico
        st.plotly_chart(fig)


with col3:
    with st.container():
        # Garantir que a coluna 'Data Venda' está no formato datetime
        all_sales['Data Venda'] = pd.to_datetime(
            all_sales['Data Venda'], format='%b/%Y')

        # Calcular o lucro total por linha
        all_sales['Lucro'] = (all_sales['Preço Unit.'] - all_sales['Custo Unit.']) * (
            all_sales['Qtd. Vendida'] - all_sales['Qtd. Devolvida'])

        # Criar a coluna 'Mês/Ano' no formato desejado
        all_sales['Mês/Ano'] = all_sales['Data Venda'].dt.strftime('%b/%Y')

        # Agrupar os dados de vendas por mês/ano e calcular o lucro total
        lucro_por_mes = all_sales.groupby(
            'Mês/Ano')['Lucro'].sum().reset_index()

        # Ordenar os dados por data para garantir que o gráfico será contínuo
        lucro_por_mes['Data'] = pd.to_datetime(
            lucro_por_mes['Mês/Ano'], format='%b/%Y')
        lucro_por_mes = lucro_por_mes.sort_values('Data')

        # Criar o gráfico com Plotly Express
        fig = px.line(lucro_por_mes, x='Data', y='Lucro',
                      title='Lucro Total por Mês/Ano',
                      labels={'Data': 'Data', 'Lucro': 'Lucro Total'},
                      markers=True)

        # Ajustar a cor da linha
        fig.update_traces(line_color="#B95BF5")

        # Exibir o gráfico
        st.plotly_chart(fig)

col4, col5 = st.columns(2)
with col4:
    # Agrupar os dados por gênero e somar a quantidade vendida
    vendas_por_genero = all_sales.groupby(
        'Genero')['Qtd. Vendida'].sum().reset_index()

    # Mapear os códigos de genero para os rótulos correspondentes
    vendas_por_genero['Genero'] = vendas_por_genero['Genero'].map(
        {'F': 'Feminino', 'M': 'Masculino'})

    # Paleta de cores personalizada
    cores_personalizadas = ['#B95BF5', '#00CC96', '#F55E5B']

    # Criar o gráfico de barras com Plotly Express
    fig = px.pie(vendas_por_genero, values='Qtd. Vendida', names='Genero', hole=0.4,
                 title='Quantidade Total de Produtos Vendidos por Gênero',
                 color_discrete_sequence=cores_personalizadas)

    # Exibir o gráfico
    st.plotly_chart(fig)

    with col5:
        # Criar o gráfico de histograma com Plotly Express
        fig = px.histogram(all_sales, x='Idade', title='Distribuição da Quantidade de Vendas por Faixa Etária', histfunc='count',
                           labels={'count': 'Quantidade Vendida'})

        # Personalizar o layout do gráfico
        fig.update_layout(xaxis_title='Idade',
                          yaxis_title='Quantidade de Vendas', bargap=0.2)

        # Personalizar as informações mostradas ao passar o mouse sobre o gráfico
        fig.update_traces(
            hovertemplate='Idade=%{x}<br>Quantidade Vendida=%{y}',
            marker_color="#B95BF5")

        # Exibir o gráfico
        st.plotly_chart(fig)

# Agrupar os dados pelo nome da categoria e calcular o lucro total
lucro_por_categoria = all_sales.groupby(
    'Categoria')['Lucro'].sum().reset_index()

# Ordenar o DataFrame por lucro total em ordem decrescente
lucro_por_categoria = lucro_por_categoria.sort_values(
    by='Lucro', ascending=False)

# Converter o lucro para milhões com duas casas decimais
lucro_por_categoria['Lucro (Milhões)'] = lucro_por_categoria['Lucro'] / 1e6
lucro_por_categoria = round(lucro_por_categoria, 2)

# Paleta de cores personalizada
cores_personalizadas2 = ['#B95BF5', '#00CC96', '#F55E5B',
                         '#5BF5A0', '#F5BE5B', '#8E70A0', '#66756D', '#757066', '#DCF55B', '#9B70B5', '#5BF2F5']

# Criar o gráfico de barras com Plotly Express
fig = px.bar(lucro_por_categoria, x='Categoria', y='Lucro',
             title='Lucro Total por Categoria de Produto',
             labels={'Categoria': 'Categoria de Produto',
                     'Lucro': 'Lucro Total'},
             color='Categoria',
             text='Lucro (Milhões)',
             color_discrete_sequence=cores_personalizadas2
             )

# Personalizar o layout do gráfico
fig.update_layout(xaxis_title='Categoria de Produto',
                  yaxis_title='Lucro Total (Milhões)')

# Exibir o gráfico
st.plotly_chart(fig)

# Agrupar os dados pelo país e contar a quantidade de clientes únicos
clientes_por_pais = all_sales.groupby(
    'País')['Id Cliente'].nunique().reset_index()
clientes_por_pais = clientes_por_pais.rename(
    columns={'Id Cliente': 'Quantidade de Clientes'})

# Ordenar os dados por quantidade de clientes
clientes_por_pais = clientes_por_pais.sort_values(
    by='Quantidade de Clientes', ascending=False)

# Criar o gráfico de barras horizontais com Plotly Express e definir uma paleta de cores
fig = px.bar(clientes_por_pais, y='País', x='Quantidade de Clientes',
             title='Quantidade de Clientes por País',
             labels={'País': 'País',
                     'Quantidade de Clientes': 'Quantidade de Clientes'},
             orientation='h',
             color='País',  # Usar a coluna 'País' para definir as cores
             color_discrete_sequence=cores_personalizadas2
             )

# Exibir o gráfico
st.plotly_chart(fig)
