#%%============================== BIBLIOTECAS =================================
import pandas as pd
import unicodedata

#%%=============================== FUNÇÕES ==================================

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
        
        # Remover palavras específicas
        if lista and lista[0].lower() in ["residencial"]:
            lista.pop(0)
        if lista and lista[0] in ["atlantic"]:
            return "Atlantic House"
        if len(lista) > 1 and lista[1] in ["see"]:
            return "Selenter See"
        if lista and lista[0] in ["ilhas"]:
            return "Ilhas Baleares"
        if lista and lista[-1] in ["residence", "(entregue)","(escritorio)"]:
            lista.pop(-1)
        if len(lista) >= 2 and lista[-2] == "(entregue":
            lista.pop(-2)
            lista.pop(-1)
            if lista and lista[-1] in ["residence"]:
                lista.pop(-1)
        
        nome_tratado = ' '.join(lista).strip()
        if nome_tratado in ["obras terceiros gerais", "escritório/administrativo agvs", "", "nan"] or pd.isna(valor) or pd.isnull(valor):
            return "Administrativo"
        if nome_tratado in ["Escritorio 252", "Imoveis De Terceiros", "obra rua 272/274 - a definir nome"]:
            return "Administrativo"
        if nome_tratado.endswith(" -"):
            nome_tratado = nome_tratado.rstrip(" -")
        
        return nome_tratado.title()  # Primeiras letras em maiúsculas
    return valor
