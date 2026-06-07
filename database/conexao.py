from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine('sqlite:///banco.db', echo=False)

Base = declarative_base()

SessionLocal = sessionmaker(bind=engine)

def criar_banco():
    """Cria todas as tabelas na base de dados, se ainda não existirem."""
    Base.metadata.create_all(engine)