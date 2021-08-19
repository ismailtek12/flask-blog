from MySQLdb import cursors
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
import os
from werkzeug.utils import secure_filename
UPLOAD_FOLDER = '/path/to/the/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app=Flask(__name__)
app.secret_key="ismy__blog"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Flask ile mysql arasında ilişki kurma
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ismy_blog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)
###################################

############### Kullanıcı Giriş Decorator'ı ############

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için oturum açmanız gerekmektedir.","danger")
            return redirect(url_for("login"))

    return decorated_function
###########################################################


####################### Kullanıcı Kayıt Formu #################
class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.length(min=4,max=25)])
    username=StringField("Kullanıcı Adı",validators=[validators.length(min=4,max=25)])
    email=StringField("Email Adresi",validators=[validators.Email(message="Lütfen geçerli bir adres girin.")])
    password=PasswordField("Parola:",validators=[
        validators.DataRequired(message="Lütfen Bir parola Belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor")
    ])
    confirm=PasswordField("Parola Doğrula")
####################################################################

class LoginForm(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola")





@app.route("/")
def index():
    # burası ilerde çok işimize yarayacak.
    #Bu özellik sözlük şekliinde içerik oluşrturmamızı sağlar.
   # articles=[
    # {"id":1,"title":"Deneme1","content":"Deneme1 icerik"},
    #  {"id":2,"title":"Deneme2","content":"Deneme2 icerik"},
    #   {"id":3,"title":"Deneme3","content":"Deneme3 icerik"}

    #]

    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/article/<string:id>")

def detail(id):
    cursor=mysql.connection.cursor()
    sorgu="Select *From articles where id = %s"
    result=cursor.execute(sorgu,(id,))

    if result>0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")
    

@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()

    sorgu="Select * from articles"

    result=cursor.execute(sorgu)

    if result > 0:

        articles=cursor.fetchall()



        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")

@app.route("/dashboard")
@login_required
def dashboard():

    cursor=mysql.connection.cursor()

    sorgu="Select * From articles where author = %s"
    result=cursor.execute(sorgu,(session["username"],))

    if result>0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")

    return render_template("dashboard.html")


##### Register Formu ######

@app.route("/register" , methods=["GET","POST"])
def register():

    form=RegisterForm(request.form)

    if request.method=="POST" and form.validate():

        #burası kayıt olma işleminin veri tabanına yazılması kısmı
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()

        sorgu="Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s) "

        cursor.execute(sorgu,(name,email,username,password))

        mysql.connection.commit()

        cursor.close()
        ###########################################################

        flash("Başarıyla kayıt oldunuz...","success")


        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)


################## LOGİN İŞLEMİ  ###############################
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method=="POST":
        username=form.username.data
        password_entered=form.password.data

        cursor=mysql.connection.cursor()

        sorgu="Select * from users where username=%s"
        result=cursor.execute(sorgu,(username,))
        if result > 0:
            
            data=cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla Giriş Yaptınız...","success")

                session["logged_in"]=True
                session["username"]=username

                return redirect(url_for("index"))

            else:
                flash("Parolanızı Yanlış Girdiniz...","danger")
                return redirect(url_for("login"))

        else:
            flash("Böyle Bir Kullanıcı Bulunmuyor...","danger")
            return redirect(url_for("login"))
    return render_template("login.html",form=form)
##################################################

#Profil Ekranı

@app.route("/profil")
@login_required
def profil():
    
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where author = %s "
    result=cursor.execute(sorgu,(session["username"],))
    if result>0:
        profil=cursor.fetchall()
        return render_template("profil.html",profil=profil)
    else:
        return render_template("index.html")
    

    




@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


#### makale ekleme#################
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form=ArticleForm(request.form)

    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data
        email=form.email.data

        cursor=mysql.connection.cursor()

        sorgu="Insert into articles(title,author,email,content) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],email,content))
        mysql.connection.commit()
        cursor.close()

        flash("Makale başarıyla eklendi","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form=form)
## Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles where author = %s and id = %s"
    result=cursor.execute(sorgu,(session["username"],id))


    if result>0:
        sorgu2="Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        
        flash("böyle bir makale yok veya bu işleme yetkiniz yok","danger")
        return redirect(url_for("index"))

# Makale Güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):

    if request.method=="GET":
        
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where id=%s and author=%s"
        result=cursor.execute(sorgu,(id,session["username"]))

        if result==0:
            flash("Böyle bir makale yok veya yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form=ArticleForm()
            form.title.data = article["title"]
            form.content.data=article["content"]
            return render_template("update.html",form=form)
    else:
        #POST REQUEST KISMI
        form=ArticleForm(request.form)

        newTitle=form.title.data
        newContent=form.content.data

        sorgu2="Update articles Set title = %s,content=%s where id = %s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Makale başarıyla güncellendi","success")

        return redirect(url_for("dashboard"))






### Makale Form
class ArticleForm(Form):
    title=StringField("Makale Başlığı",validators=[validators.length(min=5,max=100)])
    
    content=TextAreaField("Makale İçeriği",validators=[validators.length(min=10)])

    email=StringField("Email Adresi",validators=[validators.Email(message="Lütfen geçerli bir adres girin.")])


## Arama URL
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where title like '%" + keyword +"%'"
        result=cursor.execute(sorgu)
        if result==0:
            flash("Aranan kelimeye uygun makale bulunamadı....","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("article.html",articles=articles)

if __name__ =="__main__":
    app.run(debug=True)