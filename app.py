import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.express as px
from flask import Flask
from dash.dependencies import Input, Output, State

# Inicializa Flask y Dash
server = Flask(__name__)
app = dash.Dash(__name__, server=server, routes_pathname_prefix='/')

# URL de Google Drive en formato descargable
ruta_excel = "https://docs.google.com/spreadsheets/d/12AjDUOziC0-ELzN7vxWv0RdfGj2qDs4P/export?format=xlsx"

# Cargar el archivo desde Google Drive
df = pd.read_excel(ruta_excel, header=2)

# ✅ Eliminar columnas sin nombre (Unnamed)
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

# ✅ Limpieza de nombres de columnas
df.columns = df.columns.str.strip()  # Elimina espacios en los nombres de columnas
df.columns = df.columns.str.replace(' ', '_')  # Reemplaza espacios con guiones bajos
df.columns = df.columns.str.replace(r'\n', '', regex=True)  # Elimina saltos de línea ocultos
print("📌 Columnas después de la limpieza:", df.columns)  # Verifica los nombres en la consola

# ✅ Verificar si la columna 'FECHA_DE_ATENCION' existe antes de manipularla
if 'FECHA_DE_ATENCION' in df.columns:
    df['FECHA_DE_ATENCION'] = df['FECHA_DE_ATENCION'].astype(str)
else:
    print("⚠️ La columna 'FECHA_DE_ATENCION' no existe en el archivo Excel.")

# ✅ Llenar valores NaN para evitar errores en la tabla
df = df.fillna("No disponible")

app.layout = html.Div(style={'fontFamily': 'Arial', 'backgroundColor': '#f4f4f9', 'padding': '20px'}, children=[
    html.H1("Filtro de REGISTRO DE CAMBIOS", style={'textAlign': 'center', 'color': '#2c3e50'}),

    # Filtro por columna y valor
    html.Div([
        html.Label("Selecciona columna a filtrar", style={'color': '#34495e'}),
        dcc.Dropdown(
            id='columna-filtro',
            options=[{'label': col.replace('_', ' '), 'value': col} for col in df.columns],
            placeholder="Selecciona columna",
            style={'marginBottom': '10px'}
        ),
        html.Label("Ingrese el valor a filtrar", style={'color': '#34495e'}),
        dcc.Input(id='valor-filtro', type='text', placeholder="Valor a filtrar", style={'marginRight': '10px'}),
        html.Button("Filtrar", id='btn-filtrar', n_clicks=0,
                    style={'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 'padding': '5px 10px'})
    ], style={'marginBottom': '20px'}),

    # Tabla con datos filtrados
    dash_table.DataTable(
        id='tabla-filtrada',
        columns=[{"name": col.replace('_', ' '), "id": col} for col in df.columns],
        data=df.to_dict('records'),  # Cargamos todos los datos inicialmente
        style_table={'overflowX': 'auto', 'marginTop': '20px'},
        style_header={'backgroundColor': '#16a085', 'color': 'white', 'fontWeight': 'bold'},
        style_data={'backgroundColor': '#ecf0f1', 'color': '#2c3e50'}
    ),

    # Gráfico de barras (opcional, para registros por personal u otro criterio)
    dcc.Graph(id='grafico-atenciones', style={'marginTop': '20px'})
])

@app.callback(
    [Output('tabla-filtrada', 'data'),
     Output('tabla-filtrada', 'columns'),
     Output('grafico-atenciones', 'figure')],
    [Input('btn-filtrar', 'n_clicks')],
    [State('columna-filtro', 'value'),
     State('valor-filtro', 'value')]
)
def actualizar_filtro(n_clicks, columna, valor):
    if n_clicks == 0 or not columna or not valor:
        return df.to_dict('records'), [{"name": i.replace('_', ' '), "id": i} for i in df.columns], px.bar(title="Seleccione un filtro")

    # ✅ Verificar que la columna seleccionada existe en el DataFrame antes de filtrar
    if columna not in df.columns:
        print(f"⚠️ La columna '{columna}' no existe en el DataFrame.")
        return df.to_dict('records'), [{"name": i.replace('_', ' '), "id": i} for i in df.columns], px.bar(title="Columna no encontrada")

    from unidecode import unidecode  # ✅ Importamos unidecode para eliminar tildes

# ✅ Función para normalizar texto
def normalizar_texto(texto):
    if isinstance(texto, str):  
        return unidecode(texto).lower()
    return texto

@app.callback(
    [Output('tabla-filtrada', 'data'),
     Output('tabla-filtrada', 'columns'),
     Output('grafico-atenciones', 'figure')],
    [Input('btn-filtrar', 'n_clicks')],
    [State('columna-filtro', 'value'),
     State('valor-filtro', 'value')]
)
def actualizar_filtro(n_clicks, columna, valor):
    if n_clicks == 0 or not columna or not valor:
        return df.to_dict('records'), [{"name": i.replace('_', ' '), "id": i} for i in df.columns], px.bar(title="Seleccione un filtro")

    # ✅ Normalizar el valor ingresado por el usuario
    valor_normalizado = normalizar_texto(valor)

    # ✅ Normalizar toda la columna antes de filtrar
    df_filtrado = df[df[columna].astype(str).apply(normalizar_texto).str.contains(valor_normalizado, na=False)]

    # ✅ Convertir todos los datos a string para evitar errores
    df_filtrado = df_filtrado.fillna("No disponible").astype(str)

    columns = [{"name": i.replace('_', ' '), "id": i} for i in df_filtrado.columns]
    data = df_filtrado.to_dict('records')

    # ✅ Verificamos si la columna 'PERSONAL' existe antes de graficar
    if 'PERSONAL' in df_filtrado.columns and not df_filtrado.empty:
        fig = px.bar(df_filtrado, x='PERSONAL', title="Registros por Personal", color='PERSONAL',
                     color_discrete_sequence=px.colors.qualitative.Set1)
    else:
        fig = px.bar(title="Sin resultados", template="simple_white")

    return data, columns, fig

    # ✅ Convertir todos los datos a string para evitar errores
    df_filtrado = df_filtrado.fillna("No disponible").astype(str)

    columns = [{"name": i.replace('_', ' '), "id": i} for i in df_filtrado.columns]
    data = df_filtrado.to_dict('records')

    # Verificamos si la columna 'PERSONAL' existe antes de graficar
    if 'PERSONAL' in df_filtrado.columns and not df_filtrado.empty:
        fig = px.bar(df_filtrado, x='PERSONAL', title="Registros por Personal", color='PERSONAL',
                     color_discrete_sequence=px.colors.qualitative.Set1)
    else:
        fig = px.bar(title="Sin resultados", template="simple_white")

    return data, columns, fig

if __name__ == '__main__':
    app.run_server(debug=True)