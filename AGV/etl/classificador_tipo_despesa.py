#%%============================== BIBLIOTECAS =================================
import re
from tratar_nome_empreendimento import remover_acentos

#%%============================== FUNÇÕES =====================================

# Função para determinar o tipo de despesa
def determinar_tipo_despesa(origem, descricao, obra, empreendimento):
    # Remover acentos e padronizar
    origem = remover_acentos(origem.lower()) if isinstance(origem, str) else ""
    descricao = remover_acentos(descricao.lower()) if isinstance(descricao, str) else ""
    obra = obra.lower() if isinstance(obra, str) else ""
    empreendimento = empreendimento.lower() if isinstance(empreendimento, str) else ""

    # Listas de palavras-chave
    origem_tokens = re.split(r'[ ,\-\;]', origem)
    descricao_tokens = re.split(r'[ ,\-\;]', descricao)
    empreendimento_tokens = re.split(r'[ ,\-\;]', empreendimento)

    # Verificações"
    #========= IMPOSTOS =======================================================
    if any(palavra in ["darf", "inss"] for palavra in origem_tokens):
        return "(-) Impostos"
    #========= COMISSAO =======================================================
    elif any(palavra in ["comissao"] for palavra in descricao_tokens):
        return "(-) Comissão"
    #========= DISTRATOS ======================================================
    elif any(palavra in ["distrato", "devolução"] for palavra in descricao_tokens):
        return "(-) Distratos"
    #========= CUSTOS OPERACIONAIS ============================================
    elif ("administrativo" not in empreendimento_tokens and 
          "darf" not in origem_tokens and 
          not any(palavra in ["distrato", "devolução"] for palavra in descricao_tokens)):
        return "(-) Custos Operacionais" 
    #========= DESPESAS FINANCEIRAS ===========================================
    elif any(palavra in ["tarifa","emprestimo", "parcelamento", "credito","divida"] for palavra in descricao_tokens):
        return "(-) Despesas Financeiras"
    elif any(palavra in ["sicoob"] for palavra in origem_tokens):
        return "(-) Despesas Financeiras"
    #========= DESPESAS OPERACIONAIS E ADMINISTRATIVAS ========================
    else:
        return "(-) Despesas Operacionais e Administrativas"

'''
# Função para buscar tipo de despesa através da lista
def buscar_tipo_despesa(df_listas, descricao):
    resultado = df_listas.loc[df_listas['Descrição'] == descricao, 'Tipo de despesa']
    return resultado.iloc[0] if not resultado.empty else None
'''

