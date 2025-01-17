from flask import Flask, render_template, request , session , redirect
from flask_sqlalchemy import SQLAlchemy
import json
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail
import math
from datetime import datetime


with open('config.json','r') as c:
    params = json.load(c)["params"]


app = Flask(__name__)
app.secret_key = 'nobody-get-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

# app.config.update(
#     MAIL_SERVER = 'smtp.gmail.com' ,
#     MAIL_PORT = '465' ,
#     MAIL_USE_SSL = True ,
#     MAIL_USERNAME = params['g_username'] ,
#     MAIL_PASSWORD = params['g_password']
# )
# mail = Mail(app)

ENV = 'prod'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = ''
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']


db = SQLAlchemy(app)

class Contacts(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    __tablename__ = 'contacts'
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String(400), nullable=False)
    date = db.Column(db.String(40), nullable=True)
    email = db.Column(db.String(25), nullable=False)

    def __init__(self, name, phone_num, msg, email, date):
        self.name = name
        self.phone_num = phone_num
        self.msg = msg
        self.email = email
        self.date = date


class Posts(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    __tablename__ = 'posts'
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    tagline = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String(2000), nullable=False)
    date = db.Column(db.String(40), nullable=True)
    img_file = db.Column(db.String(25), nullable=False)

    def __init__(self, title, slug, tagline, content ,img_file, date):
        self.title = title
        self.slug = slug
        self.tagline = tagline
        self.content = content
        self.img_file = img_file
        self.date = date

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_post']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    #down the slicing is down[0:n]
    posts = posts[(page-1)*int(params['no_of_post']): (page-1)*int(params['no_of_post'])+int(params['no_of_post'])]
    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif(page==last):
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)


@app.route("/dashboard", methods=['GET' , 'POST'])
def dashboard():
    if('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)
    
    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_pass']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html',params=params,posts=posts)
        
    return render_template('login.html',params=params)

@app.route("/edit/<string:sno>", methods=['GET' , 'POST'])
def edit(sno):
     if('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            box_title = request.form.get('title')
            tline = request.form.get('tagline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            date = datetime.now()
            img_file = request.form.get('img_file')
            

            if sno=='0':
                post = Posts(title=box_title,slug=slug,content=content,tagline=tline,date=date,img_file=img_file)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug =  slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html",params=params,post=post,sno=sno)

@app.route("/uploader", methods=['GET' , 'POST'])
def uploader():
    if('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "UPLOADED SUCCESSFUL"

@app.route("/logout", methods=['GET' , 'POST'])
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>", methods=['GET' , 'POST'])
def delete(sno):
     if('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')
    
    
@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/post/<string:post_slug>" , methods = ['GET'])

def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New Message from ' + name ,
        #                    sender=email,
        #                    recipients = [params['g_username']],
        #                    body = message + "\n" + phone 
        #                  )
    return render_template('contact.html',params=params)
if __name__ == '__main__':

    app.run()
