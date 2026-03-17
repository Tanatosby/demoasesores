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
WITH FiltroAsesorados AS (		-- DE AQUI SE DEBEN OBTENER TODOS LOS SGRADVR_PIDM, QUE SON LOS PIDM DE LOS ALUMNOS ASESORADOS DEL DOCENTE, EN LISTA_PIDM
	SELECT DISTINCT /*+ MATERIALIZE */
		ADVR.SGRADVR_PIDM
--		ADVR.*
	FROM SATURN.SGRADVR ADVR
	WHERE
		ADVR.SGRADVR_PRIM_IND = 'Y'
		AND ADVR.SGRADVR_ADVR_PIDM = :pidm
),
AlumnosActivos AS (
	SELECT /*+ MATERIALIZE */
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
--			ROW_NUMBER() OVER (PARTITION BY MSN.SPRIDEN_ID, MSN.SPRIDEN_PIDM/*, MSN.SORLCUR_CAMP_CODE*/ ORDER BY MSN.SORLCUR_PROGRAM DESC) AS RN_PROG,
		    ROW_NUMBER() OVER (PARTITION BY MSN.SPRIDEN_ID, /*MSN.SPRIDEN_PIDM,*/ MSN.SORLCUR_PROGRAM, MSN.SORLCUR_CAMP_CODE ORDER BY MSN.SORLCUR_SEQNO DESC) AS RN_PER
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
		        ROW_NUMBER() OVER (PARTITION BY AP.SPRIDEN_ID, AP.SPRIDEN_PIDM, AP.SGRSTSP_KEY_SEQNO ORDER BY LCUR.SORLCUR_SEQNO DESC) AS RN -- COMENTAR EL DESC PARA OBTENER EL PERIODO DE ADMISION REAL DEL ESTUDIANTE (PERO SE PIERDEN ALGUNOS REGISTROS PARA CASOS DONDE NO INICIA EN PR)
		    FROM (
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
				    INNER JOIN FiltroAsesorados FAS
				    	ON FAS.SGRADVR_PIDM = TSP.SGRSTSP_PIDM
				    INNER JOIN SATURN.SPRIDEN PER
				        ON TSP.SGRSTSP_PIDM = PER.SPRIDEN_PIDM
				        AND PER.SPRIDEN_ID IS NOT NULL
				        AND PER.SPRIDEN_CHANGE_IND IS NULL
			--	    INNER JOIN SATURN.SGBSTDN TDN
			--	    	ON TDN.SGBSTDN_PIDM = PER.SPRIDEN_PIDM
				    WHERE
				    	TSP.SGRSTSP_STSP_CODE = 'AS'
				    	AND EXISTS (
							SELECT 1 
						    FROM SATURN.SGBSTDN TDN
						    WHERE
						    	TDN.SGBSTDN_PIDM = PER.SPRIDEN_PIDM
						    	AND TDN.SGBSTDN_STST_CODE = 'AS'
						)
				)
				WHERE RN_AP = 1
		    ) AP
		    INNER JOIN SATURN.SORLCUR LCUR
		        ON AP.SPRIDEN_PIDM = LCUR.SORLCUR_PIDM
		        AND AP.SGRSTSP_KEY_SEQNO = LCUR.SORLCUR_KEY_SEQNO
		        AND LCUR.SORLCUR_ROLL_IND = 'Y'
		        AND LCUR.SORLCUR_LMOD_CODE = 'LEARNER'
--		        AND LCUR.SORLCUR_CACT_CODE = 'ACTIVE'
	    ) MSN
	    WHERE
	    	RN = 1
	    	AND MSN.SORLCUR_LEVL_CODE IN ('PR', 'PP')
	) MSN
	WHERE
		RN_PER = 1
