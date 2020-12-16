import sqlite3
from flask import Flask, json, render_template, request, flash, jsonify, redirect, session, g, url_for
from werkzeug.wrappers import CommonRequestDescriptorsMixin
from wtforms import form
from formulario import Login
import yagmail as yagmail
import os
import utils
from articulos import articulos
from Conexion import get_db, close_db
import datetime
import functools

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.urandom(24)

LOGIN = 'login.html'
CREARUSUARIO = 'CrearUsuario.html'
MODUSUARIO = 'modificarUsuario.html'
GESTIONARUSU = 'GestionarUsuarios.html'
USERNAME = ''
CONTRASEÑA = ''
EMAILSERVER = 'ejemplomisiontic@gmail.com'
CONTRASEÑASERVER = 'Maracuya1234'


@app.route('/api')
def api():
    return jsonify({"message": "¡Hola, mundo!"})


@app.route('/articulos')
@app.route('/articulos/<string:nom_articulo>')
def getArticulos(nom_articulo=None):
    if nom_articulo:
        encontrado = [articulo for articulo in articulos if articulo['nombre'] == nom_articulo]
        return jsonify({"articulo": encontrado[0]})
    else:
        return jsonify({"articulos": articulos, "message": "Listado de artículos"})


@app.route('/')
def home():
    formulario = Login()
    return render_template(LOGIN, titulo="Iniciar Sesión", form=formulario)


@app.route('/login/', methods=['POST', 'GET'])
def login():  # ESta función
    formulario = Login()
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            error = ""

            close_db()
            db = get_db()

            user = db.execute('SELECT * FROM usuarios WHERE nombre_usu=?', (username,)).fetchone()

            if user is None:
                error = "¡Usuario y/o Contraseña inválidos!"
            else:
                if check_password_hash(user[3], password):
                    session.clear()
                    session['user_id'] = user[0]
                    rol_id = user[6]
                    if rol_id == 1:
                        return redirect(url_for('menu'))
                    elif rol_id == 2:
                        return redirect(url_for('usuario_aut'))
            flash(error)
            return render_template(LOGIN, titulo="Iniciar Sesión", form=formulario)
        else:
            if g.user is None:
                return render_template(LOGIN, titulo="Iniciar Sesión", form=formulario)
            else:
                rol_id = g.user[6]
                if rol_id == 1:
                    return redirect(url_for('menu'))
                elif rol_id == 2:
                    return redirect(url_for('usuario_aut'))

    except Exception as e:
        print("Ocurrió un error cuando intentaste ingresar en login:", e)
        return render_template(LOGIN, titulo="Iniciar Sesión", form=formulario)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/login/#', methods=['POST'])
def recuperar():
    formulario = Login()
    try:
        if request.method == 'POST':
            email = request.form['email']
            serverEmail = yagmail.SMTP(EMAILSERVER, CONTRASEÑASERVER)
            serverEmail.send(to=email, subject='Recuperar contraseña',
                             contents='Bienvenido, usa este link para recuperar tu cuenta')
            flash('Revisa tu correo para recuperar tu cuenta')
            return render_template(LOGIN, titulo="Iniciar Sesión", form=formulario)
        else:
            return render_template(LOGIN, titulo="Iniciar Sesión", form=formulario)
    except Exception as e:
        print("Ocurrió un error cuando intentaste recuperar la contraseña", e)
        return render_template(LOGIN, titulo="Iniciar Sesión", form=formulario)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)

    return wrapped_view


@app.route('/main-menu/')
@login_required
def menu():
    return render_template('main-menu.html')


@app.before_request
def load_logged_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        close_db()
        g.user = get_db().execute('SELECT * FROM Usuarios WHERE id_usu=?', (user_id,)).fetchone()


@app.route('/crear-usuario/', methods=['GET', 'POST'])
@login_required
def crear_usuario():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['user_email']
            try:
                chck_admin = request.form['admin']
            except Exception as e:
                chck = 2

            try:
                chck_user = request.form['user']
            except Exception as e:
                chck = 1

            error = None

            close_db()
            db = get_db()

            if not utils.isUsernameValid(username):
                error = "El usuario debe ser alfanumérico"
                flash(error)
                return render_template(CREARUSUARIO)

            if not utils.isEmailValid(email):
                error = 'Correo inválido'
                flash(error)
                return render_template(CREARUSUARIO)

            if not utils.isPasswordValid(password):
                error = 'La contraseña debe tener por los menos 8 caractéres, una mayúsccula y una mínuscula'
                flash(error)
                return render_template(CREARUSUARIO)

            if db.execute('SELECT id_usu FROM Usuarios WHERE correo_usu = ?', (email,)).fetchone() is not None:
                error = "El correo ya existe"
                flash(error)
                return render_template('GestionarUsuarios.html')

            hash_password = generate_password_hash(password)

            db.execute(
                'INSERT INTO Usuarios (nombre_usu, correo_usu, contraseña_usu, fecha_crea_usu, rol_usu_fk) Values(?,?,?,?,?)',
                (username, email, hash_password, datetime.datetime.now(), chck))
            db.commit()

            serverEmail = yagmail.SMTP(EMAILSERVER, CONTRASEÑASERVER)

            serverEmail.send(to=email, subject='Activa tu cuenta',
                             contents='Bienvenido, usa este link para activar tu cuenta \n Recuerda tus credenciales: \n Usuario: ' + username + '\n Contraseña: ' + password)

            flash('Revisa tu correo para activar tu cuenta')
            return render_template(GESTIONARUSU)
        else:
            return render_template(CREARUSUARIO)
    except Exception as e:
        print("Ocurrió un error cuando intentaste crear un usuario", e)
        return render_template(CREARUSUARIO)


@app.route('/mod-usuario/', methods=['GET', 'POST'])
@login_required
def mod_usuario():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['user_email']
            error = None

            if not utils.isUsernameValid(username):
                error = "El usuario debe ser alfanumérico"
                flash(error)
                return render_template(MODUSUARIO)

            if not utils.isEmailValid(email):
                error = 'Correo inválido'
                flash(error)
                return render_template(MODUSUARIO)

            if not utils.isPasswordValid(password):
                error = 'La contraseña debe tener por los menos 8 caractéres, una mayúsccula y una mínuscula'
                flash(error)
                return render_template(MODUSUARIO)

            serverEmail = yagmail.SMTP(EMAILSERVER, CONTRASEÑASERVER)

            serverEmail.send(to=email, subject='Modificación Usuario',
                             contents='Bienvenido, han modificado tu información de usuario, tus credenciales nuevas son: \n Usuario: ' + username + '\n Contraseña: ' + password)

            flash('Revisa tu correo')
            return render_template(GESTIONARUSU)
        else:
            return render_template(MODUSUARIO)

    except Exception as e:
        print("Ocurrió un error cuando intentaste modificar un usuario", e)
        return render_template(CREARUSUARIO)


@app.route('/lista/', methods=['GET'])
@login_required
def lista():
    return render_template('lista-productos.html')


@app.route('/buscar-producto/', methods=['GET'])
@login_required
def buscar_producto():
    return render_template('busca-producto.html')


@app.route('/producto/')
@login_required
def producto():
    return render_template('pagina-unitaria-producto.html')


@app.route('/lista-usuarios/')
@login_required
def usuarios():
    return render_template('GestionarUsuarios.html')


@app.route('/usuario-aut/', methods=['GET'])
@login_required
def usuario_aut():
    return render_template('UsuarioAutenticado.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=443, ssl_context=('micertificado.pem', 'llaveprivada.pem'))
