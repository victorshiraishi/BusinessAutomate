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

#%% Função para processar bens por empreendimento
def processar_bens_por_empreendimento(df_bens_realizado, df_bens_projetado, dre_final, CONFIG, CONFIG2):
    # Realizado
    empreendimentos_identificados = df_bens_realizado[df_bens_realizado["Empreendimento"].notna()].copy()
    df_bens_emp_real = empreendimentos_identificados.groupby("Empreendimento", as_index=False)["Valor Saida"].sum()

    # Projetado
    df_bens_projetado.loc[df_bens_projetado["Empreendimento"].isna(), "Empreendimento"] = (
        df_bens_projetado[df_bens_projetado["Empreendimento"].isna()].apply(identificar_empreendimento, axis=1)
    )

    empreendimentos_nao_identificados_proj = df_bens_projetado[df_bens_projetado["Empreendimento"].isna()].copy()
    empreendimentos_nao_identificados_proj.to_excel("../data/processed/bens_nao_identificados_proj.xlsx")

    empreendimentos_identificados_proj = df_bens_projetado[df_bens_projetado["Empreendimento"].notna()].copy()
    df_bens_emp_proj = empreendimentos_identificados_proj.groupby("Empreendimento", as_index=False)["Valor Ent."].sum()

    df_bens_emp_proj = (
        df_bens_emp_proj.set_index("Empreendimento")
        .reindex(CONFIG2["empreendimentos"], fill_value=0)
        .reset_index()
    )

    # Formatação
    df_bens_emp_real["Tipo de despesa"] = "(+) Receita Imóveis de terceiros"
    df_bens_emp_proj["Tipo de despesa"] = "(+) Receita Imóveis de terceiros"

    df_bens_emp_real.rename(columns={"Valor Saida": "Valor"}, inplace=True)
    df_bens_emp_proj.rename(columns={"Valor Ent.": "Valor"}, inplace=True)

    df_emp_realizado = pd.concat([dre_final, df_bens_emp_real])
    df_emp_realizado["Numeração"] = df_emp_realizado["Tipo de despesa"].map(CONFIG["categorias"])

    return df_emp_realizado, df_bens_emp_proj

#%% Função para pivotar o dataframe
def pivot_df(df):
    return df.pivot_table(
        index="Empreendimento",
        columns="Tipo de despesa",
        values="Valor",
        aggfunc="sum"
    ).reset_index()

#%% Função para calcular totais da pivot
def calc_pivot(df):
    df["(+) Receita Estoque"] = 0

    df["(=) Receita Líquida"] = (
        df.get("(+) Receita Vendas", 0) +
        df.get("(+) Receita Imóveis de terceiros", 0) +
        df.get("(-) Impostos", 0)
    )

    df["(=) Lucro Bruto"] = (
        df["(=) Receita Líquida"] +
        df.get("(-) Custos Operacionais", 0) +
        df.get("(-) Comissão", 0)
    )

    df["(=) Lucro Líquido"] = (
        df["(=) Lucro Bruto"] +
        df.get("(-) Despesas Financeiras", 0) +
        df.get("(-) Despesas Operacionais e Administrativas", 0)
    )
    return df

#%% Função para converter pivot para long
def long_df(df):
    return df.melt(
        id_vars=["Empreendimento"],
        var_name="Tipo de despesa",
        value_name="Valor"
    ).dropna(subset=["Valor"])

#%% Função para preparar dados projetados (contas a pagar/receber)
def preparar_proj(df_contas_a_pagar, df_contas_a_receber, df_bens_emp_proj, emp):
    df_proj1 = df_contas_a_pagar.groupby(["Empreendimento", "Tipo de despesa"], as_index=False)["Valor"].sum()
    df_proj2 = df_contas_a_receber.groupby("Empreendimento", as_index=False)["Valor"].sum()
    df_proj2["Tipo de despesa"] = "(+) Receita Vendas"

    df_ambos = pd.concat([df_proj1, df_proj2], ignore_index=True)

    tipos = df_ambos["Tipo de despesa"].unique()
    df_base = pd.MultiIndex.from_product([emp, tipos], names=["Empreendimento", "Tipo de despesa"]).to_frame(index=False)

    df_emp_proj = df_base.merge(df_ambos, on=["Empreendimento", "Tipo de despesa"], how="left")
    df_emp_proj["Valor"] = df_emp_proj["Valor"].fillna(0)

    df_emp_proj2 = pd.concat([df_emp_proj, df_bens_emp_proj])
    return df_emp_proj2

#%% Função para calcular totais combinando realizado + projetado
def calcular_totais(df_emp_realizado, df_emp_proj2, CONFIG2):
    df_concat = pd.concat([df_emp_realizado, df_emp_proj2], ignore_index=True)

    df_somado = df_concat.groupby(["Empreendimento", "Tipo de despesa", "Numeração"], as_index=False)["Valor"].sum()

    pivot_df_final = pivot_df(df_somado)
    pivot_df_final["Margem Bruta %"] = 100 * (pivot_df_final["(=) Lucro Bruto"] / pivot_df_final["(=) Receita Líquida"])
    pivot_df_final["Margem Líquida %"] = 100 * (pivot_df_final["(=) Lucro Líquido"] / pivot_df_final["(=) Receita Líquida"])

    df_final_long = long_df(pivot_df_final)
    df_final_long["Numeração"] = df_final_long["Tipo de despesa"].map(CONFIG2["categorias"])

    return df_final_long

#%%
# Etapa 1: Processar bens
df_emp_realizado, df_bens_emp_proj = processar_bens_por_empreendimento(df_bens_realizado, df_bens_projetado, dre_final, CONFIG, CONFIG2)

# Etapa 2: Calcular pivot do realizado
pivot = pivot_df(df_emp_realizado)
pivot = pivot.rename(columns={'(+/-) Resultado Financeiro': '(-) Despesas Financeiras'})
pivot["(+) Receita Vendas"] = pivot["(+) Entradas Operacionais"] - pivot["(+) Receita Imóveis de terceiros"]
pivot = calc_pivot(pivot)

# Etapa 3: Voltar para long
df_emp_realizado = long_df(pivot)
df_emp_realizado["Numeração"] = df_emp_realizado["Tipo de despesa"].map(CONFIG2["categorias"])

# Etapa 4: Preparar projetado
df_emp_proj2 = preparar_proj(df_contas_a_pagar, df_contas_a_receber, df_bens_emp_proj, CONFIG2["empreendimentos"])
df_emp_proj2["Numeração"] = df_emp_proj2["Tipo de despesa"].map(CONFIG2["categorias"])

# Etapa 5: Salvar resultado projetado
df_emp_proj2.to_excel("../data/processed/resultado_proj.xlsx", index=False)

# Etapa 6: Calcular totais combinados
df_total = calcular_totais(df_emp_realizado, df_emp_proj2, CONFIG2)
df_total.to_excel("../data/processed/resultado_total.xlsx", index=False)
