# ============================================================
#  app.py — Backend Flask
# ============================================================
#
#  INSTALACIÓN (una sola vez):
#  pip install flask oracledb python-dotenv
#
# ============================================================

from flask import Flask, request, jsonify, session, redirect, render_template, url_for
import oracledb
import os
#from dotenv import load_dotenv

#load_dotenv()
oracledb.init_oracle_client()

# ─────────────────────────────────────────
#  CONFIGURACIÓN — Cambia estos valores
# ─────────────────────────────────────────
USUARIO  = "tu_usuario"        # Ej: "UDEP_USER"
PASSWORD = "tu_password"       # Ej: "miPassword123"
HOST     = "192.168.1.100"     # IP o nombre del servidor Oracle
PUERTO   = 1521                # Puerto por defecto Oracle
SERVICIO = "ORCL"              # Nombre del servicio (SID o Service Name)
# ─────────────────────────────────────────


app = Flask(__name__)
app.secret_key = 'érase una vez un secreto muy secreto'  # Cambia esto por algo seguro en producción

# ─────────────────────────────────────────
#  Conexión a Oracle
# ─────────────────────────────────────────
#def get_db():
  #  dsn = f"{HOST}:{PUERTO}/{SERVICIO}"
  #  return oracledb.connect(
   #     user=USUARIO,
  #      password=PASSWORD,
   #     dsn=dsn
   # )

# ─────────────────────────────────────────
#  Rutas de páginas
# ─────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tabla')
def tabla():
    if 'usuario' not in session:
        return redirect(url_for('index'))
    return render_template('tabla.html')

# ─────────────────────────────────────────
#  API: Login — busca el PIDM en Oracle
# ─────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    datos    = request.get_json()
    usuario  = datos.get('usuario', '').strip()
    password = datos.get('password', '').strip()

    # Validaciones básicas
    if not usuario or not password:
        return jsonify({"success": False, "mensaje": "Completa todos los campos"}), 400

    if not usuario.endswith('@udep.edu.pe'):
        return jsonify({"success": False, "mensaje": "Usa tu correo institucional (@udep.edu.pe)"}), 401

    if password != '654123':
        return jsonify({"success": False, "mensaje": "Contraseña incorrecta"}), 401

    # Buscar PIDM en Oracle con el correo ingresado
    try:
        dsn = f"{HOST}:{PUERTO}/{SERVICIO}"
        conn = oracledb.connect(
            user=USUARIO,
            password=PASSWORD,
            dsn=dsn
         )
        print("✅ Conexión exitosa!")
        print(f"   Versión Oracle: {conn.version}\n")
      # conn   = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAL.GOREMAL_PIDM FROM GENERAL.GOREMAL MAL WHERE MAL.GOREMAL_PREFERRED_IND = 'Y' AND MAL.GOREMAL_EMAIL_ADDRESS = :correo
        """, {"correo": usuario})

        fila = cursor.fetchone()
        cursor.close()
        conn.close()

        if not fila:
            return jsonify({"success": False, "mensaje": "Correo no encontrado en el sistema"}), 401

        pidm = fila[0]

        # Guardar en sesión
        session['usuario'] = usuario
        session['pidm']    = pidm

        return jsonify({"success": True, "mensaje": "Login exitoso", "pidm": pidm})

    except Exception as e:
        return jsonify({"success": False, "mensaje": f"Error de base de datos: {str(e)}"}), 500

# ─────────────────────────────────────────
#  API: Datos de sesión (para tabla.html)
# ─────────────────────────────────────────
@app.route('/api/sesion')
def sesion():
    if 'usuario' not in session:
        return jsonify({"success": False, "mensaje": "No autenticado"}), 401

    return jsonify({
        "success": True,
        "usuario": session['usuario'],
        "pidm":    session['pidm']
    })

# ─────────────────────────────────────────
#  API: Logout
# ─────────────────────────────────────────
@app.route('/api/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─────────────────────────────────────────
#  Arrancar servidor
# ─────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)