import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Contagem de Estoque", layout="wide")

FILE_PATH = 'Base_estoque.xlsx'

def load_data():
    if os.path.exists(FILE_PATH):
        try:
            df = pd.read_excel(FILE_PATH)
            # Garantir que as colunas numéricas sejam tratadas como tal, substituindo NaN por 0
            cols_to_numeric = ['Câmara', 'Freezer 01', 'Freezer 02', 'TOTAL', 'Estoque Minimo', 'Planejamento de Produção ']
            for col in cols_to_numeric:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Zerar as colunas de contagem para iniciar a contagem
            cols_to_zero = ['Câmara', 'Freezer 01', 'Freezer 02', 'TOTAL']
            for col in cols_to_zero:
                if col in df.columns:
                    df[col] = 0
            
            # Calcular Planejamento inicial (Estoque Mínimo - Total)
            if 'Planejamento de Produção ' in df.columns and 'Estoque Minimo' in df.columns:
                df['Planejamento de Produção '] = df['Estoque Minimo'] - df['TOTAL']

            # Remover coluna inútil se existir
            if 'Unnamed: 8' in df.columns:
                df = df.drop(columns=['Unnamed: 8'])

            return df
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
            return None
    else:
        st.error(f"Arquivo {FILE_PATH} não encontrado.")
        return None

def save_data(df, selected_date):
    try:
        # Recalcular o Total
        # Assumindo que o Total é a soma das quantidades nos locais
        # Ajuste conforme a lógica de negócio real se necessário
        cols_to_sum = ['Câmara', 'Freezer 01', 'Freezer 02']
        # Verifica se as colunas existem antes de somar
        existing_cols = [c for c in cols_to_sum if c in df.columns]
        
        if existing_cols:
            df['TOTAL'] = df[existing_cols].sum(axis=1)
        
        # Calcular Planejamento (Total - Estoque Mínimo)
        if 'Planejamento de Produção ' in df.columns and 'Estoque Minimo' in df.columns:
             df['Planejamento de Produção '] = df['Estoque Minimo'] - df['TOTAL']
        
        # Salvar no arquivo com o nome da data selecionada
        date_str = selected_date.strftime("%d-%m-%Y")
        file_name = f"{date_str}_contagem.xlsx"
        
        df.to_excel(file_name, index=False)
        st.success(f"Contagem registrada com sucesso em {file_name}!")
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

st.title("📦 Sistema de Contagem de Estoque")

# Campo para inserir a data
selected_date = st.date_input("Data da Contagem", datetime.now(), format="DD/MM/YYYY")

if 'df_estoque' not in st.session_state:
    loaded_df = load_data()
    if loaded_df is not None:
        st.session_state.df_estoque = loaded_df
    else:
        st.stop()

def recalculate_totals(df):
    # Recalcular TOTAL
    cols_to_sum = ['Câmara', 'Freezer 01', 'Freezer 02']
    # Garantir numérico
    for col in cols_to_sum:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    existing_cols = [c for c in cols_to_sum if c in df.columns]
    if existing_cols:
        df['TOTAL'] = df[existing_cols].sum(axis=1)
    
    # Recalcular Planejamento
    if 'Planejamento de Produção ' in df.columns and 'Estoque Minimo' in df.columns:
        df['Planejamento de Produção '] = df['Estoque Minimo'] - df['TOTAL']
    
    return df

# Usar o dataframe do session_state
df = st.session_state.df_estoque

if df is not None:
    st.write("Edite as quantidades abaixo e clique em 'Salvar Contagem' ao finalizar.")
    
    # Configuração do editor de dados
    # Permitir edição apenas nas colunas de quantidade
    # Grupo e Produto devem ser apenas leitura idealmente, mas o data_editor permite tudo por padrão.
    # Vamos instruir o usuário.
    
    # Obter lista de grupos únicos ordenados
    if 'Grupo' in df.columns:
        groups = sorted(df['Grupo'].dropna().unique().tolist())
    else:
        groups = []

    if not groups:
        st.warning("Nenhum grupo encontrado no arquivo.")
        st.stop()

    if 'current_group_index' not in st.session_state:
        st.session_state.current_group_index = 0
    
    # Garantir que o índice esteja dentro dos limites (caso mude o arquivo)
    if st.session_state.current_group_index >= len(groups):
        st.session_state.current_group_index = 0

    # Navegação por Grupo
    st.markdown("### Navegação por Grupo")
    col_prev, col_sel, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("⬅️ Grupo Anterior", use_container_width=True):
            st.session_state.current_group_index = max(0, st.session_state.current_group_index - 1)
            st.rerun()
            
    with col_next:
        if st.button("Próximo Grupo ➡️", use_container_width=True):
            st.session_state.current_group_index = min(len(groups) - 1, st.session_state.current_group_index + 1)
            st.rerun()
            
    with col_sel:
        def update_index():
            st.session_state.current_group_index = groups.index(st.session_state.group_selector)

        selected_group = st.selectbox(
            "Selecione o Grupo", 
            options=groups, 
            index=st.session_state.current_group_index,
            key="group_selector",
            on_change=update_index,
            label_visibility="collapsed"
        )

    current_group = groups[st.session_state.current_group_index]
    
    # Filtrar dados para o grupo atual
    # Importante: Manter o índice original para poder atualizar o dataframe principal depois
    filtered_df = df[df['Grupo'] == current_group]
    
    st.info(f"Editando grupo: **{current_group}** ({len(filtered_df)} produtos)")

    column_config = {
        "Grupo": st.column_config.TextColumn("Grupo", disabled=True),
        "Produto": st.column_config.TextColumn("Produto", disabled=True),
        "Estoque Minimo": st.column_config.NumberColumn("Estoque Mínimo", disabled=True),
        "Câmara": st.column_config.NumberColumn("Câmara", min_value=0, step=1),
        "Freezer 01": st.column_config.NumberColumn("Freezer 01", min_value=0, step=1),
        "Freezer 02": st.column_config.NumberColumn("Freezer 02", min_value=0, step=1),
        "TOTAL": st.column_config.NumberColumn("TOTAL", disabled=True), # Total será calculado
        "Planejamento de Produção ":None
    }

    # Editor de dados para o grupo filtrado
    # Usamos uma chave dinâmica baseada no grupo para resetar o estado do editor ao trocar de grupo
    edited_filtered_df = st.data_editor(
        filtered_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key=f"editor_{current_group}"
    )

    # Lógica de atualização
    # Se o dataframe editado for diferente do filtrado original (antes da edição nesta interação)
    # Precisamos comparar com o que está no session_state para este grupo
    
    # Como o filtered_df vem do st.session_state.df_estoque, ele é o "estado atual salvo".
    # O edited_filtered_df é o "novo estado" vindo do frontend.
    
    if not edited_filtered_df.equals(filtered_df):
        # Atualizar o dataframe principal nas linhas correspondentes
        # O índice do edited_filtered_df é o mesmo do filtered_df, que é o mesmo do df original
        st.session_state.df_estoque.loc[edited_filtered_df.index] = edited_filtered_df
        
        # Recalcular totais no dataframe principal inteiro
        st.session_state.df_estoque = recalculate_totals(st.session_state.df_estoque)
        
        # Rerun para atualizar a interface e mostrar os totais calculados
        st.rerun()

    if st.button("Salvar Contagem", type="primary"):
        # Salvar o dataframe que já está no session_state (que está atualizado)
        save_data(st.session_state.df_estoque, selected_date)
