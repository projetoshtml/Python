from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Subscription
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'chave-secreta-super-segura'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///saas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

app = create_app()

@app.before_first_request
def create_tables():
    db.create_all()
    # Criar conta admin inicial (opcional)
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@saas.com', password='admin123')
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # Em produção, use hash!
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Assinatura do usuário
    sub = current_user.subscription
    plan = sub.plan if sub else 'free'
    return render_template('dashboard.html', plan=plan)

@app.route('/subscribe/<plan>')
@login_required
def subscribe(plan):
    valid_plans = ['free', 'basic', 'premium']
    if plan not in valid_plans:
        flash('Plano inválido.', 'error')
        return redirect(url_for('dashboard'))

    sub = current_user.subscription
    if sub:
        sub.plan = plan
    else:
        sub = Subscription(plan=plan, user_id=current_user.id)
        db.session.add(sub)
    db.session.commit()
    flash(f'Você agora está no plano {plan}.', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)