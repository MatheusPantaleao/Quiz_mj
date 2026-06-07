from sqlalchemy import Column, Integer, String
from database.conexao import Base

class Jogador(Base):
    __tablename__ = 'jogadores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    pontuacao_total = Column(Integer, default=0)
    partidas_jogadas = Column(Integer, default=0)
    tempo_total_segundos = Column(Integer, default=0) 
    
    def __repr__(self):
        return f"<Jogador(nome={self.nome}, pontos={self.pontuacao_total})>"

class EstatisticaPergunta(Base):
    __tablename__ = 'estatisticas_perguntas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    pergunta_texto = Column(String, unique=True, nullable=False)
    vezes_errada = Column(Integer, default=0)