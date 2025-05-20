import os
import numpy as np
import re
import unicodedata
import pandas as pd
from classificador_tipo_despesa import determinar_tipo_despesa

# Lista de empreendimentos
empreendimentos = [
    "Atlantic House", "Beach Dream", "Burj Exclusive", "Costa Rica", "Dublin",
    "Emirates Tower", "Flats Le Rêve", "Ilhas Baleares", "Jardim Itália",
    "Londres Residence", "Los Angeles", "Majestic", "Mar De Beaufort",
    "Monte Solaro", "Nizuc", "Ocean Garden", "Paris Sg", "Residencial San Diego",
    "Riomaggiore", "Selent Palace", "Selenter See", "Vancouver", "Administrativo"
]

# Função para remover acentos
def remover_acentos(texto):
    if isinstance(texto, str):
        nfkd = unicodedata.normalize('NFKD', texto)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))
    return texto

# Função para processar os nomes dos empreendimentos
def tratar_nome_empreendimento(valor):
    if isinstance(valor, str):
        lista = valor.lower().split()
        if len(lista) > 1:
            # Casos mais específicos
            if lista[1] == "see":
                return "Selenter See"
            if lista[1] == "palace":
                return "Selent Palace"
            elif lista[1] == "san":
                return "Residencial San Diego"
            elif lista[0] == "londres":
                return "Londres Residence"
            elif lista[0] == "ilhas":
                return "Ilhas Baleares"
            elif lista[0] == "atlantic":
                return "Atlantic House"
            elif lista[0] == "jardim":
                return "Jardim Itália"
            elif lista[0] == "jardim":
                return "Jardim Itália"
            elif lista[0] == "flats":
                return "Flats Le Rêve"
            # Remover "Residencial" se não for "Residencial San Diego"
            if lista[0] == "residencial" and "san" not in lista:
                lista.pop(0)
        # Juntar a lista em string para remover parênteses
        nome_tratado = ' '.join(lista)
        # Remover qualquer coisa dentro de parênteses
        nome_tratado = re.sub(r"\(.*?\)", "", nome_tratado).strip()
        lista = nome_tratado.split()
        if lista and lista[-1] == "residence":
            lista.pop(-1)
        nome_tratado = ' '.join(lista).strip()
        nome_tratado = nome_tratado.rstrip(" -")
        return nome_tratado.title()  # Primeiras letras em maiúsculas
    return valor

def tratamento(df):
    df["Obra"] = df["Obra"].fillna("Administrativo")
    df["Origem"] = df["Origem"].fillna("Sem preenchimento")
    df["Empreendimento"] = df["Obra"].apply(remover_acentos)
    df["Empreendimento"] = df["Empreendimento"].apply(tratar_nome_empreendimento)
    df["Empreendimento"] = df["Empreendimento"].replace({
        'Obra Da Sede Agv Selent': 'Jardim Itália',
        'Despesas Particulares': 'Administrativo',
        'Escritorio/Administrativo Agvs': 'Administrativo',
        'Obra Rua 272/274 - A Definir Nome' :'Administrativo',
        'Imoveis De Terceiro' : 'Administrativo',
        'Escritorio 252' : 'Administrativo',
        'Obras Terceiros Gerais' : 'Administrativo',
        'Obra Rua 292 - A Definir Nome' : 'Administrativo',
        'Obra Rua Luiz Walendowsky C/ Rua Valmor Serpa - A Definir Nome' : 'Administrativo'
        
    })
    return df

def tipo_despesa(df):
    #Consulta do históricos de lançamentos já realizados
    hist_lancamentos = pd.read_excel("keywords/keywords.xlsx", header=0)
    hist_lancamentos["Descrição"] = hist_lancamentos["Descrição"].str.lower()
    #Criação de um dicionário da descrição com o tipo de despesa
    dict_hist = dict(zip(hist_lancamentos['Descrição'], hist_lancamentos['Tipo de despesa']))
    
    tipos_despesa = []
    for origem, descricao, obra, empreendimento in zip(df["Origem"], df["Descrição"], df["Obra"], df["Empreendimento"]):
        tipo_excel = dict_hist.get(str(descricao).lower(), None)
        if tipo_excel:
            tipos_despesa.append(tipo_excel)
        else:
            tipo_calculado = determinar_tipo_despesa(origem, descricao, obra, empreendimento)
            tipos_despesa.append(tipo_calculado)
    df["Tipo de despesa"] = tipos_despesa
    return df

