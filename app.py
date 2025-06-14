from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime
from io import BytesIO
from xhtml2pdf import pisa
import pandas as pd
import io

app = Flask(__name__)  

# Crear la base de datos si no existe
def init_db():
    conn = sqlite3.connect('liberaciones.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS liberaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            area TEXT,
            tipo_producto TEXT,
            codigo_producto TEXT,
            numero_orden TEXT,
            cantidad INTEGER,
            estado TEXT,
            responsable TEXT,
            observaciones TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return redirect('/registro')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        area = request.form['area']
        tipo_producto = request.form['tipo_producto']
        codigo_producto = request.form['codigo_producto']
        numero_orden = request.form['numero_orden']
        cantidad = request.form['cantidad']
        estado = request.form['estado']
        responsable = request.form['responsable']
        observaciones = request.form['observaciones']

        conn = sqlite3.connect('liberaciones.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO liberaciones (
                fecha, area, tipo_producto, codigo_producto,
                numero_orden, cantidad, estado, responsable, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fecha, area, tipo_producto, codigo_producto,
              numero_orden, cantidad, estado, responsable, observaciones))
        conn.commit()
        conn.close()
        return redirect('/historial')

    return render_template('registro.html')

@app.route('/historial', methods=['GET'])
def historial():
    conn = sqlite3.connect('liberaciones.db')
    cursor = conn.cursor()

    # Obtener los filtros del formulario
    fecha = request.args.get('fecha')
    tipo_producto = request.args.get('tipo_producto')
    area = request.args.get('area')

    query = "SELECT * FROM liberaciones WHERE 1=1"
    params = []

    if fecha:
        query += " AND date(fecha) = ?"
        params.append(fecha)
    if tipo_producto:
        query += " AND tipo_producto = ?"
        params.append(tipo_producto)
    if area:
        query += " AND area = ?"
        params.append(area)

    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()

    return render_template('historial.html', datos=datos)
@app.route('/exportar_pdf')
def exportar_pdf():
    conn = sqlite3.connect('liberaciones.db')
    cursor = conn.cursor()

    # Filtros
    fecha = request.args.get('fecha')
    tipo_producto = request.args.get('tipo_producto')
    area = request.args.get('area')

    query = "SELECT * FROM liberaciones WHERE 1=1"
    params = []

    if fecha:
        query += " AND date(fecha) = ?"
        params.append(fecha)
    if tipo_producto:
        query += " AND tipo_producto = ?"
        params.append(tipo_producto)
    if area:
        query += " AND area = ?"
        params.append(area)

    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()

    # Renderizar plantilla HTML
    rendered_html = render_template('historial_pdf.html', datos=datos)

    # Convertir HTML a PDF
    result = BytesIO()
    pisa_status = pisa.CreatePDF(rendered_html, dest=result)

    if pisa_status.err:
        return "Error al generar PDF", 500

    result.seek(0)
    return send_file(result, download_name="historial.pdf", as_attachment=True)


@app.route('/exportar_excel')
def exportar_excel():
    fecha = request.args.get('fecha')
    tipo_producto = request.args.get('tipo_producto')
    area = request.args.get('area')

    conn = sqlite3.connect('liberaciones.db')
    cursor = conn.cursor()

    query = "SELECT * FROM liberaciones WHERE 1=1"
    params = []

    if fecha:
        query += " AND date(fecha) = ?"
        params.append(fecha)
    if tipo_producto:
        query += " AND tipo_producto = ?"
        params.append(tipo_producto)
    if area:
        query += " AND area = ?"
        params.append(area)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # Crear DataFrame
    df = pd.DataFrame(rows, columns=[
        'ID', 'Fecha', 'Área', 'Tipo de Producto', 'Código', 'Orden', 'Cantidad',
        'Estado', 'Responsable', 'Observaciones'
    ])

    # Convertir a Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Liberaciones')
    output.seek(0)

    return send_file(
        output,
        download_name='liberaciones.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)