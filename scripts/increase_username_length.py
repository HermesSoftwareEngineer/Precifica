"""
Script para aumentar o tamanho da coluna username de 20 para 100 caracteres
"""
import sys
import os

# Adiciona o diretório raiz ao path
if '__file__' in globals():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
else:
    sys.path.insert(0, '.')

from app import create_app, db
from sqlalchemy import text

def increase_username_length():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Aumentando tamanho da coluna username de 20 para 100")
        print("=" * 60)
        
        try:
            # Verifica o tamanho atual
            check_query = text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'username'
            """)
            
            result = db.session.execute(check_query).fetchone()
            current_length = result[0] if result else None
            
            print(f"\n📊 Tamanho atual da coluna username: {current_length} caracteres")
            
            if current_length == 100:
                print("✓ Coluna já está com 100 caracteres. Nada a fazer.")
                return
            
            # Altera o tamanho da coluna
            print("\n→ Alterando tamanho para 100 caracteres...")
            alter_query = text("""
                ALTER TABLE users 
                ALTER COLUMN username TYPE VARCHAR(100)
            """)
            
            db.session.execute(alter_query)
            db.session.commit()
            
            # Verifica novamente
            result = db.session.execute(check_query).fetchone()
            new_length = result[0] if result else None
            
            print(f"\n✅ Coluna alterada com sucesso!")
            print(f"✓ Novo tamanho: {new_length} caracteres")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao alterar coluna: {e}")
            raise

if __name__ == "__main__":
    increase_username_length()
