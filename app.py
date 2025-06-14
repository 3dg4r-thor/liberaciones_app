from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(_name)  # Nota: __name, no _name

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

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000, debug=True)