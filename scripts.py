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

    try:
        # Armar DSN
        dsn = f"{HOST}:{PUERTO}/{SERVICIO}"
        print(f"\n🔌 Conectando a: {dsn}")
        print(f"   Usuario: {USUARIO}\n")

        # Conectar
        conexion = oracledb.connect(
            user=USUARIO,
            password=PASSWORD,
            dsn=dsn
        )

        print("✅ Conexión exitosa!")
        print(f"   Versión Oracle: {conexion.version}\n")

        # Ejecutar consulta de prueba
        cursor = conexion.cursor()
        print("📋 Ejecutando: SELECT * FROM SPRIDEN...")
        print("-" * 50)

        cursor.execute("SELECT * FROM SPRIDEN FETCH FIRST 5 ROWS ONLY")

        # Mostrar nombres de columnas
        columnas = [col[0] for col in cursor.description]
        print(" | ".join(columnas))
        print("-" * 50)

        # Mostrar filas
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
        print("   - Que tu Oracle Client esté en el PATH")

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


if __name__ == "__main__":
    test_conexion()