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
#  Consulta principal de alumnos asesorados
# ─────────────────────────────────────────
SQL_ALUMNOS = """
WITH ActiveProgram AS (
	SELECT *
	FROM (
	    SELECT
	    	PER.SPRIDEN_PIDM,
	        PER.SPRIDEN_ID,
	        PER.SPRIDEN_FIRST_NAME,
	        PER.SPRIDEN_LAST_NAME,
	        TSP.SGRSTSP_TERM_CODE_EFF,
	        TSP.SGRSTSP_KEY_SEQNO,
	        TSP.SGRSTSP_STSP_CODE,
	        ROW_NUMBER() OVER (PARTITION BY PER.SPRIDEN_ID, PER.SPRIDEN_PIDM, TSP.SGRSTSP_KEY_SEQNO ORDER BY TSP.SGRSTSP_TERM_CODE_EFF DESC) AS RN_AP
	    FROM SATURN.SGRSTSP TSP
	    INNER JOIN SATURN.SPRIDEN PER
	        ON TSP.SGRSTSP_PIDM = PER.SPRIDEN_PIDM
	        AND PER.SPRIDEN_ID IS NOT NULL
	        AND PER.SPRIDEN_CHANGE_IND IS NULL
	    INNER JOIN SATURN.SGBSTDN TDN
	    	ON TDN.SGBSTDN_PIDM = PER.SPRIDEN_PIDM
	    WHERE
	    	TSP.SGRSTSP_STSP_CODE = 'AS'
	    	AND PER.SPRIDEN_PIDM IN (
		    	SELECT DISTINCT
					ADVR.SGRADVR_PIDM 
				FROM SATURN.SGRADVR ADVR
				WHERE
					ADVR.SGRADVR_PRIM_IND = 'Y'
					AND ADVR.SGRADVR_ADVR_PIDM = :pidm
	    	)
	)
	WHERE RN_AP = 1
),
AlumnosActivos AS (
	SELECT
		MSN.SPRIDEN_PIDM,
	    MSN.SPRIDEN_ID,
	    MSN.SPRIDEN_FIRST_NAME,
	    MSN.SPRIDEN_LAST_NAME,
	    MSN.SORLCUR_TERM_CODE_ADMIT,
	    MSN.SGRSTSP_KEY_SEQNO,
	    MSN.SORLCUR_PROGRAM,
	    MSN.SORLCUR_CAMP_CODE,
	    MSN.SORLCUR_SEQNO
	FROM (
		SELECT
			MSN.*,
		    ROW_NUMBER() OVER (PARTITION BY MSN.SPRIDEN_ID, MSN.SORLCUR_PROGRAM, MSN.SORLCUR_CAMP_CODE ORDER BY MSN.SORLCUR_SEQNO DESC) AS RN_PER
		FROM (
		    SELECT
	            AP.SPRIDEN_PIDM,
	            AP.SPRIDEN_ID,
	            AP.SPRIDEN_FIRST_NAME,
	            AP.SPRIDEN_LAST_NAME,
	            AP.SGRSTSP_KEY_SEQNO,
		        LCUR.SORLCUR_TERM_CODE_ADMIT,
		        LCUR.SORLCUR_PROGRAM,
		        LCUR.SORLCUR_CAMP_CODE,
		        LCUR.SORLCUR_LEVL_CODE,
		        LCUR.SORLCUR_SEQNO,
		        ROW_NUMBER() OVER (PARTITION BY AP.SPRIDEN_ID, AP.SPRIDEN_PIDM, AP.SGRSTSP_KEY_SEQNO ORDER BY LCUR.SORLCUR_SEQNO DESC) AS RN
		    FROM ActiveProgram AP
		    INNER JOIN SATURN.SORLCUR LCUR
		        ON AP.SPRIDEN_PIDM = LCUR.SORLCUR_PIDM
		        AND AP.SGRSTSP_KEY_SEQNO = LCUR.SORLCUR_KEY_SEQNO
		        AND LCUR.SORLCUR_ROLL_IND = 'Y'
	    ) MSN
	    WHERE
	    	RN = 1
	    	AND MSN.SORLCUR_LEVL_CODE IN ('PR', 'PP')
	) MSN
	WHERE
		RN_PER = 1
),
CicloActual AS (
	SELECT *
	FROM(
		SELECT
			NSP.SFRENSP_PIDM,
			NSP.SFRENSP_TERM_CODE,
			NSP.SFRENSP_KEY_SEQNO,
			NSP.CICLO_ACTUAL_1,
			NSP.ORDEN_MERITO_1,
			NSP.TOTAL_MERITO_1,
			NSP.DATOS_MERITO_1,
			ROW_NUMBER() OVER(PARTITION BY NSP.SFRENSP_PIDM, NSP.SFRENSP_KEY_SEQNO ORDER BY SFRENSP_TERM_CODE DESC) AS RN_NSP
		FROM SFRENSP_ADD NSP
	) NSP
	WHERE NSP.RN_NSP = 1
),
BecaActual AS (
	SELECT *
	FROM(
		SELECT
			NSP.SFRENSP_PIDM,
			NSP.SFRENSP_TERM_CODE,
			NSP.SFRENSP_KEY_SEQNO,
			NSP.CICLO_ACTUAL_1,
			NSP.ORDEN_MERITO_1,
			NSP.TOTAL_MERITO_1,
			NSP.DATOS_MERITO_1,
			ROW_NUMBER() OVER(PARTITION BY NSP.SFRENSP_PIDM, NSP.SFRENSP_KEY_SEQNO ORDER BY SFRENSP_TERM_CODE DESC) AS RN_NSP
		FROM SFRENSP_ADD NSP
	) NSP
	WHERE NSP.RN_NSP = 1
)
SELECT
	AAS.*,
	NSP.SFRENSP_TERM_CODE AS ULTIMO_PERIODO_SFRENSP,
	NSP.SFRENSP_KEY_SEQNO AS KEY_SEQNO,
	NSP.CICLO_ACTUAL_1 AS CICLO_ACTUAL,
	NSP.DATOS_MERITO_1 AS ATRIBUTO_ALUMNO
FROM AlumnosActivos AAS
INNER JOIN CicloActual NSP
	ON NSP.SFRENSP_PIDM = AAS.SPRIDEN_PIDM
	AND NSP.SFRENSP_KEY_SEQNO = AAS.SGRSTSP_KEY_SEQNO
"""

