#IMPORTANDO BIBLIOTECAS
from tratamento_agv import empreendimentos,processar_relatorios,identificar_empreendimento, saidas_negativas , corrigindo_zeros_contas_a_receber, exportar_dados_excel, dre_final,bens_realizado_projetado
from calculo_dre import gerar_dre,CONFIG,CONFIG2
import pandas as pd
#%%
#DEFININDO DIRETORIOS DE CONTAS PAGAS,A PAGAR,RECEBIDAS E A RECEBER
diretorio = "../data/raw"

#Tratamento dos dados
df_contas_pagas, df_contas_a_pagar, df_contas_a_receber, df_contas_recebidas = processar_relatorios(diretorio)

#%% AJUSTANDO AS SAÍDAS PARA TER VALOR NEGATIVO
df_contas_pagas, df_contas_a_pagar = saidas_negativas(df_contas_pagas, df_contas_a_pagar)

#%%CONTAS A RECEBER TEM LANÇAMENTOS ZERADOS NO FUTURO(ISSO AFETA AS PROJEÇÕES)
df_contas_a_receber = corrigindo_zeros_contas_a_receber(df_contas_a_receber)

#%% EXPORTAR CONTAS CLASSIFICADAS
df_contas_recebidas.to_excel("../data/processed/contas_recebidas.xlsx")
df_contas_pagas.to_excel("../data/processed/contas_pagas.xlsx")
df_contas_a_pagar.to_excel("../data/processed/contas_a_pagar.xlsx")
df_contas_a_receber.to_excel("../data/processed/contas_a_receber.xlsx")

#%% CALCULO DRE
dre_emp, dre_glob, dre_hist = gerar_dre(df_contas_recebidas, df_contas_pagas)

# Exportar para Excel
dre_emp.to_excel("../data/processed/dre_empreendimento.xlsx", index=False)
dre_glob.to_excel("../data/processed/dre_global.xlsx", index=False)
dre_hist.to_excel("../data/processed/dre_hist.xlsx", index=False)

dre_final = dre_final(dre_emp)

#%% IDENTIFICAÇÃO DE BENS DE PERMUTA
caminho_rel_bens = "../data/raw/rel_contrato.xls"
caminho_contas_rebidas_bens = "../data/raw/rel_conta_receber (1).xls"

df_bens_realizado, df_bens_projetado = bens_realizado_projetado(caminho_rel_bens,caminho_contas_rebidas_bens)

#%% BENS COM EMPREENDIMENTOS NAO IDENTIFICADOS
# Filtra as linhas que continuam com Empreendimento como NaN
empreendimentos_nao_identificados_real = df_bens_realizado[df_bens_realizado["Empreendimento"].isna()].copy()
empreendimentos_nao_identificados_real.to_excel("../data/processed/bens_nao_identificados_real.xlsx")

#%% 
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
    empreendimentos_nao_identificados_proj.to_excel("../data/processed/bens_nao_identificados_proj.xlsx")

    empreendimentos_identificados_proj = df_bens_projetado[df_bens_projetado["Empreendimento"].notna()].copy()

    df_bens_emp_proj = empreendimentos_identificados_proj.groupby(
        ["Empreendimento"], as_index=False
    )["Valor Ent."].sum()

    # Reindexar para garantir todos os empreendimentos, preenchendo com 0 onde não houver dados
    df_bens_emp_proj = (
        df_bens_emp_proj.set_index("Empreendimento")
        .reindex(CONFIG2["empreendimentos"], fill_value=0)
        .reset_index()
    )

    # Adiciona a coluna "Tipo de despesa" e renomeia
    df_bens_emp_real["Tipo de despesa"] = "(+) Receita Imóveis de terceiros"
    df_bens_emp_proj["Tipo de despesa"] = "(+) Receita Imóveis de terceiros"

    df_bens_emp_real.rename(columns={"Valor Saida": "Valor"}, inplace=True)
    df_bens_emp_proj.rename(columns={"Valor Ent.": "Valor"}, inplace=True)

    df_emp_realizado = pd.concat([dre_final, df_bens_emp_real])
    df_emp_realizado["Numeração"] = df_emp_realizado["Tipo de despesa"].map(CONFIG["categorias"])

    return df_emp_realizado,df_bens_emp_proj

df_emp_realizado, df_bens_emp_proj = processar_bens_por_empreendimento(df_bens_realizado, df_bens_projetado, dre_final)

#%%
def pivot_df(df):
    # 1. Pivotar para ter "Receita Vendas" e "Receita Imóveis" em colunas separadas
    pivot_df = df.pivot_table(
        index="Empreendimento",
        columns="Tipo de despesa",
        values="Valor",
        aggfunc="sum"
    ).reset_index()
    return pivot_df

