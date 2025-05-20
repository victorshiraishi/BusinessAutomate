import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

def acessar_relatorios(data_ini, data_fim):
    # Caminho do diretório onde os arquivos serão salvos, incluindo a data de hoje
    data_atual = datetime.now().strftime("%Y-%m-%d")
    download_dir = os.path.join(r"C:\Users\conta\OneDrive - L.M.D.M. - CONSULTORIA EMPRESARIAL LTDA\Documentos\Projeto de Automação - BI 1.0\1 - DADOS BRUTOS", f"relatorios_{data_atual}")
    
    # Cria a pasta com a data de hoje, caso não exista
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Configurações do Chrome para salvar o arquivo no diretório especificado
    chrome_options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": download_dir}
    chrome_options.add_experimental_option("prefs", prefs)

    # Inicializa o navegador com as opções configuradas
    navegador = webdriver.Chrome(options=chrome_options)

    # Acessa a página de login
    navegador.get('https://agv.proobra.net.br/login.php')
    navegador.maximize_window()

    # Realiza o login
    navegador.find_element(By.ID, "login").send_keys("Auditoria")
    navegador.find_element(By.ID, "senha").send_keys("auditoria123")
    navegador.find_element(By.CLASS_NAME, "btn-primary").click()

    # Aguarda a página carregar
    time.sleep(5)

    # URLs dos relatórios e seus respectivos botões
    relatorios = [
        {
            "nome": "Contas Pagas",
            "url": f"https://agv.proobra.net.br/pro_obra/relatorio/mostrar_relatorio.php?relatorio=pagas&arquivo=contas/pagas.php&data_inicial={data_ini}&data_final={data_fim}&codempresa=1,8,2,6&tipo_compara=&atualizar=N&atualizar_passado=N&corrigir_indice=N&forma_pgto=N&ignorar_data=N&cta_parcial=N&detalhes=N&incluir_bloqueado=N&fiscal=N&atrasado=N&abertas=N&antecipada=N&mostrar_contrato=N&mostrar_obra=S&mostra_correcao=N&num_titulo=N&pendentes=N&item_conta=N",
            "xpath_botao": '//*[@id="imprimir"]/input[3]'
        },
        {
            "nome": "Contas a Pagar",
            "url": f"https://agv.proobra.net.br/pro_obra/relatorio/mostrar_relatorio.php?relatorio=pagar&arquivo=contas/pagar.php&data_inicial={data_ini}&data_final={data_fim}&codempresa=1,8,2,6&tipo_compara=&atualizar=N&atualizar_passado=N&corrigir_indice=N&forma_pgto=N&ignorar_data=N&cta_parcial=N&detalhes=N&incluir_bloqueado=N&fiscal=N&atrasado=N&abertas=N&antecipada=N&mostrar_contrato=N&mostrar_obra=S&mostra_correcao=N&num_titulo=N&pendentes=N&item_conta=N",
            "xpath_botao": '//*[@id="imprimir"]/input[3]'
        },
        {
            "nome": "Contas a Receber",
            "url": f"https://agv.proobra.net.br/pro_obra/relatorio/mostrar_relatorio.php?relatorio=receber&arquivo=contas/receber.php&pdf=&grupo=4&data_inicial={data_ini}&data_final={data_fim}&codempresa=&tipo_compara=&atualizar=N&atualizar_passado=N&corrigir_indice=N&forma_pgto=N&ignorar_data=N&cta_parcial=N&detalhes=N&incluir_bloqueado=N&fiscal=N&atrasado=N&abertas=N&antecipada=N&mostrar_contrato=N&mostrar_obra=S&mostra_correcao=N&num_titulo=N&pendentes=N&item_conta=N",
            "xpath_botao": '//*[@id="imprimir"]/input[3]'
        },
        {
            "nome": "Contas Recebidas",
            "url": f"https://agv.proobra.net.br/pro_obra/relatorio/mostrar_relatorio.php?relatorio=recebido&arquivo=contas/recebidas.php&pdf=&grupo=4&data_inicial={data_ini}&data_final={data_fim}&codempresa=1,8,2,6&tipo_compara=&agrupar=N&atualizar=N&atualizar_passado=N&forma_pgto=N&ignorar_data=N&cta_parcial=N&detalhes=N&incluir_bloqueado=N&fiscal=N&antecipada=N&mostrar_caixa=N&mostrar_contrato=N&mostrar_data_prevista=N&mostrar_obra=S&mostra_correcao=N&anexo=N&pendentes=N&item_conta=N",
            "xpath_botao": '//*[@id="imprimir"]/input[3]'
        }
    ]

    # Loop para acessar cada relatório e clicar no botão correspondente
    for relatorio in relatorios:
        print(f"Acessando relatório: {relatorio['nome']}")
        navegador.get(relatorio["url"])
        time.sleep(5)  # Aguarda o carregamento da página

        # Aguarda até que o botão seja clicável
        botao_exportar = WebDriverWait(navegador, 10).until(
            EC.element_to_be_clickable((By.XPATH, relatorio["xpath_botao"]))
        )

        # Clica no botão de exportação
        botao_exportar.click()
        print(f"Botão de exportação clicado para {relatorio['nome']}")

        # Aguarda o novo arquivo ser baixado
        time.sleep(10)  # Ajuste o tempo conforme necessário

    # Fecha o navegador
    navegador.quit()

acessar_relatorios("01/01/2010", "01/02/2060")

