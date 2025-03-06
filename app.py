import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.express as px
from flask import Flask
from dash.dependencies import Input, Output, State
from unidecode import unidecode  

# Inicializa Flask y Dash
server = Flask(__name__)
app = dash.Dash(__name__, server=server, routes_pathname_prefix='/')

# ✅ URL de Google Drive en formato descargable
ruta_excel = "https://docs.google.com/spreadsheets/d/12AjDUOziC0-ELzN7vxWv0RdfGj2qDs4P/export?format=xlsx"

# ✅ Función para cargar siempre la versión más reciente del archivo
def cargar_datos():
    df = pd.read_excel(ruta_excel, header=2)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Eliminar columnas sin nombre
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace(r'\n', '', regex=True)  # Normalizar columnas
    if 'FECHA_DE_ATENCION' in df.columns:
        df['FECHA_DE_ATENCION'] = pd.to_datetime(df['FECHA_DE_ATENCION'], errors='coerce').dt.date
    df = df.fillna("No disponible")  # Llenar NaN
    return df

# ✅ Función para normalizar texto (elimina mayúsculas y tildes)
def normalizar_texto(texto):
    if isinstance(texto, str):  
        return unidecode(texto).lower()
    return texto

app.layout = html.Div(style={'fontFamily': 'Arial', 'backgroundColor': '#f4f4f9', 'padding': '20px'}, children=[
    html.H1("Filtro de REGISTRO DE CAMBIOS", style={'textAlign': 'center', 'color': '#2c3e50'}),

    # Filtros
    html.Div([
        html.Label("Selecciona columna a filtrar", style={'color': '#34495e'}),
        dcc.Dropdown(id='columna-filtro', placeholder="Selecciona columna", style={'marginBottom': '10px'}),
        html.Label("Ingrese el valor a filtrar", style={'color': '#34495e'}),
        dcc.Input(id='valor-filtro', type='text', placeholder="Valor a filtrar", style={'marginRight': '10px'}),
        html.Label("Seleccione una fecha", style={'color': '#34495e'}),
        dcc.DatePickerSingle(id='fecha-filtro', date=None, display_format='YYYY-MM-DD'),
        html.Button("Filtrar", id='btn-filtrar', n_clicks=0,
                    style={'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'padding': '5px 10px'})
    ], style={'marginBottom': '20px'}),

    # Tabla de datos
    dash_table.DataTable(
        id='tabla-filtrada',
        style_table={'overflowX': 'auto', 'marginTop': '20px'},
        style_header={'backgroundColor': '#16a085', 'color': 'white', 'fontWeight': 'bold'},
        style_data={'backgroundColor': '#ecf0f1', 'color': '#2c3e50'}
    ),

    # Gráfico de barras
    dcc.Graph(id='grafico-atenciones', style={'marginTop': '20px'})
])

@app.callback(
    [Output('tabla-filtrada', 'data'),
     Output('tabla-filtrada', 'columns'),
     Output('grafico-atenciones', 'figure'),
     Output('columna-filtro', 'options')],
    [Input('btn-filtrar', 'n_clicks')],
    [State('columna-filtro', 'value'),
     State('valor-filtro', 'value'),
     State('fecha-filtro', 'date')]
)
def actualizar_filtro(n_clicks, columna, valor, fecha):
    # ✅ Cargar SIEMPRE la última versión del archivo al hacer clic en "Filtrar"
    df = cargar_datos()

    # ✅ Generar opciones del dropdown con las columnas más recientes
    opciones_columnas = [{'label': col.replace('_', ' '), 'value': col} for col in df.columns]

    df_filtrado = df.copy()

    # ✅ Filtrar por texto si se ingresó un valor
    if columna and valor:
        valor_normalizado = normalizar_texto(valor)
        df_filtrado = df_filtrado[df_filtrado[columna].astype(str).apply(normalizar_texto).str.contains(valor_normalizado, na=False)]

    # ✅ Filtrar por fecha si se seleccionó una fecha
    if fecha:
        fecha = pd.to_datetime(fecha).date()
        df_filtrado = df_filtrado[df_filtrado['FECHA_DE_ATENCION'] == fecha]

    # ✅ Convertir todos los datos a string para evitar errores
    df_filtrado = df_filtrado.fillna("No disponible").astype(str)

    columns = [{"name": i.replace('_', ' '), "id": i} for i in df_filtrado.columns]
    data = df_filtrado.to_dict('records')

    # ✅ Verificar si la columna 'PERSONAL' existe antes de graficar
    if 'PERSONAL' in df_filtrado.columns and not df_filtrado.empty:
        fig = px.bar(df_filtrado, x='PERSONAL', title="Registros por Personal", color='PERSONAL',
                     color_discrete_sequence=px.colors.qualitative.Set1)
    else:
        fig = px.bar(title="Sin resultados", template="simple_white")

    return data, columns, fig, opciones_columnas

if __name__ == '__main__':
    app.run_server(debug=True)