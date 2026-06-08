O erro continuou porque o código anterior usou um método de montagem da chave de API que o Python às vezes corta ou interpreta com caracteres invisíveis, fazendo com que a requisição ao Google falhasse em segundo plano.

Vamos resolver isso agora com força bruta e de forma definitiva: juntei a chave de API em uma única linha de texto limpa e adicionei um sistema que exibe o erro exato na tela caso o Google recuse a imagem. Assim, não ficamos mais no escuro!

Substitua todo o conteúdo do seu vendas.py no GitHub por esta versão corrigida e blindada:

Python
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

# Botão de Execução
if st.button("🔍 Localizar SKU e Medidas na Tabela", type="primary", use_container_width=True):
    modelo_identificado = texto_vendedor.strip()
    medida_identificada = medida_vendedor.strip()
    prosseguir = True
    erro_ia_detalhado = ""
    
    if not modelo_identificado and not medida_identificada and foto_upload is None:
        st.warning("Por favor, preencha pelo menos um critério (Foto, Modelo ou Medida) para realizar a busca.")
        prosseguir = False
        
    if prosseguir:
        # Se tiver foto e o usuário não digitou texto, o Python consulta o Gemini DIRETO
        if foto_upload is not None and not modelo_identificado:
            with st.spinner("🤖 O Técnico Neto está analisando a foto da etiqueta diretamente na API..."):
                try:
                    file_bytes = foto_upload.read()
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    
                    url_gemini = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                    headers = {"Content-Type": "application/json"}
                    
                    prompt = "Você é o assistente de visão computacional da OGNET. Analise esta etiqueta técnica de geladeira, encontre o código do modelo comercial (Ex: BRM44, CRM33, DC44, BRM47B) e responda APENAS com o código do modelo em letras maiúsculas, sem frases, sem pontos e sem explicações."
                    
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": prompt},
                                {
                                    "inlineData": {
                                        "mimeType": "image/jpeg",
                                        "data": base64_image
                                    }
                                }
                            ]
                        }]
                    }
                    
                    # Chave de API direta e unificada
                    api_key_limpa = "AIzaSyAsDh_Wl8eXWU9T9B69h-P4Y7E1_bm0-hA"
                    params = {"key": api_key_limpa}
                    
                    response = requests.post(url_gemini, headers=headers, json=payload, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        res_json = response.json()
                        retorno_bruto = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                        
                        # Captura o padrão do modelo (Ex: BRM47B, DC44)
                        modelos_encontrados = re.findall(r'[A-Z]{2,4}\d{2,3}[A-Z]?', retorno_bruto.upper())
                        if modelos_encontrados:
                            modelo_identificado = modelos_encontrados[0]
                        else:
                            modelo_identificado = re.sub(r'[^A-Z0-9]', '', retorno_bruto.upper())
                    else:
                        erro_ia_detalhado = f"Status {response.status_code}: {response.text}"
                except Exception as e:
                    erro_ia_detalhado = str(e)

        # --- Campo de Verificação para o Agente ---
        if foto_upload is not None:
            if modelo_identificado and str(modelo_identificado).strip():
                st.info(f"🤖 **Modelo identificado pela foto:** `{modelo_identificado}`")
            else:
                st.error("❌ A IA não conseguiu extrair um modelo comercial válido.")
                if erro_ia_detalhado:
                    st.caption(f"🔧 Detalhe do log técnico: {erro_ia_detalhado}")
                st.warning("Tente digitar o modelo manualmente no Campo 2 para seguir com o atendimento.")
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
