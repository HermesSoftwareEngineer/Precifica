from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class State(TypedDict):
    messages: Annotated[list[str], add_messages]


class ImovelConsiderado(BaseModel):
    """Modelo para representar um imóvel considerado na avaliação (BaseListing)."""
    endereco: Optional[str] = Field(None, description="Endereço do imóvel")
    bairro: Optional[str] = Field(None, description="Bairro do imóvel")
    cidade: Optional[str] = Field(None, description="Cidade do imóvel")
    estado: Optional[str] = Field(None, description="Estado do imóvel")
    link: Optional[str] = Field(None, description="Link do anúncio do imóvel")
    area: Optional[float] = Field(None, description="Área do imóvel em m²")
    quartos: int = Field(0, description="Quantidade de quartos")
    banheiros: int = Field(0, description="Quantidade de banheiros")
    vagas: int = Field(0, description="Quantidade de vagas de garagem")
    valor_aluguel: Optional[float] = Field(None, description="Valor do aluguel")
    valor_condominio: Optional[float] = Field(None, description="Valor do condomínio")
    tipo: Optional[str] = Field(None, description="Tipo do imóvel (Apartamento, Casa, etc)")
    finalidade: Optional[str] = Field(None, description="Finalidade (Residencial, Comercial)")

class SalvarAvaliacaoInput(BaseModel):
    """Modelo de entrada para salvar a avaliação no banco de dados (Evaluation)."""
    endereco: str = Field(..., description="Endereço completo do imóvel avaliado")
    bairro: str = Field(..., description="Bairro do imóvel")
    cidade: str = Field(..., description="Cidade do imóvel")
    estado: str = Field(..., description="Estado do imóvel")
    area: float = Field(..., description="Área do imóvel em m²")
    quartos: int = Field(0, description="Quantidade de quartos")
    banheiros: int = Field(0, description="Quantidade de banheiros")
    vagas: int = Field(0, description="Quantidade de vagas de garagem")
    description: Optional[str] = Field(None, description="Descrição da avaliação")
    classification: Optional[str] = Field(None, description="Classificação (Venda/Aluguel)")
    purpose: Optional[str] = Field(None, description="Finalidade (Residencial/Comercial)")
    property_type: Optional[str] = Field(None, description="Tipo do imóvel (Apartamento, Casa, etc)")
    valor_regiao_m2: Optional[float] = Field(None, description="Valor médio do m² na região")
    tipo_analise: str = Field("region", description="Tipo de análise (region ou street)")
    nome_proprietario: Optional[str] = Field(None, description="Nome do proprietário")
    nome_avaliador: Optional[str] = Field(None, description="Nome do avaliador")
    preco_estimado: Optional[float] = Field(None, description="Preço estimado do imóvel")
    preco_arredondado: Optional[float] = Field(None, description="Preço estimado arredondado")
    imoveis_considerados: List[ImovelConsiderado] = Field(default_factory=list, description="Lista de imóveis base")
