import streamlit as st
import requests
import json
import base64
import re
import pandas as pd

# Configuração visual da página
st.set_page_config(
    page_title="Buscador de Modelos e SKU - OGNET BORRACHAS",
    page_icon="🔍",
    layout="centered"
)

# --- CONFIGURAÇÕES BASELINKER ---
BASELINKER_API_URL = "https://api.baselinker.com/connector.php"
API_TOKEN = "8005379-8008488-VNRWQK4RZAPBTQ56SPHT6YDWXDJBJH83WPFY4C99A0E903RNR9SWPA9VO3BAYDZJ"
ID_TABELA_VENDA_DIRETA = "19191"
ID_TABELA_INSTALADOR = "39122"

NOME_PLANILHA = "base_gaxetas.xlsx"

# Customização visual com as cores oficiais OGNET
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
        padding: 22px;
        border-radius: 8px;
        margin-top: 15px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    }
    .sku-destaque {
        font-size: 20px;
        color: #E96A23;
        font-weight: bold;
        background-color: #fff;
        padding: 5px 10px;
        border-radius: 4px;
        border: 1px dashed #E96A23;
        display: inline-block;
        margin-bottom: 10px;
        margin-top: 10px;
    }
    .preco-card {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 6px;
        border: 1px solid #d1d5db;
        text-align: center;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

try:
    st.image("LOGO_BANNER.jpg", width=550)
except Exception:
    pass  

st.title("🔍 Buscador de MODELOS, MEDIDAS e SKU - OGNET BORRACHAS")
st.markdown("Agente de IA de Vendas da OGNET BORRACHAS. Busca automatizada direto da nossa base de modelos com preços e estoque integrados.")
st.divider()

st.subheader("📋 Critérios para Busca de Produtos")

st.markdown("### 📸 1. Foto da Etiqueta do Equipamento/Modelo Comercial")
st.caption("Anexe a foto da etiqueta para a IA identificar o modelo comercial automaticamente.")
foto_upload = st.file_uploader("Selecione a foto da etiqueta:", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if foto_upload is not None:
    st.image(foto_upload, caption="⚡ Etiqueta carregada para análise", width=400)
    st.divider()

st.markdown("### ✍️ 2. Digite o Modelo Comercial (referencia fica na etiqueta branca, atras ou dentro dos lados)")
st.caption("Digite o modelo ou parte dele para buscar na tabela.")
texto_vendedor = st.text_input(
    "Modelo para busca:",
    placeholder="Ex: BRM44, CRM33, DC44...",
    label_visibility="collapsed",
    key="busca_vendas"
)
st.divider()

st.markdown("### 📐 3. Pesquise pela Medida Externa (canto a canto)")
st.caption("Digite as dimensões ou parte da medida externa que o cliente informou.")
medida_vendedor = st.text_input(
    "Medida para busca:",
    placeholder="Ex: 56X114, 68X160, 56...",
    label_visibility="collapsed",
    key="busca_medidas"
)
st.markdown("<br>", unsafe_allow_html=True)

# --- FUNÇÃO DE BUSCA NA PLANILHA DO GITHUB ---
@st.cache_data(ttl=300)
def buscar_na_planilha(termo_modelo, termo_medida):
    try:
        df = pd.read_excel("base_gaxetas.xlsx")
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            
        resultado = df.copy()
        
        if termo_modelo and str(termo_modelo).strip():
            termo_mod = str(termo_modelo).strip().upper()
            if 'MODELO' in df.columns:
                resultado = resultado[resultado['MODELO'].str.contains(termo_mod, na=False)]
            else:
                coluna_modelo = [c for c in df.columns if 'MODELO' in c or 'PRODUTO' in c or 'CODIGO' in c]
                if coluna_modelo:
                    resultado = resultado[resultado[coluna_modelo[0]].str.contains(termo_mod, na=False)]
                else:
                    resultado = resultado[resultado[df.columns[0]].str.contains(termo_mod, na=False)]
                    
        if termo_medida and str(termo_medida).strip():
            termo_med = str(termo_medida).strip().upper()
            if 'MEDIDA-EXTERNA' in df.columns:
                resultado = resultado[resultado['MEDIDA-EXTERNA'].str.contains(termo_med, na=False)]
            else:
                coluna_medida = [c for c in df.columns if 'EXTERNA' in c]
                if coluna_medida:
                    resultado = resultado[resultado[coluna_medida[0]].str.contains(termo_med, na=False)]
                    
        return resultado
    except Exception as e:
        st.error(f"Erro ao ler o arquivo 'base_gaxetas.xlsx' no GitHub: {e}")
        return None

# --- FUNÇÃO PARA PUXAR PREÇO E ESTOQUE DO BASELINKER VIA SKU ---
@st.cache_data(ttl=600)
def buscar_dados_baselinker(sku):
    headers = {"X-BLToken": API_TOKEN}
    try:
        # 1. Pega Inventário
        resp_inv = requests.post(BASELINKER_API_URL, data={"method": "getInventories", "parameters": json.dumps({})}, headers=headers).json()
        id_inv = resp_inv.get("inventories", [])[0].get("inventory_id")
        
        # 2. Localiza ID do Produto pelo SKU
        payload_prod = {"method": "getInventoryProductsList", "parameters": json.dumps({"inventory_id": id_inv, "filter_sku": str(sku).strip()})}
        resp_prod = requests.post(BASELINKER_API_URL, data=payload_prod, headers=headers).json()
        produtos = resp_prod.get("products", {})
        if not produtos:
            return None, None, None
            
        product_id = list(produtos.keys())[0]
        
        # 3. Puxa os dados de preço e estoque
        payload_data = {"method": "getInventoryProductsData", "parameters": json.dumps({"inventory_id": id_inv, "products": [int(product_id)]})}
        resp_data = requests.post(BASELINKER_API_URL, data=payload_data, headers=headers).json()
        dados_prod = resp_data.get("products", {}).get(str(product_id))
        
        if dados_prod:
            precos = dados_prod.get("prices", {})
            preco_vd = precos.get(ID_TABELA_VENDA_DIRETA, 0.0)
            preco_inst = precos.get(ID_TABELA_INSTALADOR, 0.0)
            
            # Soma o estoque de todos os armazéns/locais vinculados ao produto
            estoque_dict = dados_prod.get("stock", {})
            qtd_estoque = sum(estoque_dict.values()) if estoque_dict else 0
            
            return preco_vd, preco_inst, qtd_estoque
    except:
        pass
    return None, None, None

# Botão de Execução
if st.button("🔍 Localizar SKU e Medidas na Tabela", type="primary", use_container_width=True):
    modelo_identificado = texto_vendedor.strip()
    medida_identificada = medida_vendedor.strip()
    prosseguir = True
    
    if not modelo_identificado and not medida_identificada and foto_upload is None:
        st.warning("Por favor, preencha pelo menos um critério (Foto, Modelo ou Medida) para realizar a busca.")
        prosseguir = False
        
    if prosseguir:
        if foto_upload is not None and not modelo_identificado:
            with st.spinner("🤖 O Especialista em vendas Otávio Guilherme está escaneando o texto da etiqueta..."):
                try:
                    file_bytes = foto_upload.read()
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    
                    url_ocr = "https://api.ocr.space/parse/image"
                    payload_ocr = {
                        "apikey": "helloworld", 
                        "base64Image": f"data:image/jpeg;base64,{base64_image}",
                        "language": "por",
                        "isOverlayRequired": False
                    }
                    
                    response_ocr = requests.post(url_ocr, data=payload_ocr, timeout=25)
                    
                    if response_ocr.status_code == 200:
                        res_json = response_ocr.json()
                        if "ParsedResults" in res_json and len(res_json["ParsedResults"]) > 0:
                            texto_extraido = res_json["ParsedResults"][0]["ParsedText"].upper()
                            
                            modelos_encontrados = re.findall(r'[A-Z]{2,4}\d{2,3}[A-Z]?', texto_extraido)
                            if modelos_encontrados:
                                modelo_identificado = modelos_encontrados[0]
                            else:
                                padrão_curto = re.findall(r'\b\d{2,3}\b', texto_extraido)
                                if padrão_curto:
                                    modelo_identificado = padrão_curto[0]
                except Exception as e:
                    st.error(f"Erro na varredura visual direta: {e}")

        if foto_upload is not None:
            if modelo_identificado and str(modelo_identificado).strip():
                st.info(f"🤖 **Modelo identificado pela foto:** `{modelo_identificado}`")
            else:
                st.error("❌ O scanner não conseguiu capturar as letras do modelo nesta foto.")
                st.warning("Por favor, digite o modelo manualmente no Campo 2 para trazer as medidas.")
                prosseguir = False

        if prosseguir and (modelo_identificado or medida_identificada):
            with st.spinner("🔍 Procurando dados e preços na base..."):
                tabela_resultados = buscar_na_planilha(modelo_identificado, medida_identificada)
                
                if tabela_resultados is not None and not tabela_resultados.empty:
                    st.success("Resultados localizados com sucesso!")
                    st.info(f"📋 Encontrado(s) {len(tabela_resultados)} produto(s) correspondente(s):")
                    
                    for index, row in tabela_resultados.iterrows():
                        st.markdown('<div class="vendas-card">', unsafe_allow_html=True)
                        st.markdown(f"### 📦 Produto Localizado:")
                        
                        st.markdown(f"**🔹 MARCA:** {row.get('MARCA', 'N/A')} | **MODELO:** {row.get('MODELO', 'N/A')}")
                        st.markdown(f"**🔹 PERFIL:** {row.get('PERFIL', 'N/A')} | **CÓDIGO INTERNO:** {row.get('CODIGO', 'N/A')}")
                        st.divider()
                        st.markdown(f"📐 **MEDIDA ENCAIXE:** {row.get('MEDIDA-ENCAIXE', 'N/A')}")
                        st.markdown(f"📐 **MEDIDA EXTERNA:** {row.get('MEDIDA-EXTERNA', 'N/A')}")
                        st.divider()
                        
                        # --- INJEÇÃO INTELIGENTE DE PREÇOS COM MULTI-SKU ---
                        if 'SKU' in row and str(row['SKU']).strip() != 'NAN':
                            # Divide o campo SKU usando a barra "/"
                            skus_brutos = str(row['SKU']).split('/')
                            
                            for sku_extraido in skus_brutos:
                                sku_limpo = sku_extraido.strip()
                                if not sku_limpo:
                                    continue
                                
                                # Cria o cabeçalho para o SKU atual
                                st.markdown(f"<div class='sku-destaque'>🛒 SKU: {sku_limpo}</div>", unsafe_allow_html=True)
                                
                                preco_vd, preco_inst, qtd_estoque = buscar_dados_baselinker(sku_limpo)
                                
                                if preco_vd is not None and preco_inst is not None:
                                    c1, c2, c3 = st.columns(3)
                                    with c1:
                                        st.markdown(f"<div class='preco-card'><small>Venda Direta</small><br><b>R$ {float(preco_vd):,.2f}</b></div>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                                    with c2:
                                        st.markdown(f"<div class='preco-card'><small>Instalador</small><br><b>R$ {float(preco_inst):,.2f}</b></div>".replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
                                    with c3:
                                        st.markdown(f"<div class='preco-card'><small>Estoque</small><br><b>{qtd_estoque} un</b></div>", unsafe_allow_html=True)
                                else:
                                    st.caption(f"⚠️ Preços/Estoque não localizados no sistema para o SKU {sku_limpo}.")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error(f"❌ Nenhum produto localizado")
                    if modelo_identificado and medida_identificada:
                        st.warning(f"Não encontramos combinações para o modelo **'{modelo_identificado}'** com a medida **'{medida_identificada}'**.")
                    elif modelo_identificado:
                        st.warning(f"O modelo **'{modelo_identificado}'** não foi encontrado na coluna MODELO da planilha.")
                    elif medida_identificada:
                        st.warning(f"A medida **'{medida_identificada}'** não foi encontrada na coluna MEDIDA-EXTERNA.")

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("© 2026 OGNET BORRACHAS - Buscador Inteligência Artificial.")
