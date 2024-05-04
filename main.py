from flask import Flask
from flask import render_template, request, jsonify, session, redirect, url_for, abort, g, make_response, flash
from DataBase import DataBase
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

# configuration
DATABASE = "/templates/flsite.db"
DEBUG = True
SECRET_KEY = "O1I3Uoiub4d5ioU1Bi5odb"

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, "flsite.db")))

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"


@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDB(user_id, dbase)


def connect_db():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource("sq_db.sql", mode="r") as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    if not hasattr(g, "link_db"):
        g.link_db = connect_db()
    return g.link_db


dbase = None


@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = DataBase(db)


@app.route('/')
def index():
    return render_template('Front_Page.html')


@app.route('/register', methods=['GET', 'POST'])
def registration():
    if request.method == "POST":
        session.pop('_flashes', None)
        if len(request.form['name']) > 4 and len(request.form['email']) > 4 \
                and len(request.form['password']) > 4 and request.form['password'] == request.form['repassword']:
            hash = generate_password_hash(request.form['password'])
            res = dbase.addUser(request.form['name'], request.form['email'], hash)
            if res:
                flash("Вы успешно зарегистрированы", "success")
                return redirect(url_for('login'))
            else:
                flash("Данная почта уже зарегестрирована", "error")
        else:
            flash("Неверно заполнены поля", "error")
    return render_template('registration.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user = dbase.getUserByEmail(request.form['email'])
        if user and check_password_hash(user['password'], request.form['password']):
            userlogin = UserLogin().create(user)
            login_user(userlogin, remember=True)
            return redirect(url_for('profile'))
        flash("Неверный логин/пароль", "error")
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))

@app.route('/prom')
def prom():
    return render_template('prom.html')


@app.route('/profile')
@login_required
def profile():
    flash(f"""Ваш id:{current_user.get_id()}""")
    return render_template('profile.html')
                # user info: {current_user.get_id()}"""


@app.errorhandler(404)
def pageNotFound(error):
    return render_template('error.html'), 404


@app.teardown_appcontext
def close_db(error):
    # разрываем соедние с бд, есло оно было установлено
    if hasattr(g, "link_db"):
        g.link_db.close()


if __name__ == "__main__":
    app.run(debug=True)  # add debug mode
