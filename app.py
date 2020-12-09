from flask import Flask, render_template

app = Flask(__name__)


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/main-menu')
def menu():
    return render_template('main-menu.html')


if __name__ == '__main__':
    app.run(debug=True)
