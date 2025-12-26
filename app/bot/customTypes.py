from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, ConfigDict

class State(TypedDict):
    messages: Annotated[list[str], add_messages]


class ImovelConsiderado(BaseModel):
    """Modelo para representar um imóvel considerado na avaliação (BaseListing)."""
    numero_amostra: Optional[int] = Field(None, alias="sample_number", description="Número da amostra")
    endereco: Optional[str] = Field(None, alias="address", description="Endereço do imóvel")
    bairro: Optional[str] = Field(None, alias="neighborhood", description="Bairro do imóvel")
    cidade: Optional[str] = Field(None, alias="city", description="Cidade do imóvel")
    estado: Optional[str] = Field(None, alias="state", description="Estado do imóvel")
    link: Optional[str] = Field(None, alias="url", description="Link do anúncio do imóvel")
    area: Optional[float] = Field(None, description="Área do imóvel em m²")
    quartos: int = Field(0, alias="bedrooms", description="Quantidade de quartos")
    banheiros: int = Field(0, alias="bathrooms", description="Quantidade de banheiros")
    vagas: int = Field(0, alias="parking_spaces", description="Quantidade de vagas de garagem")
    valor_aluguel: Optional[float] = Field(None, alias="rent_value", description="Valor do aluguel ou preço do imóvel")
    valor_condominio: Optional[float] = Field(None, alias="condo_fee", description="Valor do condomínio")
    tipo: Optional[str] = Field(None, alias="type", description="Tipo do imóvel (Apartamento, Casa, etc)")
    finalidade: Optional[str] = Field(None, alias="purpose", description="Finalidade (Residencial, Comercial)")

    model_config = ConfigDict(populate_by_name=True, extra="allow")

class SalvarAvaliacaoInput(BaseModel):
    """Modelo de entrada para salvar a avaliação no banco de dados (Evaluation)."""
    endereco: str = Field(..., alias="address", description="Endereço completo do imóvel avaliado")
    bairro: str = Field(..., alias="neighborhood", description="Bairro do imóvel")
    cidade: str = Field(..., alias="city", description="Cidade do imóvel")
    estado: str = Field(..., alias="state", description="Estado do imóvel")
    area: float = Field(..., description="Área do imóvel em m²")
    quartos: int = Field(0, alias="bedrooms", description="Quantidade de quartos")
    banheiros: int = Field(0, alias="bathrooms", description="Quantidade de banheiros")
    vagas: int = Field(0, alias="parking_spaces", description="Quantidade de vagas de garagem")
    description: Optional[str] = Field(None, description="Descrição da avaliação")
    classification: Optional[str] = Field(None, alias="classificacao", description="Classificação (Venda/Aluguel)")
    purpose: Optional[str] = Field(None, alias="finalidade", description="Finalidade (Residencial/Comercial)")
    property_type: Optional[str] = Field(None, alias="tipo_imovel", description="Tipo do imóvel (Apartamento, Casa, etc)")
    valor_regiao_m2: Optional[float] = Field(None, alias="region_value_sqm", description="Valor médio do m² na região")
    tipo_analise: str = Field("region", alias="analysis_type", description="Tipo de análise (region ou street)")
    nome_proprietario: Optional[str] = Field(None, alias="owner_name", description="Nome do proprietário")
    nome_avaliador: Optional[str] = Field(None, alias="appraiser_name", description="Nome do avaliador")
    preco_estimado: Optional[float] = Field(None, alias="estimated_price", description="Preço estimado do imóvel")
    preco_arredondado: Optional[float] = Field(None, alias="rounded_price", description="Preço estimado arredondado")
    imoveis_considerados: List[ImovelConsiderado] = Field(default_factory=list, alias="base_listings", description="Lista de imóveis base")

    model_config = ConfigDict(populate_by_name=True, extra="allow")
