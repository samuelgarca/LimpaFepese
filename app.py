import streamlit as st
import fitz  # PyMuPDF
import io
import time
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="GabaritaAI // System",
    page_icon="💾",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS (Visual Geek Corrigido) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');

    /* Fundo e Fonte Base */
    .stApp {
        background-color: #0e1117;
        font-family: 'Fira Code', monospace;
        color: #e0e0e0;
    }
    
    /* Força fonte apenas em textos principais para não quebrar ícones */
    h1, h2, h3, p, label, .stButton, .stTextInput {
        font-family: 'Fira Code', monospace !important;
    }

    /* Título Neon */
    .title-glitch {
        font-size: 40px;
        font-weight: bold;
        color: #00ff41;
        text-shadow: 0 0 10px #00ff41;
        margin-bottom: 20px;
    }

    /* Upload Area */
    .stFileUploader {
        border: 1px dashed #00ff41;
        padding: 10px;
        border-radius: 5px;
    }

    /* Botões */
    .stButton>button {
        width: 100%;
        background-color: transparent;
        color: #00ff41;
        border: 1px solid #00ff41;
        border-radius: 0px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #00ff41;
        color: #000000;
        box-shadow: 0 0 15px #00ff41;
        border-color: #00ff41;
    }

    /* Barra de Progresso */
    .stProgress > div > div > div > div {
        background-color: #00ff41;
    }
    
    /* Mensagens */
    .stSuccess {
        background-color: rgba(0, 255, 65, 0.1);
        border-left: 5px solid #00ff41;
        color: #00ff41;
    }
    
    .stWarning {
        background-color: rgba(255, 215, 0, 0.1);
        border-left: 5px solid #FFD700;
        color: #FFD700;
    }
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 🖥️ SYSTEM STATUS")
    st.markdown("---")
    st.markdown("**CORE:** `ONLINE`")
    st.markdown("**MODULE:** `PYMUPDF`")
    st.markdown("**VERSION:** `v1.0.6-stable`")
    st.markdown("---")
    st.info("💡 **DICA:** O algoritmo reescreve todas as alternativas para garantir anonimato total da resposta correta.")
    st.markdown("---")
    st.caption("Desenvolvido por **GabaritaAI**")

# --- CABEÇALHO ---
st.markdown('<div class="title-glitch">> GabaritaAI_ </div>', unsafe_allow_html=True)
st.markdown("`Inicializando protocolo de limpeza de provas...`")
st.markdown("---")

# --- LÓGICA DE LIMPEZA ---
def desenhar_quadrado(page, rect_original, tamanho=9.0):
    page.add_redact_annot(rect_original, fill=(1, 1, 1))
    page.apply_redactions()
    centro_x = (rect_original.x0 + rect_original.x1) / 2
    centro_y = (rect_original.y0 + rect_original.y1) / 2
    novo_rect = fitz.Rect(centro_x - tamanho/2, centro_y - tamanho/2, centro_x + tamanho/2, centro_y + tamanho/2)
    shape = page.new_shape()
    shape.draw_rect(novo_rect)
    shape.finish(color=(0, 0, 0), width=0.6)
    shape.commit()

def desenhar_novo_parenteses(page, rect_original):
    rect_apagar = fitz.Rect(rect_original.x0 - 1, rect_original.y0 - 1, rect_original.x1 + 1, rect_original.y1 + 1)
    page.add_redact_annot(rect_apagar, fill=(1, 1, 1))
    page.apply_redactions()
    
    altura_box = rect_original.y1 - rect_original.y0
    tamanho_fonte = altura_box * 0.90
    x_pos = rect_original.x0
    y_pos = rect_original.y1 - (altura_box * 0.15)
    
    page.insert_text(fitz.Point(x_pos, y_pos), "(  )", fontname="tiro", fontsize=tamanho_fonte, color=(0, 0, 0))

def processar_pdf(input_stream, status_terminal):
    doc = fitz.open(stream=input_stream, filetype="pdf")
    TAMANHO_QUADRADO = 9.0
    fontes_symbol = ["FontAwesome", "Dingbats", "Wingdings", "ZapfDingbats"] 
    codigos_symbol = [67, 83, 120, 88, 10003, 10007, 61565] 
    padroes_texto = ["( X )", "(X)", "( x )", "(x)", "( )", "()", "(  )"]

    total_alterados = 0
    total_paginas = len(doc)
    barra = st.progress(0)
    
    for i, page in enumerate(doc):
        status_terminal.code(f"> SCANNING PAGE {i+1}/{total_paginas} ... [OK]")
        barra.progress((i + 1) / total_paginas)
        
        count_pagina = 0
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        if any(f_name in s["font"] for f_name in fontes_symbol):
                            for char in s["text"]:
                                if ord(char) in codigos_symbol:
                                    desenhar_quadrado(page, fitz.Rect(s["bbox"]), TAMANHO_QUADRADO)
                                    count_pagina += 1

        for padrao in padroes_texto:
            ocorrencias = page.search_for(padrao)
            for rect in ocorrencias:
                desenhar_novo_parenteses(page, rect)
                count_pagina += 1
        
        total_alterados += count_pagina

    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, total_alterados

# --- INTERFACE PRINCIPAL ---
uploaded_file = st.file_uploader("📂 CARREGAR ARQUIVO ALVO (.PDF)", type="pdf")

if uploaded_file is not None:
    st.markdown("Arquivo detectado: `" + uploaded_file.name + "`")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 EXECUTAR LIMPEZA DE DADOS"):
        terminal = st.empty()
        
        try:
            terminal.code("> INITIATING SYSTEM...")
            time.sleep(0.5)
            terminal.code("> LOADING MODULES...")
            time.sleep(0.5)
            
            pdf_limpo, qtd = processar_pdf(uploaded_file.read(), terminal)
            
            terminal.empty()
            
            if qtd > 0:
                st.success(f"✔️ SUCESSO! {qtd} ALTERNATIVAS PADRONIZADAS.")
                # st.balloons() <- REMOVIDO PARA VISUAL MAIS SÉRIO
                
                # Nome do arquivo ajustado
                nome_original = os.path.splitext(uploaded_file.name)[0]
                nome_novo = f"{nome_original}_limpa.pdf"
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="📥 DOWNLOAD ARQUIVO LIMPO",
                        data=pdf_limpo,
                        file_name=nome_novo,
                        mime="application/pdf"
                    )
            else:
                st.warning("⚠️ NENHUM PADRÃO CONHECIDO DETECTADO. O ARQUIVO PODE SER UMA IMAGEM.")
                
        except Exception as e:
            st.error(f"❌ ERRO CRÍTICO NO SISTEMA: {e}")

else:
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 12px; margin-top: 50px;'>
        WAITING FOR INPUT STREAM...
    </div>
    """, unsafe_allow_html=True)
