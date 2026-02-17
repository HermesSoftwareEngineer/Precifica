"""
Script para limpar active_unit_id de usuários que não são membros da unidade selecionada
"""
import sys
import os

# Adiciona o diretório raiz ao path
if '__file__' in globals():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
else:
    sys.path.insert(0, '.')

from app import create_app, db
from app.models.user import User

def clean_invalid_active_units():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Limpando active_unit_id inválidos...")
        print("=" * 60)
        
        # Buscar todos os usuários com active_unit_id definido
        users_with_active_unit = User.query.filter(User.active_unit_id.isnot(None)).all()
        
        print(f"\n📊 Total de usuários com unidade ativa: {len(users_with_active_unit)}")
        
        cleaned_count = 0
        
        for user in users_with_active_unit:
            # Verifica se o usuário é membro da unidade ativa
            is_member = user.units.filter_by(id=user.active_unit_id).first() is not None
            
            if not is_member:
                print(f"\n❌ Usuário {user.id} ({user.email}) tem active_unit_id={user.active_unit_id}")
                print(f"   mas NÃO é membro dessa unidade!")
                
                # Lista as unidades das quais o usuário é membro
                member_units = [u.id for u in user.units.all()]
                print(f"   Unidades válidas: {member_units if member_units else 'Nenhuma'}")
                
                # Limpa o active_unit_id
                user.active_unit_id = None
                cleaned_count += 1
                print(f"   ✓ active_unit_id limpo")
            else:
                print(f"✓ Usuário {user.id} ({user.email}) - active_unit_id={user.active_unit_id} OK")
        
        # Commit das mudanças
        if cleaned_count > 0:
            try:
                db.session.commit()
                print("\n" + "=" * 60)
                print("✅ Limpeza concluída com sucesso!")
                print("=" * 60)
                print(f"✓ {cleaned_count} usuário(s) com active_unit_id inválido foram corrigidos")
                print(f"✓ {len(users_with_active_unit) - cleaned_count} usuário(s) estavam OK")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Erro ao fazer commit: {e}")
                raise
        else:
            print("\n" + "=" * 60)
            print("✅ Nenhum problema encontrado!")
            print("=" * 60)
            print("Todos os usuários com active_unit_id são membros válidos")

if __name__ == "__main__":
    clean_invalid_active_units()