def calc_pivot(pivot_df):
    pivot_df["(+) Receita Estoque"] = 0

    pivot_df["(=) Receita Líquida"] = (
        pivot_df["(+) Receita Vendas"] + 
        pivot_df["(+) Receita Imóveis de terceiros"] +
        pivot_df["(-) Impostos"])
    
    pivot_df["(=) Lucro Bruto"] = (
        pivot_df["(=) Receita Líquida"] + 
        pivot_df["(-) Custos Operacionais"] +
        pivot_df["(-) Comissão"])
    
    pivot_df["(=) Lucro Líquido"] = (
        pivot_df["(=) Lucro Bruto"] + 
        pivot_df["(-) Despesas Financeiras"] +
        pivot_df["(-) Despesas Operacionais e Administrativas"])
    return pivot_df

def long_df(df):
    # Agora, voltando ao formato original (long format)
    df2 = df.melt(
        id_vars=["Empreendimento"],
        var_name="Tipo de despesa",
        value_name="Valor"
    ).dropna(subset=["Valor"])  # Remove linhas com NaN (se aplicável)
    return df2

pivot_df = pivot_df(df_emp_realizado)
pivot_df = pivot_df.rename(columns={'(+/-) Resultado Financeiro': '(-) Despesas Financeiras'})
pivot_df["(+) Receita Vendas"] = pivot_df["(+) Entradas Operacionais"] - pivot_df["(+) Receita Imóveis de terceiros"]
pivot_df = calc_pivot(pivot_df)

df_emp_realizado = long_df(pivot_df)
df_emp_realizado["Numeração"] = df_emp_realizado["Tipo de despesa"].map(CONFIG2["categorias"])
df_emp_realizado["Tipo de despesa"] = df_emp_realizado["Tipo de despesa"].replace("(+/-) Resultado Financeiro", "(-) Despesas Financeiras")

df_emp_realizado = df_emp_realizado.reset_index(drop=True)
df_emp_realizado = df_emp_realizado.dropna()

#%%
# Agrupamentos
df_proj1 = df_contas_a_pagar.groupby(["Empreendimento", "Tipo de despesa"], as_index=False)["Valor"].sum()
df_proj2 = df_contas_a_receber.groupby("Empreendimento", as_index=False)["Valor"].sum()

df_proj2["Tipo de despesa"] = "(+) Receita Vendas"

# Junta os dois
df_ambos = pd.concat([df_proj1, df_proj2], ignore_index=True)

# Cria o dataframe base com todas combinações possíveis de Empreendimento x Tipo de despesa
tipos = df_ambos["Tipo de despesa"].unique()
df_base = pd.MultiIndex.from_product([empreendimentos, tipos], names=["Empreendimento", "Tipo de despesa"]).to_frame(index=False)

# Junta com os valores reais
df_emp_proj = df_base.merge(df_ambos, on=["Empreendimento", "Tipo de despesa"], how="left")
df_emp_proj["Valor"] = df_emp_proj["Valor"].fillna(0)

df_emp_proj2 = pd.concat([df_emp_proj,df_bens_emp_proj])

pivot_df = df_emp_proj2.pivot_table(
    index="Empreendimento",
    columns="Tipo de despesa",
    values="Valor",
    aggfunc="sum"
).reset_index()

df_emp_proj_pivot = calc_pivot(pivot_df)

df_emp_proj = long_df(df_emp_proj_pivot)

df_emp_proj2["Numeração"] = df_emp_proj2["Tipo de despesa"].map(CONFIG2["categorias"])

df_emp_proj2["Tipo de despesa"] = df_emp_proj2["Tipo de despesa"].replace("(+/-) Resultado Financeiro", "(-) Despesas Financeiras")

df_emp_proj2.to_excel("../data/processed/resultado_proj.xlsx")
#%%
df_emp_total = pd.DataFrame()
df_emp_total["Empreendimento"] = df_emp_realizado["Empreendimento"]
df_emp_total["Tipo de despesa"] = df_emp_realizado["Tipo de despesa"]

# Suponha que seus dois DataFrames se chamem df1 e df2
df_concat = pd.concat([df_emp_realizado, df_emp_proj2], ignore_index=True)

# Agrupa pelas colunas que formam a chave única e soma os valores
df_somado = df_concat.groupby(["Empreendimento", "Tipo de despesa", "Numeração"], as_index=False)["Valor"].sum()

pivot_df = df_somado.pivot_table(
    index="Empreendimento",
    columns="Tipo de despesa",
    values="Valor",
    aggfunc="sum"
).reset_index()

pivot_df["Margem Bruta %"] = 100 * (pivot_df["(=) Lucro Bruto"] / pivot_df["(=) Receita Líquida"])

pivot_df["Margem Líquida %"] = 100 * (pivot_df["(=) Lucro Líquido"] / pivot_df["(=) Receita Líquida"])

# Agora, voltando ao formato original (long format)
df_somado = pivot_df.melt(
    id_vars=["Empreendimento"],
    var_name="Tipo de despesa",
    value_name="Valor"
).dropna(subset=["Valor"])  # Remove linhas com NaN (se aplicável)

df_somado["Numeração"] = df_somado["Tipo de despesa"].map(CONFIG2["categorias"])

df_somado.to_excel("../data/processed/resultado_total.xlsx")
