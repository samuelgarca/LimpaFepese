import streamlit as st
import fitz  # PyMuPDF
import io

# Configuração da página
st.set_page_config(
    page_title="GabaritaAI - Limpador de Provas",
    page_icon="📝",
    layout="centered"
)

st.title("📝 GabaritaAI - Limpador Universal")
st.markdown("""
Esta ferramenta remove as respostas marcadas do gabarito e padroniza as alternativas.
- **Símbolos (☑, ☒)** viram quadrados vazios.
- **Texto (( X ), (  ))** vira parênteses vazios padronizados.
""")

def desenhar_quadrado(page, rect_original, tamanho=9.0):
    """Para questões com caixinha (Estilo Simbolo)"""
    # 1. Apaga
    page.add_redact_annot(rect_original, fill=(1, 1, 1))
    page.apply_redactions()
    
    # 2. Calcula Centro
    centro_x = (rect_original.x0 + rect_original.x1) / 2
    centro_y = (rect_original.y0 + rect_original.y1) / 2
    
    # 3. Novo Quadrado
    novo_x0 = centro_x - (tamanho / 2)
    novo_y0 = centro_y - (tamanho / 2)
    novo_x1 = centro_x + (tamanho / 2)
    novo_y1 = centro_y + (tamanho / 2)
    
    # 4. Desenha
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(novo_x0, novo_y0, novo_x1, novo_y1))
    shape.finish(color=(0, 0, 0), width=0.6)
    shape.commit()

def escrever_parenteses(page, rect_original):
    """Para questões com texto (Estilo ( X ))"""
    # 1. Apagar o original
    # Adicionamos um pequeno padding (+1) para garantir que apague bordas sujas
    rect_apagar = fitz.Rect(rect_original.x0 - 1, rect_original.y0 - 1, rect_original.x1 + 1, rect_original.y1 + 1)
    page.add_redact_annot(rect_apagar, fill=(1, 1, 1))
    page.apply_redactions()
    
    # 2. Configurações da Fonte
    altura_box = rect_original.y1 - rect_original.y0
    tamanho_fonte = altura_box * 0.85 # 85% do tamanho original
    
    # 3. Calcular Posição (Baseline)
    x_pos = rect_original.x0
    y_pos = rect_original.y1 - (altura_box * 0.15)
    
    # 4. INSERÇÃO FORÇADA
    page.insert_text(
        fitz.Point(x_pos, y_pos),
        "(  )",               # Texto novo padronizado
        fontname="tiro",      # Times Roman
        fontsize=tamanho_fonte,
        color=(0, 0, 0)
    )

def limpar_pdf_web(input_stream):
    # Abre o PDF a partir da memória
    doc = fitz.open(stream=input_stream, filetype="pdf")
    
    # --- CONFIGURAÇÕES ---
    TAMANHO_QUADRADO = 9.0
    
    # PADRÃO 1: SÍMBOLOS
    fontes_symbol = ["FontAwesome", "Dingbats", "Wingdings", "ZapfDingbats"] 
    codigos_symbol = [67, 83, 120, 88, 10003, 10007, 61565]

    # PADRÃO 2: TEXTO
    # Lista completa para pegar marcadas E vazias
    padroes_texto = ["( X )", "(X)", "( x )", "(x)", "( )", "()", "(  )"]

    total_removidos = 0
    total_paginas = len(doc)
    barra_progresso = st.progress(0)
    
    for i, page in enumerate(doc):
        # Atualiza barra de progresso
        barra_progresso.progress((i + 1) / total_paginas)
        
        count_pagina = 0
        
        # FASE 1: SÍMBOLOS -> Vira Quadrado
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

        # FASE 2: TEXTO -> Vira Parênteses
        for padrao in padroes_texto:
            ocorrencias = page.search_for(padrao)
            for rect in ocorrencias:
                escrever_parenteses(page, rect)
                count_pagina += 1
        
        total_removidos += count_pagina

    # Salva o resultado na memória
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer, total_removidos

# --- INTERFACE ---
uploaded_file = st.file_uploader("Escolha o arquivo PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Limpar Gabarito"):
        with st.spinner('Processando o arquivo...'):
            try:
                input_bytes = uploaded_file.read()
                pdf_limpo, qtd = limpar_pdf_web(input_bytes)
                
                st.success(f"Concluído! {qtd} alternativas foram padronizadas.")
                
                st.download_button(
                    label="📥 Baixar PDF Limpo",
                    data=pdf_limpo,
                    file_name="prova_limpa.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

st.markdown("---")
st.caption("Desenvolvido para o projeto GabaritaAI")
