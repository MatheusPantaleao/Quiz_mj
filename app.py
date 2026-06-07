import streamlit as st
import base64
import pandas as pd
import time
import os
import altair as alt

from database.conexao import criar_banco
from controllers.quiz_controller import (
    carregar_perguntas, 
    registrar_jogador,
    verificar_login,
    salvar_pontuacao, 
    obter_ranking,
    registrar_erro_pergunta,
    obter_erros_frequentes
)

criar_banco()

# 2. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Michael Jackson Quiz", page_icon="👑", layout="centered")

# 3. FUNÇÃO DA IMAGEM DE FUNDO
def configurar_imagem_de_fundo(nome_imagem):
    caminho = f"assets/{nome_imagem}"
    
    if not os.path.exists(caminho):
        return
        
    try:
        with open(caminho, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        css = f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), url("data:image/jpeg;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{
            background-color: transparent !important;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    except Exception as e:
        pass

configurar_imagem_de_fundo("fundo_mj.jpg.jpeg")


# 4: Acessibilidade (Barra Lateral)
with st.sidebar:
    st.header("⚙️ Definições")
    st.session_state.mutado = st.toggle("🔇 Silenciar Áudio", value=False)
    st.info("Desative os sons se estiver num ambiente partilhado.")

def tocar_som_oculto(nome_arquivo):
    if st.session_state.mutado:
        return 
        
    caminho = f"assets/{nome_arquivo}"
    try:
        with open(caminho, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay="true" style="display:none;">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def resetar_jogo():
    st.session_state.etapa = "escolha"
    st.session_state.finalizado = False
    st.session_state.som_tocado = False
    st.session_state.perguntas_atuais = []
    st.session_state.respostas_usuario = {}
    st.session_state.pergunta_atual_idx = 0
    st.session_state.acertos_finais = 0
    st.session_state.pontos_ganhos = 0

# FUNÇÃO PARA A TABELA DE RANKING 
def exibir_tabela_ranking_bonita(dados_ranking):
    """Gera uma tabela formatada visualmente para o Dashboard e para o Jogador"""
    df_rank = pd.DataFrame(dados_ranking)
    df_rank = df_rank.sort_values(by=["Pontuação Total", "Tempo Total (s)"], ascending=[False, True]).reset_index(drop=True)
    df_rank.index = df_rank.index + 1
    
    st.dataframe(
        df_rank,
        use_container_width=True,
        column_config={
            "Jogador": st.column_config.TextColumn(
                "Jogador",
                width="medium"
            ),
            "Pontuação Total": st.column_config.NumberColumn(
                "Pontos",
                help="Pontuação total acumulada pelo jogador",
                format="%d pts"
            ),
            "Tempo Total (s)": st.column_config.NumberColumn(
                "⏱Tempo",
                help="Tempo total (usado como critério de desempate)",
                format="%d s"
            ),
            "Partidas Jogadas": st.column_config.NumberColumn(
                "Partidas",
                format="%d"
            )
        }
    )

# GERENCIAMENTO DE ESTADOS GLOBAIS
if "etapa" not in st.session_state: st.session_state.etapa = "login"
if "nome_usuario" not in st.session_state: st.session_state.nome_usuario = ""
if "finalizado" not in st.session_state: st.session_state.finalizado = False
if "som_tocado" not in st.session_state: st.session_state.som_tocado = False
if "perguntas_atuais" not in st.session_state: st.session_state.perguntas_atuais = []
if "pergunta_atual_idx" not in st.session_state: st.session_state.pergunta_atual_idx = 0
if "respostas_usuario" not in st.session_state: st.session_state.respostas_usuario = {}
if "tempo_inicio" not in st.session_state: st.session_state.tempo_inicio = 0 
if "tempo_gasto" not in st.session_state: st.session_state.tempo_gasto = 0   

# ECRÃS DA APLICAÇÃO
def tela_login():
    st.title("Rei do Pop - Quiz")
    st.markdown("Bem-vindo ao derradeiro desafio sobre **Michael Jackson**!")
    st.divider()
    
    aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
    
    with aba_login:
        st.subheader("Login")
        nome_login = st.text_input("usuario:", key="login_nome").strip()
        senha_login = st.text_input("Senha:", type="password", key="login_senha")
        
        if st.button("Entrar", use_container_width=True, type="primary"):
            if not nome_login or not senha_login:
                st.error("Preencha todos os campos!")
            elif nome_login.lower() in ["admin", "professor", "root"]:
                st.session_state.nome_usuario = "Professor(a)"
                st.session_state.etapa = "admin"
                st.rerun()
            else:
                sucesso, mensagem = verificar_login(nome_login, senha_login)
                if sucesso:
                    st.session_state.nome_usuario = nome_login
                    st.session_state.etapa = "escolha"
                    st.rerun()
                else:
                    st.error(mensagem)

    with aba_cadastro:
        st.subheader("Crie uma nova conta")
        nome_cad = st.text_input("Escolha um usuario:", key="cad_nome").strip()
        senha_cad = st.text_input("Crie uma Senha:", type="password", key="cad_senha")
        senha_conf = st.text_input("Confirme a Senha:", type="password", key="cad_conf")
        
        if st.button("Registar ✅", use_container_width=True):
            if not nome_cad or not senha_cad:
                st.warning("Preencha todos os campos!")
            elif senha_cad != senha_conf:
                st.error("As senhas não coincidem!")
            else:
                sucesso, mensagem = registrar_jogador(nome_cad, senha_cad)
                if sucesso:
                    st.success(f"{mensagem} Já pode fazer login na aba 'Entrar'!")
                else:
                    st.error(mensagem)

def tela_admin():
    st.title("Painel de Controle Admin")
    
    dados_ranking = obter_ranking()
    
    if not dados_ranking:
        st.warning("Sem dados registados.")
        if st.button("Sair", use_container_width=True):
            resetar_jogo()
            st.session_state.etapa = "login"
            st.rerun()
        return

    df = pd.DataFrame(dados_ranking)
    
    st.subheader("Visão Geral da Turma")
    col1, col2, col3 = st.columns(3)
    col1.metric("Alunos", len(df))
    col2.metric("Partidas", df["Partidas Jogadas"].sum())
    col3.metric("Tempo Médio (s)", round(df["Tempo Total (s)"].mean(), 1))
    
    st.divider()
    
    st.subheader("Tabela de Classificação")
    exibir_tabela_ranking_bonita(dados_ranking)
    
    st.divider()
    
    # TABELAS
    st.subheader("Questões Mais Erradas")
    dados_erros = obter_erros_frequentes()
    if dados_erros:
        df_erros = pd.DataFrame(dados_erros)
        
        grafico_horizontal = alt.Chart(df_erros).mark_bar(color='#FF4B4B').encode(
            x=alt.X('Erros:Q', title='Número de Erros', axis=alt.Axis(tickMinStep=1)),
            y=alt.Y('Pergunta:N', title='', sort='-x'), 
            tooltip=['Pergunta', 'Erros']
        ).properties(height=350)
        
        st.altair_chart(grafico_horizontal, use_container_width=True)
        

        
    else:
        st.info("A turma está fantástica! Nenhum erro registado ainda.")
        
    st.divider()
    
    st.subheader("💾 Exportar Resultados")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=" baixar arquivo (CSV)",
        data=csv,
        file_name='tabela_turma.csv',
        mime='text/csv',
        type="primary",
        use_container_width=True
    )
    
    st.write("")
    if st.button("Sair do Painel Admin", use_container_width=True):
        resetar_jogo()
        st.session_state.etapa = "login"
        st.rerun()

def tela_escolha():
    st.title("Painel do Jogador")
    st.subheader(f"Olá, {st.session_state.nome_usuario}!")
    
    aba1, aba2, aba3 = st.tabs(["Jogar", "Meu Perfil", "Ranking Global"])
    
    with aba1:
        st.markdown("### Selecione o desafio")
        niv = st.select_slider("Nível:", options=["Fácil", "Médio", "Difícil"])
        
        st.write("")
        if st.button("Iniciar Partida!", use_container_width=True, type="primary"):
            st.session_state.niv = niv
            st.session_state.perguntas_atuais = carregar_perguntas(niv)
            
            st.session_state.tempo_inicio = time.time()
            st.session_state.pergunta_atual_idx = 0
            st.session_state.respostas_usuario = {}
            st.session_state.etapa = "quiz"
            st.session_state.som_tocado = False
            st.rerun()
            
    with aba2:
        st.markdown("### As Suas Estatísticas")
        dados_ranking = obter_ranking()
        dados_usuario = next((item for item in dados_ranking if item["Jogador"] == st.session_state.nome_usuario), None)
        
        if dados_usuario:
            col1, col2, col3 = st.columns(3)
            col1.metric("Pontos", dados_usuario["Pontuação Total"])
            col2.metric("Partidas", dados_usuario["Partidas Jogadas"])
            col3.metric("Tempo (s)", dados_usuario["Tempo Total (s)"])
            
    with aba3:
        st.markdown("### Top Jogadores")
        dados_ranking = obter_ranking()
        if dados_ranking:
            exibir_tabela_ranking_bonita(dados_ranking)
            
    st.divider()
    if st.button("Sair da Conta"):
        resetar_jogo()
        st.session_state.etapa = "login"
        st.session_state.nome_usuario = ""
        st.rerun()

def tela_quiz():
    if not st.session_state.perguntas_atuais:
        st.error("Sem perguntas disponíveis. Verifique o nível escolhido.")
        if st.button("Voltar"):
            resetar_jogo()
            st.rerun()
        return

    if st.session_state.pergunta_atual_idx == 0 and not st.session_state.som_tocado:
        tocar_som_oculto("hee-hee_tTMj1yC.mp3")
        st.session_state.som_tocado = True
        
    total_perguntas = len(st.session_state.perguntas_atuais)
    idx = st.session_state.pergunta_atual_idx
    
    progresso = (idx + 1) / total_perguntas
    st.progress(progresso, text=f"Questão {idx + 1} de {total_perguntas}")
    st.divider()
    
    p_dict = st.session_state.perguntas_atuais[idx]
    st.markdown(f"### {p_dict['pergunta']}")
    
    opcoes = [p_dict['opcao_a'], p_dict['opcao_b'], p_dict['opcao_c']]
    
    resposta_salva = st.session_state.respostas_usuario.get(idx, None)
    index_resposta = opcoes.index(resposta_salva) if resposta_salva in opcoes else None
    
    resposta = st.radio("Sua resposta:", opcoes, index=index_resposta, key=f"q_{idx}")
    
    st.write("") 
    col1, col2 = st.columns(2)
    
    with col1:
        if idx > 0:
            if st.button("⬅️ Anterior", use_container_width=True):
                st.session_state.respostas_usuario[idx] = resposta
                st.session_state.pergunta_atual_idx -= 1
                st.rerun()
                
    with col2:
        if idx < total_perguntas - 1:
            if st.button("Próxima ➡️", type="primary", use_container_width=True):
                if resposta is None:
                    st.warning("Selecione uma resposta!")
                else:
                    st.session_state.respostas_usuario[idx] = resposta
                    st.session_state.pergunta_atual_idx += 1
                    st.rerun()
        else:
            if st.button("Finalizar Quiz", type="primary", use_container_width=True):
                if resposta is None:
                    st.warning("Selecione uma resposta para finalizar!")
                else:
                    st.session_state.respostas_usuario[idx] = resposta
                    st.session_state.tempo_gasto = time.time() - st.session_state.tempo_inicio
                    st.session_state.etapa = "resultado"
                    st.rerun()

def tela_resultado():
    if not st.session_state.finalizado:
        acertos = 0
        
        for i, p_dict in enumerate(st.session_state.perguntas_atuais):
            if st.session_state.respostas_usuario.get(i) == p_dict['correta']:
                acertos += 1
            else:
                registrar_erro_pergunta(p_dict['pergunta'])
                
        pesos = {"Fácil": 1, "Médio": 2, "Difícil": 3}
        peso = pesos.get(st.session_state.niv, 1)
        pontos_ganhos = acertos * peso
        
        salvar_pontuacao(st.session_state.nome_usuario, pontos_ganhos, st.session_state.tempo_gasto)
        
        st.session_state.acertos_finais = acertos
        st.session_state.pontos_ganhos = pontos_ganhos
        st.session_state.finalizado = True

    st.markdown("## Resultados da Partida")
    acertos = st.session_state.acertos_finais
    pontos = st.session_state.pontos_ganhos
    tempo = int(st.session_state.tempo_gasto)
    total_perguntas = len(st.session_state.perguntas_atuais)
    
    st.info(f"Tempo de conclusão: **{tempo} segundos**")
    st.divider()
    
    for i, p_dict in enumerate(st.session_state.perguntas_atuais):
        resp_dada = st.session_state.respostas_usuario.get(i)
        correta = p_dict['correta']
        
        if resp_dada == correta:
            st.success(f"**Q{i+1}:** {p_dict['pergunta']}  \n*(Resposta: {resp_dada} ✅)*")
        else:
            st.error(f"**Q{i+1}:** {p_dict['pergunta']}  \n*(A sua resposta: {resp_dada} ❌ | Correta: {correta})*")

    st.divider()

    col_vazia1, col_gif, col_vazia2 = st.columns([1, 2, 1])
    
    if acertos == total_perguntas:
        st.success(f"**Perfeito!** {acertos}/{total_perguntas}. Ganhou {pontos} pontos.")
        with col_gif:
            st.image("assets/Mj_kiss.gif", use_container_width=True) 
        tocar_som_oculto("me-chama-de-lord.mp3") 
        
    elif acertos >= (total_perguntas // 2):
        st.info(f"**Muito bom!** {acertos}/{total_perguntas}. Ganhou {pontos} pontos.")
        with col_gif:
            st.image("assets/Mj_speed.gif", use_container_width=True) 
        tocar_som_oculto("Mj_.mp3")
        
    else:
        st.warning(f"**Foi quase...** {acertos}/{total_perguntas}. Tente novamente!")
        with col_gif:
            st.image("assets/MJ_zumbi.gif", use_container_width=True) 
        tocar_som_oculto("not-my-problema-michael-jackson.mp3") 
        
    st.write("")
    if st.button("Voltar ao Painel", type="primary", use_container_width=True):
        resetar_jogo()
        st.rerun()

# ESTADOS DO STREAMLIT
if st.session_state.etapa == "login":
    tela_login()
elif st.session_state.etapa == "escolha":
    tela_escolha()
elif st.session_state.etapa == "quiz":
    tela_quiz()
elif st.session_state.etapa == "resultado":
    tela_resultado()
elif st.session_state.etapa == "admin":
    tela_admin()