# Função principal que irá ler e processar os arquivos
def processar_relatorios(download_dir):
    # Lê os arquivos baixados
    arquivo_baixado = os.path.join(download_dir, "rel_conta_pagar.xls")
    arquivo_baixado_1 = os.path.join(download_dir, "rel_conta_pagar (1).xls")
    arquivo_baixado_2 = os.path.join(download_dir, "rel_conta_receber.xls")
    arquivo_baixado_3 = os.path.join(download_dir, "rel_conta_receber (1).xls")

    # Lê os arquivos HTML baixados com pandas
    df_contas_pagas = pd.read_html(arquivo_baixado, header=0, thousands= '.')[0]
    df_contas_a_pagar = pd.read_html(arquivo_baixado_1, header=0, thousands= '.')[0]
    df_contas_a_receber = pd.read_html(arquivo_baixado_2, header=0, thousands= '.')[0]
    df_contas_recebidas = pd.read_html(arquivo_baixado_3, header=0, thousands= '.')[0]
    
    df_contas_a_receber = df_contas_a_receber.drop(columns=["Tipo", df_contas_a_receber.columns[-1]])
    df_contas_a_pagar = df_contas_a_pagar.drop(columns=["Tipo", df_contas_a_pagar.columns[-1]])
    df_contas_pagas = df_contas_pagas.drop(columns=["Desc.", "Acresc.","Valor"])
    df_contas_recebidas = df_contas_recebidas.drop(columns=["Desc.", "Acresc.", "Valor"])
    
    # Aplica tratamento nos DataFrames
    df_contas_pagas = tratamento(df_contas_pagas)
    df_contas_a_pagar = tratamento(df_contas_a_pagar)
    df_contas_a_receber = tratamento(df_contas_a_receber)
    df_contas_recebidas = tratamento(df_contas_recebidas)
    
    df_contas_pagas = tipo_despesa(df_contas_pagas)
    df_contas_a_pagar = tipo_despesa(df_contas_a_pagar)

    #Remover a primeira linha
    df_contas_pagas = df_contas_pagas.dropna()
    df_contas_a_pagar = df_contas_a_pagar.dropna()
    df_contas_a_receber = df_contas_a_receber.dropna()
    df_contas_recebidas = df_contas_recebidas.dropna()

    df_contas_pagas['Total'] = df_contas_pagas['Total'].replace({r'\([^)]*\)': '0', r'\.': '', r',': '.'}, regex=True).astype(float)
    df_contas_a_pagar['Valor'] = df_contas_a_pagar['Valor'].replace({r'\([^)]*\)': '0', r'\.': '', r',': '.'}, regex=True).astype(float)
    df_contas_a_receber['Valor'] = df_contas_a_receber['Valor'].replace({r'\([^)]*\)': '0', r'\.': '', r',': '.'}, regex=True).astype(float)
    df_contas_recebidas['Total'] = df_contas_recebidas['Total'].replace({r'\([^)]*\)': '0', r'\.': '', r',': '.'}, regex=True).astype(float)

    df_contas_pagas = df_contas_pagas.set_index(df_contas_pagas.columns[0])
    df_contas_a_pagar = df_contas_a_pagar.set_index(df_contas_a_pagar.columns[0])
    df_contas_a_receber = df_contas_a_receber.set_index(df_contas_a_receber.columns[0])
    df_contas_recebidas = df_contas_recebidas.set_index(df_contas_recebidas.columns[0])

    return df_contas_pagas,df_contas_a_pagar,df_contas_a_receber,df_contas_recebidas

#%%
def normalizar(texto):
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode().lower()
    texto = re.sub(r'[^a-z\s]', ' ', texto)  # remove tudo que não for letra ou espaço
    return re.sub(r'\s+', ' ', texto).strip()  # remove espaços extras

# Dicionário de palavras-chave com lowercase
chaves_empreendimentos = {
    normalizar(emp): emp for emp in empreendimentos
}

def identificar_empreendimento(row):
    if pd.notna(row["Empreendimento"]):
        return row["Empreendimento"]
    
    texto = " ".join(
        str(row[col]) 
        for col in ["Descrição_x", "Descrição_y", "Dados Entrada", "Dados Saída"] 
        if pd.notna(row[col])
    )
    
    texto = normalizar(texto)  # AQUI entra a normalização!

    for chave, nome in chaves_empreendimentos.items():
        if chave in texto:
            return nome
    return np.nan

#%%
def saidas_negativas(contas_pagas,contas_a_pagar):
    #SAIDAS COM VALORES NEGATIVOS
    contas_pagas["Total"] = contas_pagas["Total"] *- 1
    contas_a_pagar["Valor"] = contas_a_pagar["Valor"] *- 1
    return contas_pagas, contas_a_pagar
