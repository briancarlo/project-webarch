#!/usr/bin/env python


### regular imports ###
import random                                       # helps set random path if user doesn't supply a shortpath
import os                                           # added for flask-user test
from os import environ                              # this allows the app to be run on the server!
from subprocess import check_output                 # can't remember what this does ...
from datetime import datetime

### normal flask-y imports ###
import flask
from flask import abort, request, render_template, flash, redirect, url_for, session, render_template, render_template_string, make_response  
# from flask import request, render_template 
# from flask import flash, redirect, url_for, session, render_template
# from flask import render_template_string            
# from flask import make_response                     

### flask extensions ###
from flask.ext.login import LoginManager            
from flask.ext.mail import Mail, Message                     
from flask.ext.sqlalchemy import SQLAlchemy         
from flask.ext.user import login_required, UserManager, UserMixin, SQLAlchemyAdapter
from flask.ext.login import login_user, logout_user, current_user, login_required, make_secure_token
from flask.ext.bcrypt import Bcrypt

### other third-party extensions ###
from urlparse import urlparse                               # helps check if "http" hasn't been added when user inputs URL
import httplib2                                             # for URL verification
from itsdangerous import URLSafeSerializer, BadSignature    # necessary for confirmation e-mail generation
import hashlib

# import socket, ssl

# bindsocket = socket.socket()
# bindsocket.bind((port=int(environ['FLASK_PORT']))
# bindsocket.listen(5)

#context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

# context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)

# # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
# context.use_privatekey_file('ssl.key')
# context.use_certificate_file('ssl.cert')
# #from OpenSSL import SSL 
# #context = ssl.Context(ssl.PROTOCOL_TLSv1)
# context.use_privatekey_file('ssl.key')
# context.use_certificate_file('ssl.cert')



home_url = 'http://people.ischool.berkeley.edu/~brian.carlo/server/home.html'
dashboard_url = 'http://people.ischool.berkeley.edu/~brian.carlo/server/dashboard.html'

possible = range(48,58) + range(65,91) + range(97,123)  # range of possible ord for alphanumeric random path


# This stuff allows you to set configurations for the Flask app. It gets implemented below.
class ConfigClass(object):
    
    # Flask settings
    SECRET_KEY =              os.getenv('SECRET_KEY',       'nerpocalypse')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',     'sqlite:///nerp_test.sqlite')
    #USER_PASSWORD_HASH =      os.getenv('USER_PASSWORD_HASH', 'sha512_crypt')
    #SERVER_NAME =             os.getenv('SERVER_NAME',      'http://people.ischool.berkeley.edu/~brian.carlo/server/')

    CSRF_ENABLED = True

    # Flask-Mail settings
    MAIL_USERNAME =           os.getenv('MAIL_USERNAME',        'nerp.hq@gmail.com')
    MAIL_PASSWORD =           os.getenv('MAIL_PASSWORD',        'nerpocalypse')
    MAIL_DEFAULT_SENDER =     os.getenv('MAIL_DEFAULT_SENDER',  '"MyApp" <nerp.hq@gmail.com>')
    MAIL_SERVER =             os.getenv('MAIL_SERVER',          'smtp.gmail.com')
    MAIL_PORT =           int(os.getenv('MAIL_PORT',            '465'))
    MAIL_USE_SSL =        int(os.getenv('MAIL_USE_SSL',         True))
    #MAIL_USE_TLS =        int(os.getenv('MAIL_USE_TLS',         True))

    # Flask-User settings
    USER_APP_NAME        = "NERP ME!"                # Used by email templates

