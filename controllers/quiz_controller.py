import pandas as pd
import random
import hashlib
from database.conexao import SessionLocal
from database.models import Jogador, EstatisticaPergunta

# SEGURANÇA
def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# LÓGICA DAS PERGUNTAS
def carregar_perguntas(nivel):
    try:
        df = pd.read_csv("data/perguntas.csv")
        df_filtrado = df[df['nivel'] == nivel]
        perguntas = df_filtrado.to_dict('records')
        random.shuffle(perguntas)
        return perguntas[:5] 
    except FileNotFoundError:
        return []

# LÓGICA DO BANCO DE DADOS (SQLALCHEMY)
def registrar_jogador(nome, senha):
    session = SessionLocal()
    try:
        jogador_existente = session.query(Jogador).filter_by(nome=nome).first()
        if jogador_existente:
            return False, "Este nome de usuario já existe!"
        novo_jogador = Jogador(nome=nome, senha=gerar_hash(senha))
        session.add(novo_jogador)
        session.commit()
        return True, "Conta criada com sucesso!"
    finally:
        session.close()

def verificar_login(nome, senha):
    session = SessionLocal()
    try:
        jogador = session.query(Jogador).filter_by(nome=nome).first()
        if not jogador:
            return False, "usuario não encontrado!"
        if jogador.senha != gerar_hash(senha):
            return False, "Senha incorreta!"
        return True, "Login bem-sucedido!"
    finally:
        session.close()

def salvar_pontuacao(nome, pontos, tempo_gasto):
    """Atualizada para receber e guardar o tempo gasto (Feature 1)"""
    session = SessionLocal()
    try:
        jogador = session.query(Jogador).filter_by(nome=nome).first()
        if jogador:
            jogador.partidas_jogadas += 1
            jogador.pontuacao_total += pontos
            jogador.tempo_total_segundos += int(tempo_gasto)
            session.commit()
    finally:
        session.close()

def registrar_erro_pergunta(pergunta_texto):
    """Regista no Analytics qual a pergunta que o aluno errou (Feature 3)"""
    session = SessionLocal()
    try:
        estatistica = session.query(EstatisticaPergunta).filter_by(pergunta_texto=pergunta_texto).first()
        if estatistica:
            estatistica.vezes_errada += 1
        else:
            nova_estatistica = EstatisticaPergunta(pergunta_texto=pergunta_texto, vezes_errada=1)
            session.add(nova_estatistica)
        session.commit()
    finally:
        session.close()

def obter_ranking():
    session = SessionLocal()
    try:
        jogadores = session.query(Jogador).order_by(Jogador.pontuacao_total.desc()).all()
        ranking = [
            {
                "Jogador": j.nome, 
                "Pontuação Total": j.pontuacao_total, 
                "Partidas Jogadas": j.partidas_jogadas,
                "Tempo Total (s)": j.tempo_total_segundos
            } 
            for j in jogadores
        ]
        return ranking
    finally:
        session.close()

def obter_erros_frequentes():
    """Retorna os dados de erros para o painel de Admin."""
    session = SessionLocal()
    try:
        erros = session.query(EstatisticaPergunta).order_by(EstatisticaPergunta.vezes_errada.desc()).all()
        return [{"Pergunta": e.pergunta_texto, "Erros": e.vezes_errada} for e in erros]
    finally:
        session.close()