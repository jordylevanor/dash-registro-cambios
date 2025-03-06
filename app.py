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
    try:
        df = pd.read_excel(ruta_excel, header=2)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Eliminar columnas sin nombre
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace(r'\n', '', regex=True)  # Normalizar nombres de columnas
        if 'FECHA_DE_ATENCION' in df.columns:
            df['FECHA_DE_ATENCION'] = pd.to_datetime(df['FECHA_DE_ATENCION'], errors='coerce')  # Convertir a datetime
        df = df.fillna("No disponible")  # Llenar NaN
        return df
    except Exception as e:
        print("⚠️ Error al cargar el archivo:", e)
        return pd.DataFrame()  # Retorna un DataFrame vacío en caso de error

# ✅ Función para normalizar texto (evita problemas con mayúsculas y tildes)
def normalizar_texto(texto):
    if isinstance(texto, str):  
        return unidecode(texto).lower()
    return texto

# ✅ Cargar los datos inicialmente para evitar Dropdown vacío
df_inicial = cargar_datos()
opciones_columnas = [{'label': col.replace('_', ' '), 'value': col} for col in df_inicial.columns] if not df_inicial.empty else []

app.layout = html.Div(style={'fontFamily': 'Arial', 'backgroundColor': '#f4f4f9', 'padding': '20px'}, children=[
    html.H1("Filtro de REGISTRO DE CAMBIOS", style={'textAlign': 'center', 'color': '#2c3e50'}),

    # Filtros
    html.Div([
        html.Label("Selecciona columna a filtrar", style={'color': '#34495e'}),
        dcc.Dropdown(id='columna-filtro', options=opciones_columnas, placeholder="Selecciona columna", style={'marginBottom': '10px'}),

        html.Label("Ingrese el valor a filtrar", style={'color': '#34495e'}),
        dcc.Input(id='valor-filtro', type='text', placeholder="Valor a filtrar", style={'marginRight': '10px'}),

        html.Label("Seleccione un rango de fechas", style={'color': '#34495e'}),
        dcc.DatePickerRange(
            id='rango-fechas',
            start_date=None,
            end_date=None,
            display_format='YYYY-MM-DD',
            style={'marginRight': '10px'}
        ),

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

    # Gráficos
    dcc.Graph(id='grafico-atenciones', style={'marginTop': '20px'}),
    dcc.Graph(id='grafico-progreso', style={'marginTop': '20px'})
])

@app.callback(
    [Output('tabla-filtrada', 'data'),
     Output('tabla-filtrada', 'columns'),
     Output('grafico-atenciones', 'figure'),
     Output('grafico-progreso', 'figure'),
     Output('columna-filtro', 'options')],
    [Input('btn-filtrar', 'n_clicks')],
    [State('columna-filtro', 'value'),
     State('valor-filtro', 'value'),
     State('rango-fechas', 'start_date'),
     State('rango-fechas', 'end_date')]
)
def actualizar_filtro(n_clicks, columna, valor, fecha_inicio, fecha_fin):
    # ✅ Cargar SIEMPRE la última versión del archivo al hacer clic en "Filtrar"
    df = cargar_datos()

    # ✅ Generar opciones del dropdown con las columnas más recientes
    opciones_columnas = [{'label': col.replace('_', ' '), 'value': col} for col in df.columns] if not df.empty else []

    df_filtrado = df.copy()

    # ✅ Filtrar por texto si se ingresó un valor
    if columna and valor:
        valor_normalizado = normalizar_texto(valor)
        df_filtrado = df_filtrado[df_filtrado[columna].astype(str).apply(normalizar_texto).str.contains(valor_normalizado, na=False)]

    # ✅ Filtrar por rango de fechas
    if fecha_inicio and fecha_fin:
        fecha_inicio = pd.to_datetime(fecha_inicio)
        fecha_fin = pd.to_datetime(fecha_fin)
        df_filtrado = df_filtrado[(df_filtrado['FECHA_DE_ATENCION'] >= fecha_inicio) & 
                                  (df_filtrado['FECHA_DE_ATENCION'] <= fecha_fin)]

    # ✅ Convertir todos los datos a string para evitar errores
    df_filtrado = df_filtrado.fillna("No disponible").astype(str)

    columns = [{"name": i.replace('_', ' '), "id": i} for i in df_filtrado.columns]
    data = df_filtrado.to_dict('records')

    # ✅ Gráfico 1: Cantidad de atenciones por personal
    if not df_filtrado.empty and 'PERSONAL' in df_filtrado.columns:
        df_personal = df_filtrado['PERSONAL'].value_counts().reset_index()
        df_personal.columns = ['PERSONAL', 'Cantidad']
        
        fig_atenciones = px.bar(
            df_personal,
            x='PERSONAL',
            y='Cantidad',
            title="Atenciones por Personal",
            color='PERSONAL',
            text='Cantidad',  
            color_discrete_sequence=px.colors.qualitative.Set1
        )

        fig_atenciones.update_traces(textposition='outside')
        fig_atenciones.update_layout(yaxis_title="Número de Atenciones")
    else:
        fig_atenciones = px.bar(title="Sin resultados", template="simple_white")

    # ✅ Gráfico 2: Avance progresivo de atenciones
    if not df_filtrado.empty and 'FECHA_DE_ATENCION' in df_filtrado.columns:
        df_progreso = df_filtrado.copy()
        df_progreso['FECHA_DE_ATENCION'] = pd.to_datetime(df_progreso['FECHA_DE_ATENCION'])
        df_progreso = df_progreso.groupby(df_progreso['FECHA_DE_ATENCION'].dt.to_period('W')).size().reset_index(name='Atenciones')

        fig_progreso = px.line(df_progreso, x='FECHA_DE_ATENCION', y='Atenciones', title="Evolución de Atenciones Semanales",
                               markers=True, line_shape='spline')
    else:
        fig_progreso = px.line(title="Sin datos para mostrar", template="simple_white")

    return data, columns, fig_atenciones, fig_progreso, opciones_columnas