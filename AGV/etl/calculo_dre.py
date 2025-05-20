import pandas as pd
import numpy as np

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

def preparar_dados(df_recebidas, df_pagas):
    """Prepara os dados brutos combinando recebimentos e pagamentos"""
    # Resetar índices para garantir que todas as colunas estejam acessíveis
    df_recebidas = df_recebidas.reset_index()
    df_pagas = df_pagas.reset_index()
    
    df_recebidas["Tipo de despesa"] = "(+) Entradas Operacionais"
    df = pd.concat([df_recebidas, df_pagas], ignore_index=True)
    
    # Verifica se 'Dt.Pgto' está no índice ou nas colunas
    if 'Dt.Pgto' not in df.columns and 'Dt.Pgto' in df.index.names:
        df = df.reset_index()
    
    # Agora podemos acessar 'Dt.Pgto' com segurança
    df["Dt.Pgto"] = pd.to_datetime(df["Dt.Pgto"], dayfirst=True)
    df["Ano-Mes"] = df["Dt.Pgto"].dt.to_period("M").astype(str)
    df["Tipo de despesa"] = df["Tipo de despesa"].replace(
        {"(-) Despesas Financeiras": "(+/-) Resultado Financeiro"}
    )
    
    return df

def criar_dataframes_por_tipo(df, index, columns, fill_value=0):
    """Cria DataFrames pivotados para cada tipo de despesa garantindo todos os empreendimentos"""
    dfs = {}
    
    for tipo in df["Tipo de despesa"].unique():
        # Filtra os dados para o tipo atual
        df_tipo = df[df["Tipo de despesa"] == tipo]
        
        # Cria pivot table, usando 'Empreendimento' como index se fornecido
        pivot = df_tipo.pivot_table(
            values="Total",
            index="Empreendimento" if index is not None else None,
            columns="Ano-Mes",
            aggfunc="sum",
            fill_value=fill_value
        )
        
        # Garante a estrutura completa do DataFrame
        if index is not None:
            pivot = pivot.reindex(index=index, columns=columns, fill_value=fill_value)
        else:
            pivot = pivot.reindex(columns=columns, fill_value=fill_value)
        
        dfs[tipo] = pivot
    
    # Garante que todos os tipos de despesa existam, mesmo que vazios
    for tipo in CONFIG['categorias']:
        if tipo not in dfs:
            if index is not None:
                dfs[tipo] = pd.DataFrame(fill_value, index=index, columns=columns)
            else:
                dfs[tipo] = pd.DataFrame(fill_value, index=[0], columns=columns)
    
    return dfs

def calcular_metricas(dfs):
    """Calcula as métricas financeiras derivadas"""
    # Cálculos básicos
    dfs["(=) Entrada Operacional Líquida"] = (
        dfs.get("(+) Entradas Operacionais", 0) +
        dfs.get("(-) Distratos", 0) +
        dfs.get("(-) Impostos", 0)
    )
    
    dfs["(=) Fluxo de Caixa Operacional"] = (
        dfs["(=) Entrada Operacional Líquida"] +
        dfs.get("(-) Custos Operacionais", 0) +
        dfs.get("(-) Comissão", 0)
    )
    
    dfs["(=) EBIT"] = (
        dfs["(=) Fluxo de Caixa Operacional"] +
        dfs.get("(-) Despesas Operacionais e Administrativas", 0)
    )
    
    dfs["(=) Fluxo de Caixa Livre"] = (
        dfs["(=) EBIT"] +
        dfs.get("(+/-) Resultado Financeiro", 0)
    )
    
     # Cálculos de margem
    entrada_liquida = dfs["(=) Entrada Operacional Líquida"]
    
    dfs["Margem Bruta %"] = 1000 * 100 * (dfs["(=) Fluxo de Caixa Operacional"] / entrada_liquida)
    dfs["Margem EBIT %"] = 1000 *100 * (dfs["(=) EBIT"] / entrada_liquida)
    dfs["Margem Líquida %"] = 1000 * 100 * (dfs["(=) Fluxo de Caixa Livre"] / entrada_liquida)
    
    return dfs

