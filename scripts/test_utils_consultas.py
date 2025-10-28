'''
Script simple para probar las funciones de src/server/consultas/utils_consultas.py.
- Requiere asyncpg instalado y la base de datos accesible.
- Configurar DATABASE_URL en el entorno o editar la URL por defecto.
'''
import os
import sys
import asyncio
from pathlib import Path
from datetime import date

# añadir 'src' al path para poder importar server.consultas.utils_consultas
repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

import asyncpg
from server.consultas import utils_consultas as utils  # importa el módulo a probar

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/demo_obrasocial")

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        print("=== prueba periodo_window (función sin BD) ===")
        desde, hasta = utils.periodo_window(date(2025,10,15), "mensual")
        print("periodo_window mensual:", desde, hasta)
        desde_anual, hasta_anual = utils.periodo_window(date(2025,5,15), "anual")
        print("periodo_window anual:", desde_anual, hasta_anual)

        print("\n=== prueba get_plan_id_by_afiliado ===")
        af_id = 45  # ajustar según datos en la BD
        plan_id = await utils.get_plan_id_by_afiliado(conn, af_id)
        print(f"plan_id para afiliado {af_id} ->", plan_id)

        print("\n=== prueba practica_cubierta ===")
        practica_id = 2  # ajustar según datos en la BD
        info = await utils.practica_cubierta(conn, af_id, practica_id)
        print("practica_cubierta:", info)

        print("\n=== prueba tope_practica_disponible (una práctica específica) ===")
        tope = await utils.tope_practica_disponible(conn, af_id, practica_id, date.today(), "mensual")
        print("tope_practica_disponible:", tope)

        print("\n=== prueba historial_consumos ===")
        hist = await utils.historial_consumos(conn, af_id, limit=5, offset=0)
        print("historial_consumos (5 registros):", hist)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())