#%%
#SUBSTITUINDO OS ZEROS PELO ULTIMO VALOR ENCONTRADO DA PARCELA RESPECTIVA
def corrigindo_zeros_contas_a_receber(contas_a_receber):
    # Cria um dicionário estilo "PROCV": {descricao: primeiro valor não-zero}
    procv_dict = contas_a_receber[contas_a_receber["Valor"] != 0].drop_duplicates("Descrição").set_index("Descrição")["Valor"].to_dict()
    
    # Substitui os zeros usando o dicionário
    contas_a_receber["Valor"] = contas_a_receber.apply(
        lambda row: procv_dict.get(row["Descrição"], 0) if row["Valor"] == 0 else row["Valor"],
        axis=1
    )
    return contas_a_receber
#%%
def exportar_dados_excel(df_recebidas, df_pagas, df_a_pagar, df_a_receber):
    base_path = "../data/processed"
    
    df_recebidas.to_excel(f"{base_path}\\contas_recebidas.xlsx", index=False)
    df_pagas.to_excel(f"{base_path}\\contas_pagas.xlsx", index=False)
    df_a_pagar.to_excel(f"{base_path}\\contas_a_pagar.xlsx", index=False)
    df_a_receber.to_excel(f"{base_path}\\contas_a_receber.xlsx", index=False)
#%%
def dre_final(dre_emp):
    # Agrupar o restante (sem as margens)
    dre_sem_margem = dre_emp[~dre_emp["Tipo de despesa"].str.contains("Margem")]
    
    # Agrupar por Empreendimento e Tipo de despesa (soma dos valores)
    dre_agrupado = dre_sem_margem.groupby(["Empreendimento", "Tipo de despesa"], as_index=False)["Valor"].sum()
    
    # Pivotar para facilitar o cálculo
    dre_pivot = dre_agrupado.pivot(index="Empreendimento", columns="Tipo de despesa", values="Valor")
    
    # Resetar índice para voltar ao formato original
    dre_final = dre_pivot.reset_index().melt(id_vars="Empreendimento", var_name="Tipo de despesa", value_name="Valor")
    
    return dre_final