def formatar_saida(dfs, categorias, index_name=None):
    """Formata os DataFrames para saída final"""
    df_unido = pd.concat(dfs, axis=0, keys=dfs.keys()).reset_index()
    df_unido.rename(columns={"level_0": "Tipo de despesa"}, inplace=True)
    
    if index_name:
        df_unido.rename(columns={"level_1": index_name}, inplace=True)
    
    # Remover a coluna 'level_1' se não foi renomeada (quando index_name é None)
    if 'level_1' in df_unido.columns and index_name is None:
        df_unido.drop(columns=['level_1'], inplace=True)
    
    df_unido["Numeração"] = df_unido["Tipo de despesa"].map(categorias)
    
    id_vars = ["Tipo de despesa", "Numeração"]
    if index_name:
        id_vars.append(index_name)
    
    # Garantir que não incluímos a coluna 'Total' no melt
    colunas_valor = [col for col in df_unido.columns if col not in id_vars and col != 'Total']
    
    df_final = df_unido.melt(
        id_vars=id_vars,
        value_vars=colunas_valor,  # Especificar apenas as colunas de data
        var_name="Data",
        value_name="Valor"
    )
    
    return df_final.sort_values("Numeração")

def gerar_dre(df_recebidas, df_pagas):
    """Função principal que gera todos os relatórios"""
    # Preparar dados base
    df = preparar_dados(df_recebidas, df_pagas)
    
    # Relatório por empreendimento
    dfs_empreendimentos = criar_dataframes_por_tipo(
        df, 
        index=CONFIG['empreendimentos'], 
        columns=CONFIG['datas_completas']
    )
    dfs_empreendimentos = calcular_metricas(dfs_empreendimentos)
    dre_empreendimentos = formatar_saida(
        dfs_empreendimentos, 
        CONFIG['categorias'], 
        index_name="Empreendimento"
    )
    
    # Relatório global
    df_global = df.groupby(["Tipo de despesa", "Ano-Mes"], as_index=False)["Total"].sum()
    dfs_global = criar_dataframes_por_tipo(
        df_global,
        index=None,
        columns=CONFIG['datas_recentes']
    )
    dfs_global = calcular_metricas(dfs_global)
    dre_global = formatar_saida(dfs_global, CONFIG['categorias'])
    

    # Trata infinitos nos dois DataFrames
    dre_empreendimentos = dre_empreendimentos.replace([np.inf, -np.inf, np.nan], 0)
    dre_global = dre_global.replace([np.inf, -np.inf, np.nan], 0)
    dre_hist = dre_empreendimentos.pivot_table(
    index=['Tipo de despesa', 'Numeração', 'Empreendimento'],
        columns='Data',
        values='Valor',
        fill_value=0
    ).reset_index()
    
    # Exportar para Excel
    dre_empreendimentos.to_excel("../data/processed/dre_empreendimento.xlsx", index=False)
    dre_global.to_excel("../data/processed/dre_global.xlsx", index=False)
    dre_hist.to_excel("../data/processed/dre_hist.xlsx", index=False)
    return dre_empreendimentos, dre_global, dre_hist
#%%
#Configurações globais
CONFIG2 = {
    'categorias': {
        "(+) Receita Vendas": 0,
        "(+) Receita Estoque": 1,
        "(+) Receita Imóveis de terceiros": 2,
        "(-) Impostos": 3,
        "(=) Receita Líquida": 4,
        "(-) Comissão": 5,
        "(-) Custos Operacionais": 6,
        "(=) Lucro Bruto": 7,
        "Margem Bruta %": 8,
        "(-) Despesas Operacionais e Administrativas": 9,
        "(-) Despesas Financeiras": 10,
        "(-) Distratos": 11,
        "(=) Lucro Líquido": 12,
        "Margem Líquida %": 13
    },'empreendimentos': [
        "Atlantic House", "Beach Dream", "Burj Exclusive", "Costa Rica", "Dublin",
        "Emirates Tower", "Flats Le Rêve", "Ilhas Baleares", "Jardim Itália",
        "Londres Residence", "Los Angeles", "Majestic", "Mar De Beaufort",
        "Monte Solaro", "Nizuc", "Ocean Garden", "Paris Sg", "Residencial San Diego",
        "Riomaggiore", "Selent Palace", "Selenter See", "Vancouver", "Administrativo"
    ]
    }