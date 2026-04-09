import streamlit as st
import pandas as pd
import io

# Configuração da página
st.set_page_config(page_title="Mesclar Arquivos (Alta Performance)", page_icon="⚡", layout="wide")

st.title("⚡ Juntar Arquivos (Modo Rápido)")
st.write("Faça o upload de vários arquivos. O sistema usa motores otimizados para processar grandes volumes de dados.")

uploaded_files = st.file_uploader(
    "Arraste e solte ou escolha os arquivos", 
    type=["xlsx", "xls", "csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    dataframes = []

    progress_text = "Lendo arquivos em alta velocidade..."
    my_bar = st.progress(0, text=progress_text)

    for i, file in enumerate(uploaded_files):
        try:
            if file.name.endswith('.csv'):
                try:
                    # Tenta ler com pyarrow (muito mais rápido para arquivos grandes)
                    df = pd.read_csv(file, engine='pyarrow')
                except Exception:
                    # Fallback para o padrão brasileiro se o pyarrow falhar na codificação
                    file.seek(0)
                    df = pd.read_csv(file, sep=';', encoding='latin1')
            else:
                # Usa o motor calamine (extremamente rápido para Excel)
                df = pd.read_excel(file, engine='calamine')

            df['Arquivo_Origem'] = file.name
            dataframes.append(df)

        except Exception as e:
            st.error(f"Erro ao processar o arquivo {file.name}: {e}")

        my_bar.progress((i + 1) / len(uploaded_files), text=f"Processado: {file.name}")

    if dataframes:
        st.write("---")
        st.subheader("Prévia dos Dados Combinados")

        # Concatenação otimizada
        df_final = pd.concat(dataframes, ignore_index=True)

        st.dataframe(df_final.head(10), use_container_width=True)
        st.caption(f"Total de linhas: {len(df_final):,} | Total de colunas: {len(df_final.columns)}".replace(',', '.'))

        st.write("---")
        st.subheader("Opções de Download")
        st.info("💡 Para arquivos muito grandes, o download em CSV é gerado quase instantaneamente, enquanto o Excel pode demorar vários minutos.")

        col1, col2 = st.columns(2)

        with col1:
            # Geração rápida de CSV
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⚡ Baixar Rápido (CSV)",
                data=csv_data,
                file_name="arquivos_combinados.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            # Geração tradicional de Excel (mais lenta)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Dados')

            st.download_button(
                label="📊 Baixar Formatado (Excel)",
                data=buffer.getvalue(),
                file_name="arquivos_combinados.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
