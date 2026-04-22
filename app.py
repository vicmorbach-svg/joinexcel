import streamlit as st
import pandas as pd
import io
import gc  # Biblioteca nativa do Python para limpar a memória RAM

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
        # 1. Junta os arquivos direto na variável final (sem criar df_bruto)
        df_final = pd.concat(dataframes, ignore_index=True)

        # 2. Limpeza imediata de memória
        del dataframes # Deleta a lista original da memória
        gc.collect()   # Força o servidor a esvaziar a lixeira da RAM

        st.write("---")
        st.header("🛠️ Reduzir Tamanho do Arquivo Final")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("1. Escolha as Colunas")
            todas_colunas = df_final.columns.tolist()
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

        # Aplicando as reduções diretamente no df_final
        if colunas_selecionadas and len(colunas_selecionadas) < len(todas_colunas):
            df_final = df_final[colunas_selecionadas]
            gc.collect() # Limpa a memória das colunas descartadas

        if remover_vazias:
            df_final = df_final.dropna(how='all')

        if remover_duplicadas:
            df_final = df_final.drop_duplicates()

        # Correção do erro do PyArrow (Object para String)
        for col in df_final.select_dtypes(include=['object']).columns:
            try:
                df_final[col] = df_final[col].astype("string")
            except:
                pass

        if otimizar_memoria:
            for col in df_final.columns:
                try:
                    if df_final[col].dtype == 'float64':
                        df_final[col] = pd.to_numeric(df_final[col], downcast='float')
                    elif df_final[col].dtype == 'int64':
                        df_final[col] = pd.to_numeric(df_final[col], downcast='integer')
                    elif df_final[col].dtype == 'string':
                        if len(df_final[col].unique()) / len(df_final[col]) < 0.5:
                            df_final[col] = df_final[col].astype('category')
                except:
                    pass

        st.write("---")
        st.subheader("Resumo da Redução")
        st.success(f"**Linhas finais:** {len(df_final):,} | **Colunas finais:** {len(df_final.columns)}".replace(',', '.'))
        st.dataframe(df_final.head(5), use_container_width=True)

        st.write("---")
        st.subheader("Opções de Download")
        st.info("💡 Para arquivos gigantes, o formato **Parquet** é o mais recomendado. Ele comprime os dados e abre muito mais rápido no Power BI ou Python.")

        col_dl1, col_dl2, col_dl3 = st.columns(3)

        with col_dl1:
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
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⚡ Baixar Rápido (CSV)",
                data=csv_data,
                file_name="dados_otimizados.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_dl3:
            # Função para limpar a memória RAM logo após o download
            def limpar_memoria_excel():
                if 'excel_buffer' in st.session_state:
                    del st.session_state['excel_buffer']
                    import gc
                    gc.collect()

            # 1. Se o arquivo ainda não foi gerado, mostra o botão de "Gerar"
            if 'excel_buffer' not in st.session_state:
                if st.button("⚙️ Preparar Excel (Pesado)", use_container_width=True):
                    with st.spinner("Processando arquivo Excel..."):
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            df_final.to_excel(writer, index=False, sheet_name='Dados')

                        # Salva o arquivo temporariamente na sessão e recarrega a tela
                        st.session_state['excel_buffer'] = buffer.getvalue()
                        st.rerun()

            # 2. Se o arquivo já foi gerado, mostra o botão de "Baixar"
            else:
                st.download_button(
                    label="📊 Baixar Excel",
                    data=st.session_state['excel_buffer'],
                    file_name="dados_otimizados.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True,
                    on_click=limpar_memoria_excel # Limpa a memória ao clicar
                )
