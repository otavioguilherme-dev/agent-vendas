import streamlit as st
import requests
import json
import base64
import re
import pandas as pd  # Biblioteca para ler a planilha do GitHub

# Configuração visual da página
st.set_page_config(
    page_title="Identificador de Modelos e SKU - OGNET",
    page_icon="🔍",
    layout="centered"
)

# --- CONFIGURAÇÕES ---
# Este Webhook só será usado se houver FOTO para o Gemini extrair o texto do modelo
WEBHOOK_VENDAS_URL = "https://hook.us2.make.com/SUA_NOVA_URL_DE_VENDAS"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"
NOME_PLANILHA = "base_gaxetas.xlsx"  # Nome exato do seu arquivo Excel no GitHub

# Customização visual com as cores oficiais OGNET (Azul: #1B2E7C | Laranja: #E96A23)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    div.stButton > button:first-child {
        background-color: #1B2E7C !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #E96A23 !important;
        box-shadow: 0px 4px 10px rgba(233, 106, 35, 0.3) !important;
    }
    
    h1, h2, h3 { color: #1B2E7C !important; }
    
    .vendas-card {
        background-color: #f1f3f9;
        border-left: 6px solid #1B2E7C;
        padding: 25px;
        border-radius: 8px;
        margin-top: 20px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho Principal com Logo Local
try:
    st.image("LOGO_BANNER.jpg", width=350)
except Exception:
    pass  

st.title("🔍 Localizador de Catálogo e SKU - Técnico Neto")
st.markdown("Facilitador comercial para o time de vendas OGNET. Busca automatizada direto no banco de dados local.")
st.divider()

st.subheader("📋 Dados de Busca do Produto")

# Passo 1: Imagem da Etiqueta
st.markdown("### 📸 1. Foto da Etiqueta do Equipamento (Opcional)")
st.caption("Anexe a foto da etiqueta para a IA identificar o modelo comercial automaticamente.")
foto_upload = st.file_uploader("Selecione a foto da etiqueta:", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if foto_upload is not None:
    st.image(foto_upload, caption="⚡ Etiqueta carregada para análise", width=400)
    st.divider()

# Passo 2: Digitação Direta
st.markdown("### ✍️ 2. Digitar Modelo Comercial (Caso não tenha foto)")
st.caption("Digite o modelo ou parte dele para buscar direto na tabela.")
texto_vendedor = st.text_input(
    "Modelo para busca:",
    placeholder="Ex: BRM44, CRM33, REFRIGERADOR...",
    label_visibility="collapsed",
    key="busca_vendas"
)

st.markdown("<br>", unsafe_allow_html=True)

# --- FUNÇÃO DE BUSCA NA PLANILHA DO GITHUB ---
def buscar_na_planilha(termo_busca):
    try:
        # Carrega o arquivo Excel carregado na raiz do GitHub
        df = pd.read_excel(NOME_PLANILHA)
        
        termo = str(termo_busca).strip().upper()
        if not termo:
            return None
        
        # Converte todas as colunas para string e maiúsculo para busca precisa
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            
        # Busca inteligente: tenta achar colunas com nomes comuns de identificação
        coluna_modelo = [c for c in df.columns if 'MODELO' in c or 'PRODUTO' in c or 'CODIGO' in c]
        
        if coluna_modelo:
            # Filtra linhas onde a coluna de modelo contém o termo buscado
            resultado = df[df[coluna_modelo[0]].str.contains(termo, na=False)]
        else:
            # Caso não ache uma coluna específica, varre a primeira coluna da planilha
            resultado = df[df[df.columns[0]].str.contains(termo, na=False)]
            
        return resultado
    except Exception as e:
        st.error(f"Erro ao ler o arquivo '{NOME_PLANILHA}' no GitHub: {e}")
        return None

# Botão de Execução
if st.button("🔍 Localizar SKU e Medidas na Tabela", type="primary", use_container_width=True):
    modelo_identificado = texto_vendedor.strip()
    prosseguir = True
    
    if not modelo_identificado and foto_upload is None:
        st.warning("Por favor, digite o modelo ou anexe a foto da etiqueta para realizar a busca.")
        prosseguir = False
        
    if prosseguir:
        # Se tiver foto, o Make entra em ação só para o Gemini ler o texto da etiqueta
        if foto_upload is not None:
            with st.spinner("🤖 O Técnico Neto está analisando a foto da etiqueta..."):
                try:
                    file_bytes = foto_upload.read()
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    
                    imgbb_url = "https://api.imgbb.com/1/upload"
                    payload_imgbb = {"key": IMGBB_API_KEY, "image": base64_image, "expiration": 600}
                    res_imgbb = requests.post(imgbb_url, data=payload_imgbb)
                    res_data = res_imgbb.json()
                    
                    if res_imgbb.status_code == 200 and res_data.get("success"):
                        link_foto = res_data["data"]["url"]
                        
                        payload = {"foto": link_foto, "texto": "EXTRAIR_MODELO"}
                        response = requests.post(WEBHOOK_VENDAS_URL, data=payload, timeout=30)
                        
                        if response.status_code == 200:
                            modelo_identificado = response.text.replace('{"result":"', '').replace('"}', '').strip()
                except Exception as e:
                    st.error(f"Erro na análise visual da etiqueta: {e}")

        # Executa a busca local instantânea dentro do Excel
        if modelo_identificado:
            with st.spinner(f"🔍 Procurando dados para o modelo '{modelo_identificado}' na tabela..."):
                tabela_resultados = buscar_na_planilha(modelo_identificado)
                
                if tabela_resultados is not None and not tabela_resultados.empty:
                    st.success(f"Modelo '{modelo_identificado}' Localizado com Sucesso!")
                    
                    for index, row in tabela_resultados.iterrows():
                        st.markdown('<div class="vendas-card">', unsafe_allow_html=True)
                        st.markdown(f"### 📦 Produto Localizado:")
                        
                        # Lista dinamicamente todas as colunas que você preencheu no Excel
                        for coluna in tabela_resultados.columns:
                            st.markdown(f"**🔹 {coluna}:** {row[coluna]}")
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ Nenhuma especificação técnica foi encontrada para o modelo '{modelo_identificado}' no arquivo base_gaxetas.xlsx.")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("© 2026 OGNET BORRACHAS - Divisão de Inteligência Comercial e Catálogo.")
