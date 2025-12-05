from langchain_core.tools import tool
from scraper import extract_content
from langgraph.prebuilt import ToolNode
from webSearch import web_search
import pandas as pd
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, Field
import os
import sqlite3
from database import init_db

@tool
def ler_conteudo_site(url: str):
    """
        Use essa ferramente para ler conteúdos de sites através de urls.
    """
    content = extract_content(url)
    return content

@tool
def pesquisar_sites(pesquisa: str):
    """
        Use essa ferramenta pra fazer pesquisas online.
    """
    cx = "f250cd15b14884f9f" 
    num_results=10
    results = web_search(pesquisa, num_results, cx)
    return results

@tool
def avaliar_imovel(prompt: str):
    """
        Essa ferramenta chama um agente de avaliação de imóveis. Adicionei no prompt o endereço do imóvel avaliado e a área em metros quadrados do imóvel.
    """

    return "Olá, mundo! Ferramenta em desenvolvimento..."

class ImovelConsiderado(BaseModel):
    """Modelo para representar um imóvel considerado na avaliação."""
    endereco: str = Field(description="Endereço do imóvel")
    link: str = Field(description="Link do anúncio do imóvel")
    area_m2: str = Field(description="Área do imóvel em metros quadrados")
    valor_total: str = Field(description="Valor total do imóvel")
    valor_m2: str = Field(description="Valor por metro quadrado")

class AvaliacaoInput(BaseModel):
    """Modelo de entrada para a exportação de avaliação."""
    endereco_imovel: str = Field(description="Endereço completo do imóvel avaliado")
    area_imovel: float = Field(description="Área do imóvel em metros quadrados")
    valor_medio_m2: float = Field(description="Valor médio do metro quadrado na região")
    preco_estimado: float = Field(description="Preço estimado do imóvel avaliado")
    imoveis_considerados: List[ImovelConsiderado] = Field(
        description="Lista de imóveis considerados na avaliação"
    )

