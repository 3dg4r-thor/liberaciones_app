from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

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

@app.route('/historial')
def historial():
    conn = sqlite3.connect('liberaciones.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM liberaciones ORDER BY fecha DESC')
    datos = cursor.fetchall()
    conn.close()
    return render_template('historial.html', datos=datos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)