import pandas as pd

try:
    df = pd.read_excel('Base_estoque.xlsx')
    print(df.columns.tolist())
    print(df.head())
except Exception as e:
    print(e)