#%%
def bens_realizado_projetado(caminho_rel_bens,caminho_contas_rebidas_bens):
        
    df_rel_bens = pd.read_html(caminho_rel_bens, header=0, thousands='.')[0]
    df_rel_bens = df_rel_bens.iloc[1:-2]
    df_rel_bens = df_rel_bens.dropna(subset=['Ref.'])

    df_contas_recebidas_bens = pd.read_html(caminho_contas_rebidas_bens, header=0, thousands='.')[0]
    df_contas_recebidas_bens = df_contas_recebidas_bens.iloc[1:-2]
    df_contas_recebidas_bens = tratamento(df_contas_recebidas_bens)

    #A PALAVRA ITENS É UM INDICADOR FORTE PARA IMOVEIS DE TERCEIROS
    filtro_itens = df_contas_recebidas_bens['Descrição'].str.contains(r'\bitens\b', case=False, na=False, regex=True)

    #Armazenando os dados encontrados que contem a palavra itens
    df_encontrados_itens = df_contas_recebidas_bens[filtro_itens].copy()

    # Converte as colunas para número, removendo pontos e trocando vírgula por ponto
    df_encontrados_itens['Total'] = df_encontrados_itens['Total'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    df_rel_bens['Valor Ent.'] = df_rel_bens['Valor Ent.'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    df_rel_bens['Valor Saida'] = df_rel_bens['Valor Saida'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    df_rel_bens['Diferença'] = df_rel_bens['Diferença'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

    #Criando ID para que eu consigo unir contas recebidas(com os imoveis identificados) com relatório de bens de permuta
    df_encontrados_itens["ID"] = df_encontrados_itens['Origem'].astype(str) + ' - ' + df_encontrados_itens['Total'].astype(str)
    df_rel_bens["ID"] = df_rel_bens['Dados Entrada'].astype(str) + ' - ' + df_rel_bens['Valor Ent.'].astype(str)

    # Adiciona um contador para cada duplicata (0, 1, 2...) dentro de cada grupo de ID
    df_encontrados_itens['temp_dup_count'] = df_encontrados_itens.groupby('ID').cumcount()
    df_rel_bens['temp_dup_count'] = df_rel_bens.groupby('ID').cumcount()

    # Faz o merge usando ID + contador temporário
    df_merge = pd.merge(df_encontrados_itens,df_rel_bens,how="outer",on=["ID", "temp_dup_count"])  # Agora o merge respeita a ordem dos duplicados
    df_merge = df_merge.drop(columns=['temp_dup_count']) # Remove a coluna auxiliar se não for mais necessária

    # Divide os dados conforme existência ou não de "Valor Ent."
    # SE FOI VENDIDO TERA VALOR DE ENTRADA
    df_bens_realizado = df_merge[df_merge["Valor Saida"].notna()].copy()
    df_bens_projetado = df_merge[df_merge["Valor Saida"].isna()].copy()

    # Aplica apenas nas linhas com Empreendimento vazio
    df_bens_realizado.loc[df_bens_realizado["Empreendimento"].isna(), "Empreendimento"] = df_bens_realizado[df_bens_realizado["Empreendimento"].isna()].apply(identificar_empreendimento, axis=1)
    return df_bens_realizado, df_bens_projetado

#%%
#Configurações globais
CONFIG = {
    'categorias': {
        "(+) Entradas Operacionais": 0,
        "(-) Impostos": 1,
        "(-) Distratos": 2,
        "(=) Entrada Operacional Líquida": 3,
        "(-) Custos Operacionais": 4,
        "(-) Comissão": 5,
        "(=) Fluxo de Caixa Operacional": 6,
        "Margem Bruta %": 7,
        "(-) Despesas Operacionais e Administrativas": 8,
        "(=) EBIT": 9,
        "Margem EBIT %": 10,
        "(+/-) Resultado Financeiro": 11,
        "(=) Fluxo de Caixa Livre": 12,
        "Margem Líquida %": 13
    },
    'empreendimentos': [
        "Atlantic House", "Beach Dream", "Burj Exclusive", "Costa Rica", "Dublin",
        "Emirates Tower", "Flats Le Rêve", "Ilhas Baleares", "Jardim Itália",
        "Londres Residence", "Los Angeles", "Majestic", "Mar De Beaufort",
        "Monte Solaro", "Nizuc", "Ocean Garden", "Paris Sg", "Residencial San Diego",
        "Riomaggiore", "Selent Palace", "Selenter See", "Vancouver", "Administrativo"
    ],
    'datas_completas': pd.date_range("2010-01-01", "2025-05-01", freq="M").strftime("%Y-%m").tolist(),
    'datas_recentes': pd.date_range("2010-01-01", "2025-05-01", freq="M").strftime("%Y-%m").tolist()
}

def processar_bens_por_empreendimento(df_bens_realizado, df_bens_projetado, dre_final):
    # --- Realizado ---
    empreendimentos_identificados = df_bens_realizado[df_bens_realizado["Empreendimento"].notna()].copy()

    df_bens_emp_real = empreendimentos_identificados.groupby(
        ["Empreendimento"], as_index=False
    )["Valor Saida"].sum()

    # --- Projetado ---
    df_bens_projetado.loc[
        df_bens_projetado["Empreendimento"].isna(), "Empreendimento"
    ] = df_bens_projetado[df_bens_projetado["Empreendimento"].isna()].apply(
        identificar_empreendimento, axis=1
    )

    empreendimentos_nao_identificados_proj = df_bens_projetado[df_bens_projetado["Empreendimento"].isna()].copy()
    empreendimentos_nao_identificados_proj.to_excel("data/processed/bens_nao_identificados_proj.xlsx")

    empreendimentos_identificados_proj = df_bens_projetado[df_bens_projetado["Empreendimento"].notna()].copy()

    df_bens_emp_proj = empreendimentos_identificados_proj.groupby(
        ["Empreendimento"], as_index=False
    )["Valor Ent."].sum()

    # Reindexar para garantir todos os empreendimentos, preenchendo com 0 onde não houver dados
    df_bens_emp_proj = (
        df_bens_emp_proj.set_index("Empreendimento")
        .reindex(CONFIG["empreendimentos"], fill_value=0)
        .reset_index()
    )

    # Adiciona a coluna "Tipo de despesa" e renomeia
    df_bens_emp_real["Tipo de despesa"] = "(+) Receita Imóveis de terceiros"
    df_bens_emp_proj["Tipo de despesa"] = "(+) Receita Imóveis de terceiros"

    df_bens_emp_real.rename(columns={"Valor Saida": "Valor"}, inplace=True)
    df_bens_emp_proj.rename(columns={"Valor Ent.": "Valor"}, inplace=True)

    df_emp_realizado = pd.concat([dre_final, df_bens_emp_real])
    df_emp_realizado["Numeração"] = df_emp_realizado["Tipo de despesa"].map(CONFIG["categorias"])

    return df_emp_realizado
#%%

