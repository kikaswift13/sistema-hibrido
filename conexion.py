from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "1234"),
        database=os.getenv("DB_NAME", "sistema_hibrido"),
        port=int(os.getenv("DB_PORT", 3306))
    )

@app.route('/')
def index():
    tabla = request.args.get('tabla', 'Products')
    busqueda = request.args.get('busqueda', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener columnas
    cursor.execute(f"SHOW COLUMNS FROM {tabla}")
    columnas_info = cursor.fetchall()
    columnas = [col['Field'] for col in columnas_info]

    # 🔎 CONSULTA CON BÚSQUEDA
    if busqueda:
        condiciones = " OR ".join([f"{col} LIKE %s" for col in columnas])
        valores = ["%" + busqueda + "%"] * len(columnas)

        query = f"SELECT * FROM {tabla} WHERE {condiciones} LIMIT 50"
        cursor.execute(query, valores)
    else:
        cursor.execute(f"SELECT * FROM {tabla} LIMIT 50")

    datos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'index.html',
        datos=datos,
        columnas=columnas,
        tabla=tabla
    )

@app.route('/add', methods=['POST'])
def add():
    tabla = request.form.get('tabla')

    conn = get_db_connection()
    cursor = conn.cursor()

    data = request.form.to_dict()
    data.pop('tabla')

    columnas = ", ".join(data.keys())
    valores = ", ".join(["%s"] * len(data))

    query = f"INSERT INTO {tabla} ({columnas}) VALUES ({valores})"

    cursor.execute(query, list(data.values()))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(f"/?tabla={tabla}")

@app.route('/delete/<tabla>/<id>')
def delete(tabla, id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Detectar primary key automáticamente
    cursor.execute(f"SHOW KEYS FROM {tabla} WHERE Key_name = 'PRIMARY'")
    pk = cursor.fetchone()[4]

    cursor.execute(f"DELETE FROM {tabla} WHERE {pk}=%s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/?tabla={tabla}")

if __name__ == '__main__':
    app.run(debug=True)