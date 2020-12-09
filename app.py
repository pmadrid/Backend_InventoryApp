from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = "mischiefManaged"

@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')


@app.route('/main-menu')
def menu():
    return render_template('main-menu.html')


@app.route('/crear-usuario')
def crear_usuario():
    return render_template('CrearUsuario.html')


@app.route('/mod-usuario')
def mod_usuario():
    return render_template('modificarUsuario.html')


@app.route('/lista')
def lista():
    return render_template('lista-productos.html')


@app.route('/buscar-producto')
def buscar_producto():
    return render_template('busca-producto.html')


@app.route('/producto')
def producto():
    return render_template('pagina-unitaria-producto.html')


if __name__ == '__main__':
    app.run(debug=True)
