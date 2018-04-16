from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
import cgi

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(1000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'register']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/blog')
def index():
    users = User.query.all()
    blogs = Blog.query.all() #is this a list of objects
    blog_query = request.args.get('id')
    user_query = request.args.get('user')
    owners = [] #list of blog posters in order of the postings of their blog
    titles = []
    bodies = []
    ids = []
    user_list = []
    for blog in blogs:
        owner = User.query.filter_by(id = blog.owner_id).first()
        owners.append(owner.username)
        titles.append(blog.title)
        bodies.append(blog.body)
        ids.append(blog.id) 
    for user in users:
        user_list.append(user.username)

    if not blog_query and not user_query:
        return render_template('home.html', owners=owners, titles=titles, bodies=bodies, ids=ids, total_blogs=len(blogs), user_list=user_list)
    elif blog_query:
        return render_template('home.html', owners=[owners[(int(blog_query))-1]], titles=[titles[(int(blog_query))-1]],
         bodies=[bodies[(int(blog_query))-1]], ids=[ids[(int(blog_query))-1]], total_blogs=1, user_list=user_list)
    elif user_query:
        for blog in blogs:
            for user in users:
                if blog.owner_id == user.id:
                    if user.username != user_query:
                        owners.remove(user.username)
                        titles.remove(blog.title)
                        bodies.remove(blog.body)
                        ids.remove(blog.id)
                        total_blogs=len(titles)
        return render_template('home.html', owners=owners, titles=titles, bodies=bodies, ids=ids, total_blogs=total_blogs, user_list=user_list)

@app.route('/newpost', methods=['POST', 'GET'])
def new_post():
    owner = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        title = request.form['new_title']
        body = request.form['new_body']
        if not title or not body:
            return render_template('new_post.html', entry_error = True)
        else:
            blog = Blog(title, body, owner)
            db.session.add(blog)
            db.session.commit()
            return redirect('/blog')
    else:
        return render_template('new_post.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        username_error = False
        password_error = False
        confirm_error = False
        #errors begin
        #password error
        if len(password) < 3 or len(password) > 20:
            password_error = True
        for char in password:
            if char == " ":
                password_error = True
        #confirm error
        if password != confirm:
            confirm_error = True
        #username errors
        period_check = False
        at_check = False
        for char in username:
            if char == " ":
                username_error = True
            if char == ".":
                period_check = True
            if char == "@":
                at_check = True
        if period_check == False or at_check == False:
            username_error = True
        if username_error == False and password_error == False and confirm_error == False:
            user = User(username, password,)
            db.session.add(user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        else:
            return render_template('register.html', username = username, username_error = username_error, password_error = password_error, confirm_error = confirm_error)
    else:
        return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            return redirect('/newpost')
        else: 
            return render_template('login.html', username=username, error=True)
    return render_template('login.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/')

if __name__ == "__main__":
    app.run()
