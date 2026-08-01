import os
from flask import Flask,render_template,redirect,url_for,send_from_directory,request,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from werkzeug.security import generate_password_hash,check_password_hash

from flask_login import LoginManager,UserMixin,login_user,logout_user,login_required,current_user
login_manager = LoginManager()


class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] =os.environ.get('DB_KEY', 'sqlite:///users.db')
app.config["SECRET_KEY"]=os.environ.get('SECRET_KEY')

db.init_app(app)

login_manager.init_app(app)

class User(db.Model,UserMixin):
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str]=mapped_column(String(100),unique=True)
    password:Mapped[str]=mapped_column(String(100))


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User,user_id)

@app.route("/")
def home():
    return render_template('index.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        email=request.form['email']
        user=db.session.execute(db.select(User).where(User.email==email)).scalar()
        if user:
            flash('Email already exists .login instead')
            return redirect(url_for('login'))
        hashed_password=generate_password_hash(request.form['password'],method='pbkdf2:sha256',salt_length=8)

        user=User(
            email=request.form['email'],
            password=hashed_password,
            name=request.form['name']

        )

        db.session.add(user)
        db.session.commit()
        login_user(user)
        return render_template('secrets.html',name=user.name)
    return render_template('register.html')


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        user=db.session.execute(db.select(User).where(User.email==email)).scalar()
        if user:
            hash_password=check_password_hash(user.password,request.form['password'])
            if hash_password:
                login_user(user)
                return render_template('secrets.html')
            else:
                flash('Invalid username or password')

        flash('Email does not exist ')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



@app.route('/secrets')
@login_required
def secrets():
    return render_template('secrets.html',name=current_user.name)



@app.route('/download')
@login_required
def download():
    return send_from_directory(directory='static',path='files/cheat_sheet.pdf')