SQL_PIDM = """
SELECT
	MAL.GOREMAL_PIDM,
	BIO.SPBPERS_LEGAL_NAME
FROM GENERAL.GOREMAL MAL
INNER JOIN SATURN.SPBPERS BIO 
    ON BIO.SPBPERS_PIDM = MAL.GOREMAL_PIDM
WHERE
	MAL.GOREMAL_PREFERRED_IND = 'Y'
	AND MAL.GOREMAL_EMAIL_ADDRESS = :correo
"""


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
        cursor.execute(SQL_PIDM, {"correo": usuario})

        fila = cursor.fetchone()
        cursor.close()
        conn.close()

        if not fila:
            return jsonify({"success": False, "mensaje": "Correo no encontrado en el sistema"}), 401

        pidm = fila[0]
        name = fila[1]

        # Guardar en sesión
        session['usuario'] = usuario
        session['pidm']    = pidm
        session['name']    = name

        return jsonify({"success": True, "mensaje": "Login exitoso", "pidm": pidm})

    except Exception as e:
        return jsonify({"success": False, "mensaje": f"Error de base de datos: {str(e)}"}), 500


# ─────────────────────────────────────────
#  API: Lista de alumnos asesorados
# ─────────────────────────────────────────
@app.route('/api/alumnos')
def alumnos():
    if 'usuario' not in session:
        return jsonify({"success": False, "mensaje": "No autenticado"}), 401

    try:
        dsn = f"{HOST}:{PUERTO}/{SERVICIO}"
        conn = oracledb.connect(user=USUARIO, password=PASSWORD, dsn=dsn)
        cursor = conn.cursor()
        cursor.execute(SQL_ALUMNOS, {"pidm": session['pidm']})

        columnas = [col[0] for col in cursor.description]
        filas    = cursor.fetchall()
        cursor.close()
        conn.close()

        datos = [dict(zip(columnas, fila)) for fila in filas]
        return jsonify({"success": True, "columnas": columnas, "datos": datos, "total": len(datos)})

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
        "pidm":    session['pidm'],
        "name":    session['name']

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
    app.run(host='0.0.0.0', port=5000)