# Processamento de imagem com OpenCV
## Configuração do ambiente de programação com Anaconda
### Pré-requisitos
 - [ ] Anaconda Navigator (https://docs.anaconda.com/free/anaconda/install/index.html)
 - [ ] Python 3 (Vem com o Anaconda)
 - [ ] Visual Studio Code (https://code.visualstudio.com)

### Instalando das libs necessárias
Executar o Anaconda Prompt e rodar os seguintes comandos:

    conda install -c conda-forge opencv
    conda install -c conda-forge pyside6

### Executando o projeto
Para executar o projeto, basta clonar ou baixar os arquivos desse repositório, e rodar por dentro do Anaconda Prompt:

    cd <diretorio_do_projeto>
    python main.py

## Como usar
A aplicação irá iniciar detectando a primeira webcam disponível como fonte de captura. Também é possível escolher um vídeo ou imagem a partir do botão "Carregar arquivo".

### Filtros
É possível aplicar diversos filtros, que são selecionados a partir de uma combo-box na interface. O filtro é aplicado ao clicar no botão "Aplicar filtro"

### Adesivos
Existem 2 tipos de adesivos que podem ser carregados no frame. O adesivo facial será aplicado por cima dos rostos identificados na imagem e pode ser carregado no botão "Carregar máscara". Os demais adesivos podem ser aplicados ao clicar com o botão esquerdo do mouse em qualquer região da imagem, isso fará com que seja aberta uma janela para a seleção do adesivo.

### Salvando o frame
O frame atual pode ser salvo em disco a partir do botão "Salvar imagem" na interface.