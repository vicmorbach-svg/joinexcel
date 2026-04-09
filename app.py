import streamlit as st
import pandas as pd
import io

# Configuração da página
st.set_page_config(page_title="Mesclar Arquivos", page_icon="📊")

st.title("📊 Juntar Arquivos Excel e CSV")
st.write("Faça o upload de vários arquivos (Excel ou CSV) para combiná-los em um único arquivo. Os dados serão empilhados verticalmente.")

# Upload de múltiplos arquivos (agora aceitando CSV)
uploaded_files = st.file_uploader(
    "Arraste e solte ou escolha os arquivos", 
    type=["xlsx", "xls", "csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    dataframes = []

    # Barra de progresso visual
    progress_text = "Lendo arquivos..."
    my_bar = st.progress(0, text=progress_text)

    for i, file in enumerate(uploaded_files):
        try:
            # Verifica se é CSV ou Excel
            if file.name.endswith('.csv'):
                try:
                    # Tenta ler com padrão internacional (vírgula e utf-8)
                    df = pd.read_csv(file)
                except Exception:
                    # Se falhar, tenta o padrão comum no Brasil (ponto e vírgula e latin1)
                    file.seek(0)
                    df = pd.read_csv(file, sep=';', encoding='latin1')
            else:
                df = pd.read_excel(file)

            # Adiciona uma coluna para identificar a origem dos dados
            df['Arquivo_Origem'] = file.name
            dataframes.append(df)

        except Exception as e:
            st.error(f"Erro ao processar o arquivo {file.name}: {e}")

        # Atualiza a barra de progresso
        my_bar.progress((i + 1) / len(uploaded_files), text=f"Processando: {file.name}")

    if dataframes:
        st.write("---")
        st.subheader("Prévia dos Dados Combinados")

        # Junta todos os dataframes da lista em um só
        df_final = pd.concat(dataframes, ignore_index=True)

        # Mostra as primeiras linhas e o total de registros
        st.dataframe(df_final.head(10))
        st.caption(f"Total de linhas combinadas: {len(df_final)} | Total de colunas: {len(df_final.columns)}")

        # Prepara o arquivo final para download em Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Dados_Combinados')

        st.write("---")
        # Botão de download
        st.download_button(
            label="📥 Baixar Arquivo Combinado (Excel)",
            data=buffer.getvalue(),
            file_name="arquivos_combinados.xlsx",
            mime="application/vnd.ms-excel"
        )
