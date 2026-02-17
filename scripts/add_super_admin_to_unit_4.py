"""
Script para adicionar o super admin à unidade 4
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
from app.models.unit import Unit

def add_super_admin_to_unit_4():
    app = create_app()
    
    with app.app_context():
        # Buscar super admin
        super_admin = User.query.filter_by(email='hermesbarbosa9@gmail.com').first()
        if not super_admin:
            print("❌ Super admin não encontrado!")
            return
        
        # Buscar unidade 4
        unit_4 = Unit.query.get(4)
        if not unit_4:
            print("❌ Unidade 4 não encontrada!")
            return
        
        print(f"Super admin: {super_admin.email} (ID: {super_admin.id})")
        print(f"Unidade: {unit_4.name} (ID: {unit_4.id})")
        print("-" * 60)
        
        # Verificar se já é membro
        is_member = super_admin.units.filter_by(id=4).first() is not None
        
        if is_member:
            print(f"✓ Super admin já é membro da unidade {unit_4.name}")
        else:
            print(f"→ Adicionando super admin à unidade {unit_4.name}...")
            unit_4.add_user(super_admin, role='admin')
            db.session.commit()
            print("✅ Super admin adicionado com sucesso!")
        
        # Definir como unidade ativa se não tiver
        if super_admin.active_unit_id != 4:
            print(f"\n→ Definindo unidade 4 como ativa para o super admin...")
            super_admin.active_unit_id = 4
            db.session.commit()
            print("✅ Unidade ativa atualizada!")
        else:
            print(f"\n✓ Unidade 4 já é a unidade ativa")

if __name__ == "__main__":
    add_super_admin_to_unit_4()
