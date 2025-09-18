import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_connection():
    """
    Crea y retorna una conexión a PostgreSQL usando credenciales del .env
    """
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        return connection
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None
