# app.py
from flask import Flask
from models import db
from routes import bp  # Blueprint’i al

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(bp)   # Blueprint’i kayıt et

    with app.app_context():
        db.create_all()
    return app

# Flask CLI ve doğrudan python app.py ile çalışmak için
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
