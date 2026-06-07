import streamlit as st
import requests
import json
import base64
import re

# Configuração visual da página (Focada em ferramentas internas de Vendas)
st.set_page_config(
    page_title="Identificador de Modelos e SKU - OGNET",
    page_icon="🔍",
    layout="centered"
)

# --- CONFIGURAÇÕES DO WEBHOOK DE VENDAS ---
# RECOMENDAÇÃO: Crie um novo cenário no Make e cole a URL nova aqui abaixo
WEBHOOK_VENDAS_URL = "https://hook.us2.make.com/SUA_NOVA_URL_AQUI"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"

# Customização visual com as cores oficiais OGNET (Azul: #1B2E7C | Laranja: #E96A23)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    
    div.stButton > button:first-child {
        background-color: #1B2E7C !important; /* Botão principal azul para diferenciar do suporte */
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
st.markdown("Facilitador comercial para o time de vendas OGNET. Descubra medidas e códigos de venda em segundos.")
st.divider()

st.subheader("📋 Dados de Busca do Produto")

# Passo 1: Imagem da Etiqueta
st.markdown("### 📸 1. Foto da Etiqueta do Equipamento (Recomendado)")
st.caption("Tire ou anexe uma foto nítida da etiqueta técnica da geladeira (onde aparece o modelo comercial).")
foto_upload = st.file_uploader("Selecione a foto da etiqueta:", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if foto_upload is not None:
    st.image(foto_upload, caption="⚡ Etiqueta carregada para análise visual", width=400)
    st.divider()

# Passo 2: Digitação Direta
st.markdown("### ✍️ 2. Digitar Modelo Comercial (Alternativa)")
st.caption("Se não tiver foto, digite o modelo, marca ou código que o cliente informou.")
texto_vendedor = st.text_area(
    "Dados informados:",
    placeholder="Ex: Cliente informou que é uma Brastemp BRM44 ou mandou o texto REFRIGERADOR CRM33...",
    height=100,
    label_visibility="collapsed",
    key="busca_vendas"
)

st.markdown("<br>", unsafe_allow_html=True)

# Botão de Execução
if st.button("🔍 Localizar SKU e Medidas na Tabela", type="primary", use_container_width=True):
    link_imagem_final = "sem_foto"
    prosseguir = True
    
    if not texto_vendedor.strip() and foto_upload is None:
        st.warning("Por favor, digite o modelo ou anexe a foto da etiqueta para realizar a busca.")
        prosseguir = False
        
    if prosseguir:
        if foto_upload is not None:
            with st.spinner("🤖 Analisando imagem da etiqueta..."):
                try:
                    file_bytes = foto_upload.read()
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    
                    imgbb_url = "https://api.imgbb.com/1/upload"
                    payload_imgbb = {
                        "key": IMGBB_API_KEY,
                        "image": base64_image,
                        "expiration": 600 
                    }
                    
                    res_imgbb = requests.post(imgbb_url, data=payload_imgbb)
                    res_data = res_imgbb.json()
                    
                    if res_imgbb.status_code == 200 and res_data.get("success"):
                        link_imagem_final = res_data["data"]["url"]
                except Exception as e:
                    st.error(f"Erro no processamento da imagem: {e}")

        # Payload limpo para o novo cenário do Make
        payload = {
            "foto": link_imagem_final,
            "texto": texto_vendedor.strip()
        }
        
        # Reaproveitando nossa função de limpeza de JSON blindada
        def limpar_resposta_ia(texto_bruto):
            if not isinstance(texto_bruto, str):
                return ""
            texto = texto_bruto.strip()
            try:
                if texto.startswith('{'):
                    dados_json = json.loads(texto)
                    if "result" in dados_json: return dados_json["result"].strip()
            except Exception:
                pass
            texto = re.sub(r'^\{\s*\\*"(resposta_ia|result)\\*"\s*:\s*\\*["\']', '', texto)
            texto = re.sub(r'^\{\s*"(resposta_ia|result)"\s*:\s*["\']', '', texto)
            texto = texto.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '    ')
            return texto.strip()

        with st.spinner("🤖 O Técnico Neto está consultando o catálogo e a planilha... Aguarde."):
            try:
                response = requests.post(WEBHOOK_VENDAS_URL, data=payload, timeout=45)
                
                if response.status_code == 200:
                    resposta_final = limpar_resposta_ia(response.text)
                    
                    if not resposta_final.strip():
                        st.warning("⚠️ Busca processada, mas o catálogo não retornou dados para este modelo.")
                    else:
                        st.success("Busca de Catálogo Concluída!")
                        
                        st.markdown('<div class="vendas-card">', unsafe_allow_html=True)
                        st.subheader("📦 Dados Localizados para Venda:")
                        st.markdown(resposta_final)
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error(f"Erro ao consultar planilha. (Código: {response.status_code})")
            except requests.exceptions.RequestException:
                st.error("Falha de comunicação com o servidor de banco de dados.")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("© 2026 OGNET BORRACHAS - Divisão de Inteligência Comercial e Catálogo.")
