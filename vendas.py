import streamlit as st
import requests
import json
import base64
import re
import pandas as pd

# Configuração visual da página
st.set_page_config(
    page_title="Identificador de Modelos e SKU - OGNET",
    page_icon="🔍",
    layout="centered"
)

# --- CONFIGURAÇÕES ---
WEBHOOK_VENDAS_URL = "https://hook.us2.make.com/58kq63uwxgpnxc39sgyr2qk88o7o3wrw"
IMGBB_API_KEY = "c303da0c70a1655c79f00832f7b1456d"
NOME_PLANILHA = "base_gaxetas.xlsx"

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
    }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho Principal com Logo Local
try:
    st.image("LOGO_BANNER.jpg", width=550)
except Exception:
    pass  

st.title("🔍 Buscador de MARCA, MODELO, MEDIDAS e SKU - OGNET BORRACHAS")
st.markdown("Facilitador comercial para o time de vendas OGNET BORRACHAS. Busca automatizada direto da nossa base de modelos.")
st.divider()

st.subheader("📋 Critérios de Busca do Produto")

# Campo 1: Imagem da Etiqueta
st.markdown("### 📸 1. Foto da Etiqueta do Equipamento (Opcional)")
st.caption("Anexe a foto da etiqueta para a IA identificar o modelo comercial automaticamente.")
foto_upload = st.file_uploader("Selecione a foto da etiqueta:", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

if foto_upload is not None:
    st.image(foto_upload, caption="⚡ Etiqueta carregada para análise", width=400)
    st.divider()

# Campo 2: Digitação Direta do Modelo
st.markdown("### ✍️ 2. Digite o Modelo Comercial (Caso não tenha foto)")
st.caption("Digite o modelo ou parte dele para buscar na tabela.")
texto_vendedor = st.text_input(
    "Modelo para busca:",
    placeholder="Ex: BRM44, CRM33, DC44...",
    label_visibility="collapsed",
    key="busca_vendas"
)

st.divider()

# Campo 3: Digitação da Medida Externa
st.markdown("### 📐 3. Ou pesquise pela Medida Externa (Alternativa)")
st.caption("Digite as dimensões ou parte da medida externa que o cliente informou.")
medida_vendedor = st.text_input(
    "Medida para busca:",
    placeholder="Ex: 56X114, 68X160, 56...",
    label_visibility="collapsed",
    key="busca_medidas"
)

st.markdown("<br>", unsafe_allow_html=True)

# --- FUNÇÃO DE BUSCA NA PLANILHA DO GITHUB ---
def buscar_na_planilha(termo_modelo, termo_medida):
    try:
        df = pd.read_excel("base_gaxetas.xlsx")
        
        # Converte todas as colunas para string, limpa espaços e joga para maiúsculo
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            
        resultado = df.copy()
        
        # Só filtra por modelo se o termo_modelo não for vazio
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
                    
        # Só filtra por medida se o termo_medida não for vazio
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

# Botão de Execução
if st.button("🔍 Localizar SKU e Medidas na Tabela", type="primary", use_container_width=True):
    modelo_identificado = texto_vendedor.strip()
    medida_identificada = medida_vendedor.strip()
    prosseguir = True
    
    if not modelo_identificado and not medida_identificada and foto_upload is None:
        st.warning("Por favor, preencha pelo menos um critério (Foto, Modelo ou Medida) para realizar a busca.")
        prosseguir = False
        
    if prosseguir:
        # Se tiver foto e o usuário não digitou texto, o Make entra em ação
        if foto_upload is not None and not modelo_identificado:
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
                            retorno_bruto = response.text.strip()
                            
                            # --- SUPER BLINDAGEM DA RESPOSTA ---
                            # Tenta extrair qualquer palavra que pareça um modelo de geladeira (Ex: BRM47, DC44, CRM33)
                            # Se o Make trouxer JSON estruturado ou texto com aspas, o regex isola o modelo real
                            modelos_encontrados = re.findall(r'[A-Z]{2,4}\d{2,3}[A-Z]?', retorno_bruto.upper())
                            
                            if modelos_encontrados:
                                modelo_identificado = modelos_encontrados[0]
                            else:
                                # Se não achar pelo padrão técnico, limpa caracteres especiais e tenta ler o texto puro
                                retorno_bruto = re.sub(r'[\{\}\[\]"\'\n\r]', '', retorno_bruto)
                                retorno_bruto = retorno_bruto.replace('result:', '').replace('resposta_ia:', '').strip()
                                if retorno_bruto and len(retorno_bruto) < 15 and "ACCEPTED" not in retorno_bruto.upper():
                                    modelo_identificado = retorno_bruto
                                else:
                                    modelo_identificado = ""
                except Exception as e:
                    st.error(f"Erro na análise visual da etiqueta: {e}")

        # --- Campo de Verificação para o Agente ---
        if foto_upload is not None:
            if modelo_identificado and str(modelo_identificado).strip():
                st.info(f"🤖 **Modelo identificado pela foto:** `{modelo_identificado}`")
            else:
                st.error("❌ A IA não conseguiu extrair um modelo comercial válido. Tente digitar o modelo manualmente no Campo 2.")
                prosseguir = False

        # Executa a busca se tivermos algum critério válido após a análise
        if prosseguir and (modelo_identificado or medida_identificada):
            with st.spinner("🔍 Procurando dados correspondentes na tabela..."):
                tabela_resultados = buscar_na_planilha(modelo_identificado, medida_identificada)
                
                if tabela_resultados is not None and not tabela_resultados.empty:
                    st.success("Resultados localizados com sucesso!")
                    st.info(f"📋 Encontrado(s) {len(tabela_resultados)} produto(s) correspondente(s):")
                    
                    for index, row in tabela_resultados.iterrows():
                        st.markdown('<div class="vendas-card">', unsafe_allow_html=True)
                        st.markdown(f"### 📦 Produto Localizado:")
                        if 'SKU' in row:
                            st.markdown(f"<span class='sku-destaque'>🛒 SKU: {row['SKU']}</span>", unsafe_allow_html=True)
                        
                        st.markdown(f"**🔹 MARCA:** {row.get('MARCA', 'N/A')} | **MODELO:** {row.get('MODELO', 'N/A')}")
                        st.markdown(f"**🔹 PERFIL:** {row.get('PERFIL', 'N/A')} | **CÓDIGO INTERNO:** {row.get('CODIGO', 'N/A')}")
                        st.divider()
                        st.markdown(f"📐 **MEDIDA ENCAIXE:** {row.get('MEDIDA-ENCAIXE', 'N/A')}")
                        st.markdown(f"📐 **MEDIDA EXTERNA:** {row.get('MEDIDA-EXTERNA', 'N/A')}")
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
st.caption("© 2026 OGNET BORRACHAS - Divisão de Inteligência Comercial e Catálogo.")
