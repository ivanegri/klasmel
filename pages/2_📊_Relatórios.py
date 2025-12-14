import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime

st.set_page_config(page_title="Relatório de Estoque", layout="wide")

st.title("📊 Relatório de Estoque e Planejamento")

# Função para listar arquivos de contagem
def list_count_files():
    files = glob.glob("data/*_contagem.xlsx")
    file_data = []
    for f in files:
        try:
            # Extrair data do nome do arquivo (data/DD-MM-YYYY_contagem.xlsx)
            filename = os.path.basename(f)
            date_str = filename.split("_")[0]
            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
            file_data.append({"file": f, "date": date_obj})
        except Exception:
            continue
    
    # Ordenar por data (mais recente primeiro)
    file_data.sort(key=lambda x: x["date"], reverse=True)
    return file_data

files = list_count_files()

if not files:
    st.warning("Nenhum arquivo de contagem encontrado.")
    st.stop()

# Seleção de arquivo (padrão: mais recente)
latest_file = files[0]
file_options = {f["date"].strftime("%d/%m/%Y"): f for f in files}

selected_date_str = st.selectbox(
    "Selecione a data do relatório:",
    options=list(file_options.keys()),
    index=0
)

selected_file_data = file_options[selected_date_str]
file_path = selected_file_data["file"]

st.divider()

try:
    df = pd.read_excel(file_path)
    
    # Exibir data do arquivo
    st.subheader(f"📅 Situação em: {selected_date_str}")
    
    # Filtrar colunas relevantes
    # O usuário quer saber "o que tem" (TOTAL) e "planejamento"
    cols_to_show = ['Grupo', 'Produto', 'TOTAL', 'Estoque Minimo', 'Planejamento de Produção ']
    
    # Verificar se as colunas existem
    available_cols = [c for c in cols_to_show if c in df.columns]
    
    display_df = df[available_cols].copy()
    
    # Formatação condicional (opcional, mas bom para UX)
    # Destacar planejamento positivo (precisa produzir)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "TOTAL": st.column_config.NumberColumn("Estoque Atual", format="%d"),
            "Estoque Minimo": st.column_config.NumberColumn("Estoque Mínimo", format="%d"),
            "Planejamento de Produção ": st.column_config.NumberColumn("Planejamento (Produzir)", format="%d"),
        }
    )
    
    # Resumo / Métricas
    total_itens = len(df)
    total_estoque = df['TOTAL'].sum() if 'TOTAL' in df.columns else 0
    itens_para_produzir = df[df['Planejamento de Produção '] > 0].shape[0] if 'Planejamento de Produção ' in df.columns else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Produtos Cadastrados", total_itens)
    col2.metric("Quantidade Total em Estoque", f"{total_estoque:,.0f}")
    col3.metric("Itens com Necessidade de Produção", itens_para_produzir)

    st.divider()

    col_top_stock, col_top_prod = st.columns(2)

    with col_top_stock:
        st.subheader("🏆 Top 10 - Maior Estoque")
        if 'TOTAL' in df.columns:
            top_stock = df.nlargest(10, 'TOTAL')[['Produto', 'TOTAL']]
            st.dataframe(
                top_stock,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "TOTAL": st.column_config.NumberColumn("Quantidade", format="%d")
                }
            )

    with col_top_prod:
        st.subheader("⚠️ Top 10 - Necessidade de Produção")
        if 'Planejamento de Produção ' in df.columns:
            # Filtrar apenas os que precisam de produção (> 0)
            prod_needed = df[df['Planejamento de Produção '] > 0]
            if not prod_needed.empty:
                top_prod = prod_needed.nlargest(10, 'Planejamento de Produção ')[['Produto', 'Planejamento de Produção ']]
                st.dataframe(
                    top_prod,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Planejamento de Produção ": st.column_config.NumberColumn("Faltam", format="%d")
                    }
                )
            else:
                st.info("Nenhum produto com necessidade de produção.")

    st.divider()
    
    # Cálculo da Diferença (Estoque Atual - Estoque Mínimo)
    if 'TOTAL' in df.columns and 'Estoque Minimo' in df.columns:
        df['Diferenca'] = df['TOTAL'] - df['Estoque Minimo']
        
        col_diff_pos, col_diff_neg = st.columns(2)
        
        with col_diff_pos:
            st.subheader("📈 Top 10 - Diferença Positiva (Sobra)")
            # Estoque > Mínimo
            surplus = df[df['Diferenca'] > 0]
            if not surplus.empty:
                top_surplus = surplus.nlargest(10, 'Diferenca')[['Produto', 'TOTAL', 'Estoque Minimo', 'Diferenca']]
                st.dataframe(
                    top_surplus,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "TOTAL": st.column_config.NumberColumn("Atual", format="%d"),
                        "Estoque Minimo": st.column_config.NumberColumn("Mínimo", format="%d"),
                        "Diferenca": st.column_config.NumberColumn("Diferença", format="+%d")
                    }
                )
            else:
                st.info("Nenhum produto com estoque acima do mínimo.")
                
        with col_diff_neg:
            st.subheader("📉 Top 10 - Diferença Negativa (Falta)")
            # Estoque < Mínimo
            deficit = df[df['Diferenca'] < 0]
            if not deficit.empty:
                # Ordenar pelos mais negativos (menores valores)
                top_deficit = deficit.nsmallest(10, 'Diferenca')[['Produto', 'TOTAL', 'Estoque Minimo', 'Diferenca']]
                st.dataframe(
                    top_deficit,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "TOTAL": st.column_config.NumberColumn("Atual", format="%d"),
                        "Estoque Minimo": st.column_config.NumberColumn("Mínimo", format="%d"),
                        "Diferenca": st.column_config.NumberColumn("Diferença", format="%d")
                    }
                )
            else:
                st.info("Nenhum produto com estoque abaixo do mínimo.")
    
    # Botão para baixar o relatório filtrado (opcional)
    
except Exception as e:
    st.error(f"Erro ao ler o arquivo {file_path}: {e}")