--		AND RN_PROG != 1  -- DESCOMENTAR PARA VER A AQUELLOS CON MÁS DE UNA CARRERA
),
UltimoCAPP AS (
	SELECT
		QCM.SMRRQCM_PIDM,
		QCM.SMRRQCM_REQUEST_NO,
		QCM.SMRRQCM_PROGRAM
	FROM (
		SELECT
			QCM.SMRRQCM_PIDM,
			QCM.SMRRQCM_REQUEST_NO,
			QCM.SMRRQCM_PROGRAM,
			ROW_NUMBER () OVER (PARTITION BY QCM.SMRRQCM_PIDM, QCM.SMRRQCM_PROGRAM ORDER BY QCM.SMRRQCM_REQUEST_NO DESC) AS RN_QCM
		FROM SATURN.SMRRQCM QCM
		) QCM
	INNER JOIN FiltroAsesorados FAS
		ON FAS.SGRADVR_PIDM = QCM.SMRRQCM_PIDM
	WHERE
		QCM.RN_QCM = 1
),
CicloActual AS (
	SELECT *
	FROM(
		SELECT
			NSP.SFRENSP_PIDM,
			NSP.SFRENSP_TERM_CODE,
			NSP.SFRENSP_KEY_SEQNO,
			NSP.CICLO_ACTUAL_1,
			CEIL(NSP.CICLO_ACTUAL_1/2) AS NIVEL_ACTUAL,
--			NSP.ORDEN_MERITO_1,
--			NSP.TOTAL_MERITO_1,
			ROW_NUMBER() OVER(PARTITION BY NSP.SFRENSP_PIDM, NSP.SFRENSP_KEY_SEQNO ORDER BY SFRENSP_TERM_CODE DESC) AS RN_NSP
		FROM SFRENSP_ADD NSP
		INNER JOIN FiltroAsesorados FAS
			ON FAS.SGRADVR_PIDM = NSP.SFRENSP_PIDM
	) NSP
	WHERE NSP.RN_NSP = 1
),
BecaActual AS (							-- CAMBIAR NOMBRE A LA CTE
	SELECT *
	FROM (
		SELECT
			ATT.SGRSATT_PIDM,
			ATT.SGRSATT_TERM_CODE_EFF,
			ATT.SGRSATT_STSP_KEY_SEQUENCE,
			MAX(CASE WHEN ATT.SGRSATT_ATTS_CODE NOT IN ('TSUP', 'QSUP', 'SREN', 'DSUP', 'PROB', 'AEXT', 'AUDP', 'AUED', 'PREP') THEN ATT.SGRSATT_ATTS_CODE END) AS BECAS,
			MAX(CASE WHEN ATT.SGRSATT_ATTS_CODE IN ('TSUP', 'QSUP', 'SREN', 'DSUP') THEN ATT.SGRSATT_ATTS_CODE END) AS REND_ACAD,
			MAX(CASE WHEN ATT.SGRSATT_ATTS_CODE = 'PROB' THEN ATT.SGRSATT_ATTS_CODE END) AS PRONABEC,
			MAX(CASE WHEN ATT.SGRSATT_ATTS_CODE IN ('AEXT', 'AUDP', 'AUED') THEN ATT.SGRSATT_ATTS_CODE END) AS ATRIBUTOS_CONTABLES,
			MAX(CASE WHEN ATT.SGRSATT_ATTS_CODE = 'PREP' THEN ATT.SGRSATT_ATTS_CODE END) AS PRE_SELECCIONADO_PRONABEC,
			ROW_NUMBER() OVER(PARTITION BY ATT.SGRSATT_PIDM, ATT.SGRSATT_STSP_KEY_SEQUENCE ORDER BY ATT.SGRSATT_TERM_CODE_EFF DESC) AS RN_ATT
		FROM SATURN.SGRSATT ATT
		INNER JOIN FiltroAsesorados FAS
			ON FAS.SGRADVR_PIDM = ATT.SGRSATT_PIDM
		GROUP BY
		    ATT.SGRSATT_PIDM,
		    ATT.SGRSATT_TERM_CODE_EFF,
		    ATT.SGRSATT_STSP_KEY_SEQUENCE
	) ATT
	WHERE ATT.RN_ATT = 1
),
EmailAlumnos AS (
	SELECT
		MAL.GOREMAL_PIDM,
		LISTAGG(MAL.GOREMAL_EMAIL_ADDRESS || ' || ' || VMAL.GTVEMAL_DESC || ' || ' || CASE WHEN MAL.GOREMAL_PREFERRED_IND = 'Y' THEN 'PREFERIDO' ELSE 'OTROS' END, ' // ') WITHIN GROUP (ORDER BY MAL.GOREMAL_PREFERRED_IND DESC, MAL.GOREMAL_EMAIL_ADDRESS) AS CORREO	
	FROM GENERAL.GOREMAL MAL
	INNER JOIN FiltroAsesorados FAS
		ON FAS.SGRADVR_PIDM = MAL.GOREMAL_PIDM
	INNER JOIN GENERAL.GTVEMAL VMAL
		ON VMAL.GTVEMAL_CODE = MAL.GOREMAL_EMAL_CODE
	WHERE
		MAL.GOREMAL_STATUS_IND = 'A'
	GROUP BY
		MAL.GOREMAL_PIDM
),
TelefonoAlumnos AS (
	SELECT
		TEL.SPRTELE_PIDM,
		LISTAGG(TEL.SPRTELE_PHONE_NUMBER || ' || ' || VTEL.STVTELE_DESC || ' || ' || CASE WHEN TEL.SPRTELE_PRIMARY_IND = 'Y' THEN 'PRIMARIO' ELSE 'OTROS' END, ' // ') WITHIN GROUP (ORDER BY TEL.SPRTELE_PRIMARY_IND, VTEL.STVTELE_DESC) AS TELEFONO
	FROM (
		SELECT
			TEL.SPRTELE_PIDM,
			TEL.SPRTELE_SEQNO,
			TEL.SPRTELE_PHONE_NUMBER,
			TEL.SPRTELE_TELE_CODE,
			TEL.SPRTELE_PRIMARY_IND
		FROM (
			SELECT
				TEL.SPRTELE_PIDM,
				TEL.SPRTELE_SEQNO,
				TEL.SPRTELE_PHONE_NUMBER,
				TEL.SPRTELE_TELE_CODE,
				TEL.SPRTELE_PRIMARY_IND,
				ROW_NUMBER() OVER(PARTITION BY TEL.SPRTELE_PIDM, TEL.SPRTELE_PHONE_NUMBER, TEL.SPRTELE_TELE_CODE ORDER BY TEL.SPRTELE_SEQNO DESC) AS RN_TEL
			FROM SATURN.SPRTELE TEL
			WHERE
				TEL.SPRTELE_STATUS_IND IS NULL
	--			AND TEL.SPRTELE_PRIMARY_IND = 'Y'
		) TEL
		WHERE TEL.RN_TEL = 1
	) TEL
	INNER JOIN FiltroAsesorados FAS
		ON FAS.SGRADVR_PIDM = TEL.SPRTELE_PIDM 
	INNER JOIN SATURN.STVTELE VTEL
		ON VTEL.STVTELE_CODE = TEL.SPRTELE_TELE_CODE
	GROUP BY
		TEL.SPRTELE_PIDM 
)
SELECT
	AAS.*,
	QCM.SMRRQCM_REQUEST_NO AS REQ_NO,
	NSP.SFRENSP_TERM_CODE AS ULTIMO_PERIODO_SFRENSP,
	NSP.SFRENSP_KEY_SEQNO AS KEY_SEQNO,
	PGAG.SZRPGAG_PGAG AS PROMEDIO,
	NSP.CICLO_ACTUAL_1 AS CICLO_ACTUAL,
	NSP.NIVEL_ACTUAL,
	BAC.SGRSATT_TERM_CODE_EFF AS PERIODO_SGRSATT,
	BAC.BECAS,
	BAC.REND_ACAD,
	BAC.PRONABEC,
	BAC.ATRIBUTOS_CONTABLES,
	BAC.PRE_SELECCIONADO_PRONABEC,
	EAS.CORREO,
	TAS.TELEFONO
