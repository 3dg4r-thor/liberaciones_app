from flask import Flask, render_template, request, redirect, send_file, session, url_for
import sqlite3
from datetime import datetime
import pytz
from io import BytesIO
from xhtml2pdf import pisa
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'Torresrod_9413'

# Crear tablas si no existen
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return redirect('/login')

@app.route('/registrar_usuario', methods=['GET', 'POST'])
def registrar_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('liberaciones.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return render_template('registrar_usuario.html', error="Nombre de usuario ya existe")
        finally:
            conn.close()

    return render_template('registrar_usuario.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('liberaciones.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['usuario'] = username
            return redirect('/registro')
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/login')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'usuario' not in session:
        return redirect('/login')

    if request.method == 'POST':
        zona_horaria = pytz.timezone('America/Mexico_City')
        fecha = datetime.now(zona_horaria).strftime("%Y-%m-%d %H:%M:%S")
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
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('liberaciones.db')
    cursor = conn.cursor()

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
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('liberaciones.db')
    cursor = conn.cursor()

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

    rendered_html = render_template('historial_pdf.html', datos=datos)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(rendered_html, dest=result)

    if pisa_status.err:
        return "Error al generar PDF", 500

    result.seek(0)
    return send_file(result, download_name="historial.pdf", as_attachment=True)

@app.route('/exportar_excel')
def exportar_excel():
    if 'usuario' not in session:
        return redirect('/login')

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

    df = pd.DataFrame(rows, columns=[
        'ID', 'Fecha', 'Área', 'Tipo de Producto', 'Código', 'Orden', 'Cantidad',
        'Estado', 'Responsable', 'Observaciones'
    ])

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