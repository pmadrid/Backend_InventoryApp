import sqlite3
from flask import Flask, json, render_template, request, flash, jsonify, redirect, session, g, url_for
from werkzeug.wrappers import CommonRequestDescriptorsMixin
from wtforms import form
from formulario import Login, convertToBinaryData, writeTofile
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
ROL = 0


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
                    ROL = rol_id
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
            return render_template(CREARUSUARIO)
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
            identificacion = request.form['identificacion']
            username = request.form['username']
            password = request.form['password']
            email = request.form['user_email']
            delete_button = request.form.get('delete_button', None)

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
            
            if delete_button == 'pressed':
                borrar_usuario(int(identificacion))
                return redirect(url_for('mod_usuario'))

            if not utils.isUsernameValid(username):
                error = "El usuario debe ser alfanumérico"
                flash(error)
                return redirect(url_for('mod_usuario'))

            if not utils.isEmailValid(email):
                error = 'Correo inválido'
                flash(error)
                return redirect(url_for('mod_usuario'))

            if not utils.isPasswordValid(password):
                error = 'La contraseña debe tener por los menos 8 caractéres, una mayúsccula y una mínuscula'
                flash(error)
                return redirect(url_for('mod_usuario'))
            
            hash_password = generate_password_hash(password)
            
            db.execute(
                'UPDATE Usuarios SET nombre_usu=?, correo_usu=?, contraseña_usu=?, fecha_mod_usu=?, rol_usu_fk=? WHERE id_usu=?',
                (username, email, hash_password, datetime.datetime.now(), chck, identificacion))
            db.commit()
            
            serverEmail = yagmail.SMTP(EMAILSERVER, CONTRASEÑASERVER)
            serverEmail.send(to=email, subject='Modificacion Usuario',
                             contents='Bienvenido, han modificado tu informacion de usuario, tus credenciales nuevas son: \n Usuario: ' + username + '\n Contraseña: ' + password)
        
            flash('Revisa tu correo')
            return redirect(url_for('usuarios'))
        else:
            lista_usu = ['Id Usuario a Modificar', 'Nuevo Nombre Usuario', 'Nuevo Correo Usuario', 'Nuevo Password Usuario']
            return render_template(MODUSUARIO, data = lista_usu)

    except Exception as e:
        print("Ocurrió un error cuando intentaste modificar un usuario", e)
        return redirect(url_for('usuarios'))


def borrar_usuario(id):
    try:
        close_db()
        db = get_db()
        db.execute('DELETE FROM Usuarios WHERE id_usu=?',(id,))
        db.commit()
    except Exception as e:
        print("Hay un error cuando tratas de borrar un usuario ", e)

@app.route('/lista/', methods=['GET'])
@login_required
def lista():
    return render_template('lista-productos.html')

@app.route('/lista-usu/', methods=['GET'])
@login_required
def lista_usu():
    return render_template('lista-productos-usu.html')


@app.route('/buscar-producto/', methods=['GET'])
@login_required
def buscar_producto():
    return render_template('busca-producto.html')

@app.route('/buscar-producto-usu/', methods=['GET'])
@login_required
def buscar_producto_usu():
    return render_template('busca-producto-usu.html')



@app.route('/producto/')
@login_required
def producto():
    return render_template('pagina-unitaria-producto.html')

@app.route('/producto-usu/')
@login_required
def producto_usu():
    return render_template('pagina-unitaria-producto-usu.html')


@app.route('/lista-usuarios/')
@login_required
def usuarios():
    close_db()
    usuarios = get_db().execute('SELECT id_usu, nombre_usu, correo_usu, rol_usu_fk FROM Usuarios').fetchall()

    return render_template('GestionarUsuarios.html', data = usuarios)

@app.route('/lista-productos/')
@login_required
def productos():
    close_db()
    productos = get_db().execute('SELECT id_pro, nombre_pro, cantidad_pro, costo_pro, descripcion_pro, image_pro FROM Productos').fetchall()
    lista_productos = []
    for tupla in productos:
        lista_productos.append(list(tupla))
    for lista in lista_productos:
        if lista[5] is not None:
            path_img = 'static\\Images\\'+lista[1]+'.jpg'
            writeTofile(lista[5], path_img)
            lista[5] = '..\\' + path_img
    return render_template('GestionarProductos.html', data = lista_productos)

@app.route('/crear-producto/', methods=['GET', 'POST'])
@login_required
def crear_producto():
    try:
        if request.method == 'POST':
            product_name = request.form['productname']
            product_cant = request.form['productcant']
            product_cost = request.form['productcost']
            product_desc = request.form['productdesc']
            img = request.form['productimg']
            img_path = "static\\Images\\" + img
            product_img = convertToBinaryData(img_path)
            error = None

            close_db()
            db = get_db()

            if db.execute('SELECT id_pro FROM Productos WHERE nombre_pro = ?', (product_name,)).fetchone() is not None:
                error = "El correo ya existe"
                flash(error)
                return render_template('CrearProducto.html')

            db.execute(
                'INSERT INTO Productos (nombre_pro, cantidad_pro, costo_pro, descripcion_pro, image_pro) Values(?,?,?,?,?)',
                (product_name, product_cant, product_cost, product_desc, product_img))
            db.commit()

            return render_template('CrearProducto.html')
        else:
            return render_template('CrearProducto.html')
    except Exception as e:
        print("Ocurrió un error cuando intentaste crear un Producto", e)
        return render_template('CrearProducto.html')


@app.route('/mod-producto/', methods=['GET', 'POST'])
@login_required
def mod_producto():
    try:
        if request.method == 'POST':
            product_id = request.form['productid']
            product_name = request.form['productname']
            product_cant = request.form['productcant']
            product_cost = request.form['productcost']
            product_desc = request.form['productdesc']
            error = None

            close_db()
            db = get_db()
            delete_button = request.form.get('delete_button', None)

            if delete_button == 'pressed':
                borrar_producto(int(product_id))
                return redirect(url_for('mod_producto'))
            
            img = request.form['productimg']
            img_path = "static\\Images\\" + img
            product_img = convertToBinaryData(img_path)
            

            db.execute(
                'UPDATE Productos SET nombre_pro=?, cantidad_pro=?, costo_pro=?, descripcion_pro=?, image_pro=? WHERE id_pro=?',
                (product_name, product_cant, product_cost, product_desc, product_img, product_id))
            db.commit()
            
            return redirect(url_for('productos'))
        else:
            lista_prod = ['Id Producto a Modificar', 'Nuevo Nombre Producto', 'Nueva Cantidad Producto', 'Nueva Costo Producto', 'Nueva Descripción Producto', 'Nueva Imagen Producto']
            return render_template('modificarProducto.html', data = lista_prod)

    except Exception as e:
        print("Ocurrió un error cuando intentaste modificar un usuario", e)
        return redirect(url_for('productos'))


def borrar_producto(id):
    try:
        close_db()
        db = get_db()
        db.execute('DELETE FROM Productos WHERE id_pro=?',(id,))
        db.commit()
    except Exception as e:
        print("Hay un error cuando tratas de borrar un usuario ", e)

@app.route('/usuario-aut/', methods=['GET'])
@login_required
def usuario_aut():
    return render_template('UsuarioAutenticado.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=443, ssl_context=('micertificado.pem', 'llaveprivada.pem'))