--	NSP.SFRENSP_TERM_CODE AS TERM_CODE_CICLO,
FROM AlumnosActivos AAS
INNER JOIN CicloActual NSP
	ON NSP.SFRENSP_PIDM = AAS.SPRIDEN_PIDM
	AND NSP.SFRENSP_KEY_SEQNO = AAS.SGRSTSP_KEY_SEQNO
LEFT JOIN UltimoCAPP QCM
	ON QCM.SMRRQCM_PIDM = AAS.SPRIDEN_PIDM
	AND QCM.SMRRQCM_PROGRAM = AAS.SORLCUR_PROGRAM
LEFT JOIN SATURN.SZRPGAG PGAG
	ON QCM.SMRRQCM_PIDM = PGAG.SZRPGAG_PIDM 
	AND QCM.SMRRQCM_REQUEST_NO = PGAG.SZRPGAG_REQUEST_NO 
LEFT JOIN BecaActual BAC
	ON BAC.SGRSATT_PIDM = AAS.SPRIDEN_PIDM
	AND BAC.SGRSATT_STSP_KEY_SEQUENCE = AAS.SGRSTSP_KEY_SEQNO
LEFT JOIN EmailAlumnos EAS
	ON EAS.GOREMAL_PIDM = AAS.SPRIDEN_PIDM
LEFT JOIN TelefonoAlumnos TAS
	ON TAS.SPRTELE_PIDM = AAS.SPRIDEN_PIDM
ORDER BY
	AAS.SPRIDEN_LAST_NAME,
	AAS.SPRIDEN_FIRST_NAME
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