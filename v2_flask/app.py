from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from io import BytesIO
import pandas as pd
import os
from datetime import datetime
import glob
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Define data directory relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '../data')

def get_base_file_path():
    return os.path.join(DATA_DIR, 'Base_estoque.xlsx')

def get_count_file_path(date_str):
    return os.path.join(DATA_DIR, f'{date_str}_contagem.xlsx')

def get_historical_data():
    files = glob.glob(os.path.join(DATA_DIR, '*_contagem.xlsx'))
    data_points = []
    
    # Track all unique (product, group) pairs
    all_product_groups = set()

    for f in files:
        try:
            filename = os.path.basename(f)
            date_str_part = filename.split('_')[0]
            date_obj = datetime.strptime(date_str_part, '%d-%m-%Y')
            df = pd.read_excel(f)
            
            if 'TOTAL' in df.columns:
                df['TOTAL'] = pd.to_numeric(df['TOTAL'], errors='coerce').fillna(0)
            
            group_totals = {}
            if 'Grupo' in df.columns and 'TOTAL' in df.columns:
                group_totals = df.groupby('Grupo')['TOTAL'].sum().to_dict()
            
            current_products = {}
            if 'Produto' in df.columns and 'TOTAL' in df.columns and 'Grupo' in df.columns:
                for _, row in df.iterrows():
                    p = row['Produto']
                    g = row['Grupo']
                    t = row['TOTAL']
                    # Use a tuple key (Product, Group)
                    key = (p, g)
                    current_products[key] = t
                    all_product_groups.add(key)
            
            data_points.append({
                'date': date_obj,
                'date_str': date_str_part,
                'groups': group_totals,
                'products': current_products
            })
        except Exception:
            continue
    
    data_points.sort(key=lambda x: x['date'])
    
    dates = [dp['date_str'] for dp in data_points]
    
    # Process Groups
    all_groups = set()
    for dp in data_points:
        all_groups.update(dp['groups'].keys())
    
    groups_series = []
    for g in sorted(all_groups):
        data = []
        for dp in data_points:
            data.append(dp['groups'].get(g, 0))
        groups_series.append({'label': g, 'data': data})
        
    # Process Products
    products_series = []
    # Sort by Group then Product
    for p, g in sorted(list(all_product_groups), key=lambda x: (x[1], x[0])):
        data = []
        for dp in data_points:
            data.append(dp['products'].get((p, g), 0))
        products_series.append({'label': p, 'group': g, 'data': data})
        
    return {
        'dates': dates,
        'groups': groups_series,
        'products': products_series
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/count', methods=['GET', 'POST'])
def count():
    if request.method == 'POST':
        try:
            data = request.json
            date_str = data.get('date')
            items = data.get('items')

            if not date_str or not items:
                return jsonify({'success': False, 'message': 'Dados inválidos.'}), 400

            # Convert items back to DataFrame
            df = pd.DataFrame(items)
            
            # Ensure numeric columns
            cols_to_numeric = ['Câmara', 'Freezer 01', 'Freezer 02', 'TOTAL', 'Estoque Minimo', 'Planejamento de Produção ']
            for col in cols_to_numeric:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Calculate Total and Planning
            cols_to_sum = ['Câmara', 'Freezer 01', 'Freezer 02']
            existing_sum_cols = [c for c in cols_to_sum if c in df.columns]
            if existing_sum_cols:
                df['TOTAL'] = df[existing_sum_cols].sum(axis=1)
            
            if 'Planejamento de Produção ' in df.columns and 'Estoque Minimo' in df.columns:
                df['Planejamento de Produção '] = df['Estoque Minimo'] - df['TOTAL']

            # Save to Excel
            # Format date for filename
            try:
                # Expecting YYYY-MM-DD from HTML input
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d-%m-%Y')
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de data inválido.'}), 400

            file_path = get_count_file_path(formatted_date)
            df.to_excel(file_path, index=False)

            return jsonify({'success': True, 'message': f'Contagem salva com sucesso em {formatted_date}_contagem.xlsx!'})

        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # GET request: Load base data
    base_path = get_base_file_path()
    if not os.path.exists(base_path):
        flash(f'Arquivo base não encontrado em {base_path}', 'error')
        return redirect(url_for('index'))

    try:
        df = pd.read_excel(base_path)
        
        # Prepare data for frontend
        # Clean and initialize
        cols_to_numeric = ['Câmara', 'Freezer 01', 'Freezer 02', 'TOTAL', 'Estoque Minimo', 'Planejamento de Produção ']
        for col in cols_to_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Zero out counts for new count
        cols_to_zero = ['Câmara', 'Freezer 01', 'Freezer 02', 'TOTAL']
        for col in cols_to_zero:
            if col in df.columns:
                df[col] = 0
        
        # Initial Planning calculation
        if 'Planejamento de Produção ' in df.columns and 'Estoque Minimo' in df.columns:
            df['Planejamento de Produção '] = df['Estoque Minimo'] - df['TOTAL']

        if 'Unnamed: 8' in df.columns:
            df = df.drop(columns=['Unnamed: 8'])

        # Get unique groups
        groups = sorted(df['Grupo'].dropna().unique().tolist()) if 'Grupo' in df.columns else []
        
        # Convert to records for JS
        records = df.to_dict('records')
        
        return render_template('count.html', groups=groups, data=records, today=datetime.now().strftime('%Y-%m-%d'))

    except Exception as e:
        flash(f'Erro ao ler arquivo base: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<date_str>')
def download_report(date_str):
    # date_str is expected to be DD-MM-YYYY as in the filename
    filename = f'{date_str}_contagem.xlsx'
    file_path = os.path.join(DATA_DIR, filename)
    
    if not os.path.exists(file_path):
        flash('Arquivo não encontrado.', 'error')
        return redirect(url_for('reports'))
        
    try:
        df = pd.read_excel(file_path)
        
        # Calculate Group Totals
        group_cols = ['Câmara', 'Freezer 01', 'Freezer 02', 'TOTAL']
        # Ensure cols exist
        existing_cols = [c for c in group_cols if c in df.columns]
        
        if 'Grupo' in df.columns and existing_cols:
            group_totals = df.groupby('Grupo')[existing_cols].sum().reset_index()
        else:
            group_totals = pd.DataFrame()

        # Create Excel in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Detalhado', index=False)
            if not group_totals.empty:
                group_totals.to_excel(writer, sheet_name='Resumo por Grupo', index=False)
                
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'Relatorio_Estoque_{date_str}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Erro ao gerar download: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/reports')
def reports():
    # List files
    files = glob.glob(os.path.join(DATA_DIR, '*_contagem.xlsx'))
    file_options = []
    for f in files:
        try:
            filename = os.path.basename(f)
            date_str_part = filename.split('_')[0]
            date_obj = datetime.strptime(date_str_part, '%d-%m-%Y')
            file_options.append({
                'filename': filename,
                'date': date_obj,
                'date_str': date_obj.strftime('%d/%m/%Y'),
                'raw_date': date_str_part
            })
        except Exception:
            continue
    
    file_options.sort(key=lambda x: x['date'], reverse=True)
    
    selected_date = request.args.get('date')
    selected_file = None
    
    if file_options:
        if selected_date:
            # Find file by raw_date
            for f in file_options:
                if f['raw_date'] == selected_date:
                    selected_file = f
                    break
        else:
            selected_file = file_options[0]
    
    report_data = None
    if selected_file:
        try:
            file_path = os.path.join(DATA_DIR, selected_file['filename'])
            df = pd.read_excel(file_path)
            
            # Calculate metrics
            total_items = len(df)
            total_stock = df['TOTAL'].sum() if 'TOTAL' in df.columns else 0
            prod_col = 'Planejamento de Produção '
            items_to_produce = df[df[prod_col] > 0].shape[0] if prod_col in df.columns else 0
            
            # Top Lists
            top_stock = []
            if 'TOTAL' in df.columns:
                cols = ['Grupo', 'Produto', 'TOTAL'] if 'Grupo' in df.columns else ['Produto', 'TOTAL']
                top_stock = df.nlargest(10, 'TOTAL')[cols].to_dict('records')
                
            top_prod = []
            if prod_col in df.columns:
                cols = ['Grupo', 'Produto', prod_col] if 'Grupo' in df.columns else ['Produto', prod_col]
                top_prod = df[df[prod_col] > 0].nlargest(10, prod_col)[cols].to_dict('records')
                
            # Difference
            top_surplus = []
            top_deficit = []
            if 'TOTAL' in df.columns and 'Estoque Minimo' in df.columns:
                df['Diferenca'] = df['TOTAL'] - df['Estoque Minimo']
                cols = ['Grupo', 'Produto', 'TOTAL', 'Estoque Minimo', 'Diferenca'] if 'Grupo' in df.columns else ['Produto', 'TOTAL', 'Estoque Minimo', 'Diferenca']
                top_surplus = df[df['Diferenca'] > 0].nlargest(10, 'Diferenca')[cols].to_dict('records')
                top_deficit = df[df['Diferenca'] < 0].nsmallest(10, 'Diferenca')[cols].to_dict('records')

            report_data = {
                'total_items': total_items,
                'total_stock': total_stock,
                'items_to_produce': items_to_produce,
                'top_stock': top_stock,
                'top_prod': top_prod,
                'top_surplus': top_surplus,
                'top_deficit': top_deficit
            }
            
        except Exception as e:
            flash(f'Erro ao carregar relatório: {str(e)}', 'error')

    history = get_historical_data()
    return render_template('reports.html', file_options=file_options, selected_file=selected_file, report_data=report_data, history=history)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
