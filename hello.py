# Importações de bibliotecas e ferramentas necessárias
import os
from threading import Thread
from flask import Flask, render_template, session, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import requests
from datetime import datetime

# Lê o ficheiro .env para carregar variáveis de ambiente de forma segura
from dotenv import load_dotenv
load_dotenv()

# Define o diretório base da aplicação
basedir = os.path.abspath(os.path.dirname(__file__))

# Inicialização da aplicação Flask e configurações básicas
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações da API do Mailgun resgatadas das variáveis de ambiente
app.config['API_KEY'] = os.environ.get('API_KEY')
app.config['API_URL'] = os.environ.get('API_URL')
app.config['API_FROM'] = os.environ.get('API_FROM')

# Configurações auxiliares de e-mail e administradores
app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_MAIL_SENDER'] = 'b.hiandra@aluno.ifsp.edu.br'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')

# Inicialização das extensões do Flask
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelo de Dados para os Cargos (Roles) dos usuários no banco de dados
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

# Modelo de Dados para os Utilizadores/Usuários cadastrados
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username

# Função responsável por disparar o e-mail utilizando a API HTTP do Mailgun
def send_simple_message(to, subject, html_content):
    print('Enviando mensagem (POST)...', flush=True)
    
    # Se 'to' for uma lista, converte para uma string separada por vírgulas (exigido pelo Mailgun)
    if isinstance(to, list):
        to_address = ", ".join(to)
    else:
        to_address = to

    try:
        resposta = requests.post(app.config['API_URL'], 
                               auth=("api", app.config['API_KEY']), 
                               data={"from": app.config['API_FROM'], 
                                     "to": to_address, 
                                     "subject": app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject, 
                                     "html": html_content})
            
        print('Enviando mensagem (Resposta)...' + str(resposta) + ' - ' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), flush=True)
        return resposta
    except Exception as e:
        print('ERRO AO ENVIAR E-MAIL: ' + str(e), flush=True)
        raise e

# Definição do formulário de cadastro utilizando Flask-WTF
class NameForm(FlaskForm):
    name = StringField('Qual é o seu nome?', validators=[DataRequired()])
    role = SelectField('Qual é o seu cargo?', choices=[
        ('Usuário', 'Usuário'), 
        ('Moderador', 'Moderador'), 
        ('Administrador', 'Administrador')
    ])
    email = BooleanField('Deseja enviar e-mail para b.hiandra@aluno.ifsp.edu.br?')
    submit = SubmitField('Enviar')
    
# Contexto de shell para facilitar testes e manipulação via linha de comando
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)

# Tratamento personalizado para a página não encontrada (Erro 404)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Tratamento personalizado para erro interno do servidor (Erro 500)
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Rota principal da aplicação (lida com visualização e submissão do formulário)
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    
    # Valida se o formulário foi enviado corretamente
    if form.validate_on_submit():
        old_name = session.get('name')
        nome = form.name.data
        role_selecionada = form.role.data
        
        # Verifica se o nome mudou na sessão ignorando maiúsculas/minúsculas
        if old_name is not None and old_name.lower() != nome.strip().lower():
            session['known'] = False
        else:
            session['known'] = True
            
        session['name'] = nome.strip()

        # Procura a role escolhida no banco, se não existir, cria
        user_role = Role.query.filter_by(name=role_selecionada).first()
        if not user_role:
            user_role = Role(name=role_selecionada)
            db.session.add(user_role)
            db.session.commit()

        # Normaliza o nome para minúsculas e remove espaços para evitar duplicados
        nome_tratado = nome.strip()
        usuario_existente = User.query.filter(db.func.lower(User.username) == nome_tratado.lower()).first()
        
        # Variáveis para controlar o envio do e-mail e o tipo de ação
        is_new_user = False
        is_role_updated = False

        if not usuario_existente:
            # Caso 1: Utilizador novo
            user = User(username=nome_tratado, role=user_role)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            is_new_user = True
        else:
            # Caso 2: Utilizador já existe, verifica se alterou o cargo
            if usuario_existente.role != user_role:
                usuario_existente.role = user_role
                db.session.commit()
                is_role_updated = True
            session['known'] = True
            user = usuario_existente

        # Se for um novo utilizador OU houver atualização de cargo, dispara o e-mail (caso o admin esteja configurado)
        if (is_new_user or is_role_updated) and app.config['FLASKY_ADMIN']:
            print('Enviando mensagem...', flush=True)
            destinatarios = [app.config['FLASKY_ADMIN']]
            
            # Adiciona o e-mail pessoal se a caixa de seleção do formulário estiver marcada
            if form.email.data == True:
                destinatarios.append("b.hiandra@aluno.ifsp.edu.br")
                
            # Define o assunto com base na ação executada
            assunto = 'Novo usuário cadastrado' if is_new_user else 'Atualização de cargo de usuário'
            
            # Renderiza o template unificado passando o utilizador e a flag de novo utilizador
            html_mensagem = render_template('mail/user.html', user=user, is_new=is_new_user)
            
            # Dispara a função que envia a mensagem e exibe o status
            send_simple_message(destinatarios, assunto, html_mensagem)
            print('Mensagem enviada...', flush=True)
            
        return redirect(url_for('index'))
        
    # Consultas para listagens e contadores atualizadas para a view
    user_all = User.query.all()
    roles = Role.query.all()

    # Renderiza a página HTML principal passando os dados necessários
    return render_template('index.html', 
                           form=form, 
                           name=session.get('name'),
                           known=session.get('known', False), 
                           usuarios=user_all,
                           user_count=len(user_all),
                           roles=roles,
                           role_count=len(roles),
                           moment_time=datetime.utcnow())