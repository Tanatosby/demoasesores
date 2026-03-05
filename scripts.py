# ============================================================
#  test_conexion_oracle.py
#  Prueba de conexión a Oracle 19c + consulta básica
# ============================================================
#
#  INSTALACIÓN (ejecuta esto en tu terminal una sola vez):
#  pip install oracledb
#
# ============================================================

import oracledb
import os
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

def test_conexion():
    print("=" * 50)
    print("  PRUEBA DE CONEXIÓN A ORACLE 19c")
    print("=" * 50)

    # Verificar que todas las variables están cargadas
    faltantes = [nombre for nombre, valor in {
        "DB_USUARIO": USUARIO, "DB_PASSWORD": PASSWORD,
        "DB_HOST": HOST, "DB_SERVICIO": SERVICIO
    }.items() if not valor]

    if faltantes:
        print(f"\n❌ Faltan variables en tu .env: {', '.join(faltantes)}")
        return

    try:
        dsn = f"{HOST}:{PUERTO}/{SERVICIO}"
        print(f"\n🔌 Conectando a: {dsn}")
        print(f"   Usuario: {USUARIO}\n")

        conexion = oracledb.connect(
            user=USUARIO,
            password=PASSWORD,
            dsn=dsn
        )

        print("✅ Conexión exitosa!")
        print(f"   Versión Oracle: {conexion.version}\n")

        cursor = conexion.cursor()
        print("📋 Ejecutando: SELECT * FROM SPRIDEN...")
        print("-" * 50)

        cursor.execute("SELECT * FROM SPRIDEN FETCH FIRST 5 ROWS ONLY")

        columnas = [col[0] for col in cursor.description]
        print(" | ".join(columnas))
        print("-" * 50)

        filas = cursor.fetchall()
        if filas:
            for fila in filas:
                print(" | ".join(str(valor) for valor in fila))
            print(f"\n✅ Se obtuvieron {len(filas)} filas correctamente.")
        else:
            print("⚠️  La consulta no devolvió filas.")

        cursor.close()
        conexion.close()
        print("\n🔒 Conexión cerrada correctamente.")

    except oracledb.DatabaseError as e:
        error, = e.args
        print(f"\n❌ Error de base de datos:")
        print(f"   Código:  {error.code}")
        print(f"   Mensaje: {error.message}")
        print("\n💡 Revisa:")
        print("   - Usuario y contraseña correctos")
        print("   - HOST, PUERTO y SERVICIO correctos")
        print("   - Ruta del Oracle Client en init_oracle_client()")

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("💡 Si el error menciona 'init_oracle_client', agrega la ruta")
        print("   de tu Oracle Client en la línea correspondiente del script.")

if __name__ == "__main__":
    test_conexion()