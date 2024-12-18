from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, csv

# Inicialização do Flask
app = Flask(__name__)

# Configuração do Banco de Dados
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Diretório do projeto
DB_PATH = os.path.join(BASE_DIR, 'db', 'finance.db')  # Caminho absoluto para o banco
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret_key_here'

# Inicialização do SQLAlchemy e LoginManager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modelos do Banco de Dados
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # RECEITA ou DESPESA
    category = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, default=datetime.utcnow)

# Carregar usuário no login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Buscar usuário no banco
        user = User.query.filter_by(username=username).first()

        if user:
            # Comparar hash da senha
            if check_password_hash(user.password_hash, password):
                login_user(user)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Senha incorreta!', 'danger')
        else:
            flash('Usuário não encontrado!', 'danger')

    return render_template('login.html')

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        transaction = Transaction(
            user_id=current_user.id,
            type=request.form['type'],
            category=request.form['category'],
            value=float(request.form['value']),
            description=request.form['description'],
            date=request.form['date']
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transação adicionada!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_transaction.html')

@app.route('/export_csv')
@login_required
def export_csv():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    output = []
    for t in transactions:
        output.append([t.date, t.type, t.category, t.description, t.value])
    csv_data = "Data,Tipo,Categoria,Descrição,Valor\n"
    csv_data += "\n".join([",".join(map(str, row)) for row in output])
    response = Response(csv_data, mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=transacoes.csv"
    return response

@app.route('/dashboard')
@login_required
def dashboard():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', transactions=transactions)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema!', 'success')
    return redirect(url_for('login'))

# Inicializar banco de dados no início do programa
if not os.path.exists(os.path.join(BASE_DIR, 'db')):
    os.makedirs(os.path.join(BASE_DIR, 'db'), exist_ok=True)

with app.app_context():
    db.create_all()

# Executar o app
if __name__ == '__main__':
    app.run(debug=True)