def create_app():



    app = flask.Flask(__name__)
    app.debug = True
    
    # Configurations set above in the ConfigClass ...
    app.config.from_object(__name__+'.ConfigClass')
    

    #app.logger.debug(ssl.PROTOCOL_TLSv1)

    # Initialize Flask extensions
    db = SQLAlchemy(app)                            # Initialize Flask-SQLAlchemy
    mail = Mail(app)                                # Initialize Flask-Mail ... 
    bcrypt = Bcrypt(app)                            # Inifialize Bcrypt ...


    # Define the User data model. Make sure to add flask.ext.user UserMixin !!!
    class User(db.Model, UserMixin):

        id = db.Column(db.Integer, primary_key=True)

        password = db.Column(db.String(255), nullable=False, server_default='')
        #reset_password_token = db.Column(db.String(100), nullable=False, server_default='')
        authenticate = db.Column(db.Boolean)

        email = db.Column(db.String(255), nullable=False, unique=True)
        confirmed_at = db.Column(db.DateTime())

        is_enabled = db.Column(db.Boolean(), nullable=False, default=False)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
        registered_on = db.Column('registered_on' , db.DateTime)

        chrome_hash = db.Column(db.String(500))
        secure_token = db.Column(db.String(500))
     
        def hash_password(self, password):
            self.password = bcrypt.generate_password_hash(password)

        def verify_password(self, password):
            return bcrypt.check_password_hash(self.password, password)

        def activate(self):
            self.authenticate = True

        def is_authenticated(self):
            return True
     
        def is_active(self):
            return True
     
        def is_anonymous(self):
            return False
     
        def get_id(self):
            return unicode(self.id)

        def set_chrome_hash(self):
            self.chrome_hash = str(hashlib.sha224(self.email).hexdigest())

        def set_secure_token(self):
            secure_token = make_secure_token(self.email)

    class Path(db.Model):
    
        __tablename__ = 'paths'

        id = db.Column(db.Integer, primary_key=True)
        path = db.Column(db.String(50), nullable=False, unique=True)
        url = db.Column(db.String(250), nullable=False)
        creator_id = db.Column(db.Integer, nullable=True)
        clicks = db.Column(db.Integer, default=0)
        note = db.Column(db.String(300), default="No note.")
        timestamp = db.Column(db.DateTime)

    ### INITIALIZE THE DB, USER MODEL, LOGIN MANAGER, ETC. ... ###
   
    db.create_all()                                 # Create all database tables if they don't exist ...
    db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
    user_manager = UserManager(db_adapter, app)     # Initialize Flask-User
    login_manager = LoginManager()                  # Initialize the Login manager? ...
    login_manager.init_app(app)                     # this needs a secret key, set above in the Config class

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))



    ######################################################################
    #                                                                    #
    #                       CONFIRMATION EMAILS                          #
    #                                                                    #
    ######################################################################


    def get_serializer(secret_key=None):
        app.logger.debug("in get_serializer")
        if secret_key is None:
            secret_key = app.secret_key
        return URLSafeSerializer(secret_key)


    @app.route('/users/activate/<payload>')
    def activate_user(payload):
        app.logger.debug("in activate_user")
        s = get_serializer()
        try:
            user_id = s.loads(payload)
        except BadSignature:
            abort(404)

        user = User.query.get_or_404(user_id)
        user.authenticate = True
        db.session.commit()

        flash('User activated')
        return flask.redirect(home_url)        
       

    def get_activation_link(user):
        app.logger.debug("in get_activation_link")
        s = get_serializer()
        payload = s.dumps(user.id)
        
        return url_for('activate_user', payload=payload)
 

    def send_confirmation_email(user):
        link = get_activation_link(user)
        msg = Message("Hello", sender="nerp.hq@google.com")
        msg.add_recipient(user.email)
        msg.body = "people.ischool.berkeley.edu/~brian.carlo/server"+link
        mail.send(msg)


    ######################################################################
    #                                                                    #
    #                       REGISTRATION AND LOGIN                       #
    #                                                                    #
    ######################################################################
    

    @app.route('/login.html', methods=["GET", "POST"])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        email = request.form['email']
        password = request.form['password']

        registered_user = User.query.filter_by(email=email).first()

        if registered_user.verify_password(password):
            login_user(registered_user)
            flash('Logged in successfully')
            return flask.redirect(dashboard_url)
        else:
            flash('Username or Password is invalid' , 'error')
            return render_template('login.html')            

    @app.route('/register.html', methods=['GET','POST'])
    def register():
        if request.method == 'GET':                
            return render_template('register.html')
        try:
            user = User(email=request.form['email'])
            user.hash_password(request.form['password'])
            db.session.add(user)
            db.session.commit()
            registered_user = User.query.filter_by(email=user.email).first()
            send_confirmation_email(registered_user)
            registered_user.set_chrome_hash()

            app.logger.debug(registered_user.chrome_hash)
            db.session.commit()

            response = make_response(flask.redirect(home_url))
            response.set_cookie('chrome_id', value=registered_user.chrome_hash,max_age=2592000)
            return response
        except:
            flash("That e-mail address is already Nerping for real. Maybe Nerp a different e-mail?")
            return render_template('register.html')


    ######################################################################
    #                                                                    #
    #                           POSTING PATHS!                           #
    #                                                                    #
    ######################################################################


    @app.before_request
    def validate():                                                 # runs before any app.route()
        """ Helper validates URLs and handles errors for CHROME_PUT(), SHORTS_PUT(). """
        if request.path == '/shorts':                               # if the server request is to '/shorts' ...
            shortpath = str(request.form.get('shortpath')).strip()  # grab the shortpath
            if shortpath == "":                         
                pass                                                # if there's no path, no worries
            else:
                if Path.query.filter_by(path=shortpath).first():
                    app.logger.debug("made it here")
                    flash("already taken!")

            inputURL = str(request.form.get('url')).lower().strip() # grab the URL
            if inputURL == None or inputURL == "":                  # if it's not there ...
                abort(412)                                          # throw the 412


    def insert_path_for_user_or_not(path, inputURL):
        """ HELPER FOR CHROME_PUT(), SHORTS_PUT() """
        try:
            new_path = Path(path=path, url=inputURL,creator_id=current_user.id,timestamp=datetime.utcnow())
            app.logger.debug("UID!")
        except:
            app.logger.debug("NOID!")
            new_path = Path(path=path, url=inputURL,creator_id=None,timestamp=datetime.utcnow())
        db.session.add(new_path)
        db.session.commit()


    def make_random_path():
        """ HELPER FOR CHROME_PUT(), SHORTS_PUT() """
        myPath = ""                     
        for i in range(7):
            myPath = myPath + chr(random.choice(possible))
        return myPath


    def format_url(inputURL):
        """ HELPER FOR CHROME_PUT(), SHORTS_PUT() """
        parsed = urlparse(inputURL)                         
        if parsed.scheme == "":                             
            inputURL = "http://" + inputURL                 
      
        h = httplib2.Http()                                 
        try:                                                
            response = h.request(inputURL,'HEAD')           
            inputURL = response[0]['content-location']      
            return inputURL
        except:
            return False      


    def insert_note(path):
        added_path = Path.query.filter_by(path=path).first()
        added_path.note = str(request.form.get('note', ''))


    @app.route('/chrome', methods=['PUT', 'POST'])
    def chrome_put():

        if 'chrome_id' not in request.cookies:
            user_id = 0
        else:
            chrome_hash = request.cookies.get('chrome_id')
            user = User.query.filter_by(chrome_hash=chrome_hash).first()
            user_id = user.id

        inputURL = str(request.form.get('url', '')).lower()

        inputURL = format_url(inputURL)
        if not inputURL:
            response = make_response("Broken URL. Try another")
            return response          

        shortpath = str(request.form.get('shortpath', ''))
        
        if not shortpath:
            myPath = make_random_path()
            while Path.query.filter_by(path=myPath).first():
                myPath = make_random_path()
            insert_path_for_user_or_not(myPath, inputURL)
            insert_note(myPath)
        else:                                    
            insert_path_for_user_or_not(shortpath, inputURL)
            insert_note(shortpath)
        return flask.redirect('http://people.ischool.berkeley.edu/~brian.carlo/server/chrome.html')
        

    @app.route('/shorts', methods=['PUT', 'POST'])
    def shorts_put():
        try:
            inputURL = str(request.form.get('url', '')).lower()
            inputURL = format_url(inputURL)
            if not inputURL:
                response = make_response("Broken URL. Try another")
                return response          
                                                               
            shortpath = str(request.form.get('shortpath', ''))

            app.logger.debug(inputURL + "," + shortpath)

            if not shortpath:                                  
                myPath = make_random_path()
                while Path.query.filter_by(path=myPath).first():
                    myPath = make_random_path()
                insert_path_for_user_or_not(myPath, inputURL)
                path = myPath
            else:                                               
                insert_path_for_user_or_not(shortpath, inputURL)
                path = shortpath
            try:
                if current_user.id:
                    return flask.redirect(dashboard_url)
            except:
                flash("nerp.me/"+path)
                return render_template('promo.html')

        except:
            abort(405)


    @app.route('/delete', methods=['POST','PUT'])
    @login_required                 
    def delete_nerp():
        nerp_id = str(request.form.get('nerp_id', ''))  # REMEMBER TO CHANGE "NERP-ID"
        death_row_nerp = Path.query.filter_by(id=nerp_id).first()
        db.session.delete(death_row_nerp)
        db.session.commit()       


    ######################################################################
    #                                                                    #
    #                           GET METHODS!                             #
    #                                                                    #
    ######################################################################


    @app.route('/shorts/<shortpath>', methods=['GET'])
    def shorts_shortpath(shortpath):   
        try:
            path = Path.query.filter_by(path=shortpath).first()
            url = path.url
            path.clicks = path.clicks + 1
            db.session.commit()
            return flask.redirect(url)                          
        except:
            abort(404)   


    @app.route('/chrome.html', methods=['GET'])
    def chrome_dash():
        return render_template('chrome.html')


    @app.route('/home.html', methods=['GET'])                                      
    def root():
        return render_template('promo.html')


    @app.route('/dashboard.html', methods=['GET'])
    @login_required                 
    def dashboard():
        items = Path.query.filter_by(creator_id=current_user.id).order_by(Path.timestamp.desc()).all()
        top_nerps = Path.query.order_by(Path.clicks.desc()).limit(10)
        return render_template('dashboard.html', items=items, top_nerps=top_nerps)


    @app.route('/logout', methods=['GET'])
    def logout():
        logout_user()
        return flask.redirect(home_url)


    ######################################################################
    #                                                                    #
    #                           ERROR HANDLERS!                          #
    #                                                                    #
    ######################################################################


    @app.errorhandler(412)
    def precondition_failed(e):
        flash("put in a url, dumbass")
        try:
            if current_user.is_authenticated:
                return flask.redirect(dashboard_url)  
        except:
            return render_template('promo.html')


    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404


    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template('promo.html'), 405


    @app.errorhandler(409)
    def conflict(e):
        return render_template('final_temp_3.html', code=409, message="Short path already exists. Please choose a different path."), 409



    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=int(environ['FLASK_PORT']))
        #,ssl_context=context)
