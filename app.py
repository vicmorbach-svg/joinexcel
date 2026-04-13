import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Mesclar e Otimizar Arquivos", page_icon="🗜️", layout="wide")

st.title("🗜️ Juntar e Exportar Arquivos (Excel, CSV, Parquet)")
st.write("Faça o upload, limpe os dados e baixe no formato ideal para o seu volume de dados.")

uploaded_files = st.file_uploader(
    "Arraste e solte ou escolha os arquivos", 
    type=["xlsx", "xls", "csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    dataframes = []
    my_bar = st.progress(0, text="Lendo arquivos...")

    for i, file in enumerate(uploaded_files):
        try:
            if file.name.endswith('.csv'):
                try:
                    df = pd.read_csv(file, engine='pyarrow')
                except Exception:
                    file.seek(0)
                    df = pd.read_csv(file, sep=';', encoding='latin1')
            else:
                df = pd.read_excel(file, engine='calamine')

            df['Arquivo_Origem'] = file.name
            dataframes.append(df)
        except Exception as e:
            st.error(f"Erro no arquivo {file.name}: {e}")

        my_bar.progress((i + 1) / len(uploaded_files), text=f"Processado: {file.name}")

    if dataframes:
        df_bruto = pd.concat(dataframes, ignore_index=True)

        st.write("---")
        st.header("🛠️ Reduzir Tamanho do Arquivo Final")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("1. Escolha as Colunas")
            todas_colunas = df_bruto.columns.tolist()
            colunas_selecionadas = st.multiselect(
                "Remova as colunas que você não precisa exportar:",
                options=todas_colunas,
                default=todas_colunas
            )

        with col2:
            st.subheader("2. Limpeza e Compressão")
            remover_vazias = st.checkbox("Remover linhas totalmente vazias", value=True)
            remover_duplicadas = st.checkbox("Remover linhas duplicadas")
            otimizar_memoria = st.checkbox("Comprimir tipos de dados (Recomendado)", value=True)

        # Aplicando as reduções
        df_final = df_bruto.copy()

        if colunas_selecionadas:
            df_final = df_final[colunas_selecionadas]

        if remover_vazias:
            df_final = df_final.dropna(how='all')

        if remover_duplicadas:
            df_final = df_final.drop_duplicates()

        if otimizar_memoria:
            for col in df_final.columns:
                if df_final[col].dtype == 'float64':
                    df_final[col] = pd.to_numeric(df_final[col], downcast='float')
                elif df_final[col].dtype == 'int64':
                    df_final[col] = pd.to_numeric(df_final[col], downcast='integer')
                elif df_final[col].dtype == 'object':
                    if len(df_final[col].unique()) / len(df_final[col]) < 0.5:
                        df_final[col] = df_final[col].astype('category')

        st.write("---")
        st.subheader("Resumo da Redução")
        st.success(f"**Linhas finais:** {len(df_final):,} | **Colunas finais:** {len(df_final.columns)}".replace(',', '.'))
        st.dataframe(df_final.head(5), use_container_width=True)

        st.write("---")
        st.subheader("Opções de Download")
        st.info("💡 Para arquivos gigantes, o formato **Parquet** é o mais recomendado. Ele comprime os dados e abre muito mais rápido no Power BI ou Python.")

        # Criando 3 colunas para os botões de download
        col_dl1, col_dl2, col_dl3 = st.columns(3)

        with col_dl1:
            # Geração de Parquet (Mais rápido e leve)
            parquet_buffer = io.BytesIO()
            df_final.to_parquet(parquet_buffer, engine='pyarrow', index=False)
            st.download_button(
                label="🚀 Baixar Ultra Leve (Parquet)",
                data=parquet_buffer.getvalue(),
                file_name="dados_otimizados.parquet",
                mime="application/octet-stream",
                use_container_width=True
            )

        with col_dl2:
            # Geração de CSV
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⚡ Baixar Rápido (CSV)",
                data=csv_data,
                file_name="dados_otimizados.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_dl3:
            # Geração de Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Dados')

            st.download_button(
                label="📊 Baixar Pesado (Excel)",
                data=buffer.getvalue(),
                file_name="dados_otimizados.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