@tool(args_schema=AvaliacaoInput)
def exportar_avaliacao_excel(
    endereco_imovel: str,
    area_imovel: float,
    valor_medio_m2: float,
    preco_estimado: float,
    imoveis_considerados: List[ImovelConsiderado]
):
    """
    Exporta o relatório de avaliação de imóvel para um arquivo Excel.
    
    Args:
        endereco_imovel: Endereço completo do imóvel avaliado
        area_imovel: Área do imóvel em metros quadrados
        valor_medio_m2: Valor médio do metro quadrado na região
        preco_estimado: Preço estimado do imóvel avaliado
        imoveis_considerados: Lista de imóveis considerados na avaliação
    
    Returns:
        Caminho do arquivo Excel gerado
    """
    try:
        # Converter objetos Pydantic para dicionários
        imoveis_dict = [
            {
                'endereco': imovel.endereco,
                'link': imovel.link,
                'area_m2': imovel.area_m2,
                'valor_total': imovel.valor_total,
                'valor_m2': imovel.valor_m2
            }
            for imovel in imoveis_considerados
        ]
        
        # Criar DataFrame com os imóveis considerados
        df_imoveis = pd.DataFrame(imoveis_dict)
        
        # Renomear colunas para português
        df_imoveis.columns = ['Endereço', 'Link', 'Área (m²)', 'Valor Total (R$)', 'Valor/m² (R$)']
        
        # Criar DataFrame com informações da avaliação
        df_resumo = pd.DataFrame({
            'Item': [
                'Endereço do Imóvel Avaliado',
                'Área do Imóvel (m²)',
                'Valor Médio do m² na Região (R$)',
                'Preço Estimado do Imóvel (R$)',
                'Quantidade de Imóveis Analisados',
                'Data da Avaliação'
            ],
            'Valor': [
                endereco_imovel,
                f"{area_imovel:.2f}",
                f"{valor_medio_m2:.2f}",
                f"{preco_estimado:.2f}",
                len(imoveis_considerados),
                datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            ]
        })
        
        # Criar diretório de relatórios se não existir
        relatorios_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'relatorios')
        os.makedirs(relatorios_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"avaliacao_imovel_{timestamp}.xlsx"
        caminho_arquivo = os.path.join(relatorios_dir, nome_arquivo)
        
        # Exportar para Excel com múltiplas abas
        with pd.ExcelWriter(caminho_arquivo, engine='openpyxl') as writer:
            df_resumo.to_excel(writer, sheet_name='Resumo da Avaliação', index=False)
            df_imoveis.to_excel(writer, sheet_name='Imóveis Considerados', index=False)
            
            # Ajustar largura das colunas
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return f"Relatório exportado com sucesso para: {caminho_arquivo}"
    
    except Exception as e:
        return f"Erro ao exportar relatório: {str(e)}"

class SalvarAvaliacaoInput(BaseModel):
    """Modelo de entrada para salvar a avaliação no banco de dados."""
    endereco_imovel: str = Field(description="Endereço completo do imóvel avaliado")
    area_imovel: float = Field(description="Área do imóvel em metros quadrados")
    valor_medio_m2: float = Field(description="Valor médio do metro quadrado na região")
    preco_estimado: float = Field(description="Preço estimado do imóvel avaliado")
    finalidade: str = Field(description="Finalidade da avaliação (ex: 'venda', 'aluguel')")
    imoveis_considerados: List[ImovelConsiderado] = Field(description="Lista de imóveis considerados na avaliação")

@tool(args_schema=SalvarAvaliacaoInput)
def salvar_avaliacao_db(
    endereco_imovel: str,
    area_imovel: float,
    valor_medio_m2: float,
    preco_estimado: float,
    finalidade: str,
    imoveis_considerados: List[ImovelConsiderado]
):
    """
    Salva os dados da avaliação e do imóvel em um banco de dados SQLite.
    """
    try:
        db_path = init_db()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se o imóvel já existe pelo endereço
        cursor.execute("SELECT id FROM imoveis_avaliados WHERE endereco = ?", (endereco_imovel,))
        result = cursor.fetchone()
        
        if result:
            imovel_id = result[0]
        else:
            cursor.execute(
                "INSERT INTO imoveis_avaliados (endereco, area_m2) VALUES (?, ?)",
                (endereco_imovel, area_imovel)
            )
            imovel_id = cursor.lastrowid
            
        # Insere a avaliação
        cursor.execute(
            """
            INSERT INTO avaliacoes (imovel_id, valor_medio_m2, preco_estimado, finalidade)
            VALUES (?, ?, ?, ?)
            """,
            (imovel_id, valor_medio_m2, preco_estimado, finalidade)
        )
        avaliacao_id = cursor.lastrowid

        # Insere os imóveis comparativos
        for imovel in imoveis_considerados:
            # Tratamento básico de valores numéricos que podem vir como string
            try:
                val_total = float(str(imovel.valor_total).replace('R$', '').replace('.', '').replace(',', '.').strip()) if isinstance(imovel.valor_total, str) else imovel.valor_total
            except:
                val_total = 0.0
                
            try:
                val_m2 = float(str(imovel.valor_m2).replace('R$', '').replace('.', '').replace(',', '.').strip()) if isinstance(imovel.valor_m2, str) else imovel.valor_m2
            except:
                val_m2 = 0.0

            try:
                area = float(str(imovel.area_m2).replace('m²', '').strip()) if isinstance(imovel.area_m2, str) else imovel.area_m2
            except:
                area = 0.0

            cursor.execute(
                """
                INSERT INTO imoveis_comparativos (avaliacao_id, endereco, link, area_m2, valor_total, valor_m2)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (avaliacao_id, imovel.endereco, imovel.link, area, val_total, val_m2)
            )
        
        conn.commit()
        conn.close()
        return f"Avaliação salva com sucesso no banco de dados (ID Avaliação: {avaliacao_id})."
        
    except Exception as e:
        return f"Erro ao salvar no banco de dados: {str(e)}"

toolsList = [ler_conteudo_site, pesquisar_sites, exportar_avaliacao_excel, salvar_avaliacao_db]
tools_node = ToolNode(toolsList)