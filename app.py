import streamlit as st
import fitz  # PyMuPDF
import io

# Configuração da página
st.set_page_config(page_title="Limpador de Gabarito FEPESE", page_icon="📝")

st.title("📝 Removedor de Gabarito - FEPESE")
st.write("Faça upload da sua prova em PDF e baixe a versão limpa para treinar.")

# Função de limpeza (A mesma lógica que criamos, adaptada para memória)
def limpar_pdf(input_stream):
    # Abre o PDF a partir da memória (bytes)
    doc = fitz.open(stream=input_stream, filetype="pdf")
    
    fontes_alvo = ["FontAwesome", "Dingbats", "Wingdings"] 
    codigos_alvo = [67, 83] # 67=Marcada, 83=Vazia
    TAMANHO = 9.0
    count = 0
    
    progress_bar = st.progress(0)
    total_pages = len(doc)

    for i, page in enumerate(doc):
        # Atualiza barra de progresso
        progress_bar.progress((i + 1) / total_pages)

        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        if any(f in s["font"] for f in fontes_alvo):
                            for char in s["text"]:
                                if ord(char) in codigos_alvo:
                                    rect_original = fitz.Rect(s["bbox"])
                                    
                                    # 1. Apagar
                                    page.add_redact_annot(rect_original, fill=(1, 1, 1))
                                    page.apply_redactions()
                                    
                                    # 2. Desenhar
                                    centro_x = (rect_original.x0 + rect_original.x1) / 2
                                    centro_y = (rect_original.y0 + rect_original.y1) / 2
                                    
                                    novo_x0 = centro_x - (TAMANHO / 2)
                                    novo_y0 = centro_y - (TAMANHO / 2)
                                    novo_x1 = centro_x + (TAMANHO / 2)
                                    novo_y1 = centro_y + (TAMANHO / 2)
                                    
                                    novo_rect = fitz.Rect(novo_x0, novo_y0, novo_x1, novo_y1)
                                    
                                    shape = page.new_shape()
                                    shape.draw_rect(novo_rect)
                                    shape.finish(color=(0, 0, 0), width=0.6)
                                    shape.commit()
                                    count += 1
    
    # Salva o resultado em um buffer de memória (não no disco)
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer, count

# --- INTERFACE DO USUÁRIO ---

uploaded_file = st.file_uploader("Escolha o arquivo PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Limpar Gabarito"):
        with st.spinner('Processando... Isso pode levar alguns segundos.'):
            try:
                # Lê o arquivo enviado como bytes
                input_bytes = uploaded_file.read()
                
                # Processa
                pdf_limpo, qtd_removida = limpar_pdf(input_bytes)
                
                st.success(f"Sucesso! {qtd_removida} questões foram padronizadas.")
                
                # Botão de Download
                st.download_button(
                    label="📥 Baixar PDF Limpo",
                    data=pdf_limpo,
                    file_name="prova_limpa.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")
