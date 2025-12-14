import streamlit as st

st.set_page_config(
    page_title="Klasmel - Sistema de Estoque",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Klasmel - Sistema de Gestão de Estoque")

st.markdown("""
### Bem-vindo ao Sistema de Controle de Estoque e Produção

Este sistema foi desenvolvido para facilitar o gerenciamento do estoque e o planejamento da produção.

#### 👈 Utilize o menu lateral para navegar:

- **📝 Contagem**: Realize a contagem física do estoque, atualize quantidades e registre as datas.
- **📊 Relatórios**: Visualize indicadores de desempenho, itens com estoque baixo e necessidades de produção.

---
**Instruções Rápidas:**
1. Mantenha o arquivo `Base_estoque.xlsx` atualizado na pasta raiz.
2. Ao finalizar uma contagem, um novo arquivo com a data será gerado.
3. O relatório sempre busca o arquivo de contagem mais recente por padrão.
""")

st.sidebar.success("Selecione uma página acima.")
