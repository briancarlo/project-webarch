#!/usr/bin/env python

### regular imports ###
import random                                       # helps set random path if user doesn't supply a shortpath
import os                                           # added for flask-user test
from os import environ                              # this allows the app to be run on the server!
from subprocess import check_output                 # can't remember what this does ...
from datetime import datetime

### normal flask-y imports ###
import flask
from flask import abort
from flask import request, render_template 
from flask import flash, redirect, url_for, session, render_template
from flask import render_template_string            # added for flask-user

### flask extensions ###
from flask.ext.login import LoginManager            # added for flask-login
from flask.ext.mail import Mail                     # added for flask-user
from flask.ext.sqlalchemy import SQLAlchemy         # added for flask-user
from flask.ext.user import login_required, UserManager, UserMixin, SQLAlchemyAdapter    # added for flask-user
from flask.ext.login import login_user , logout_user , current_user , login_required

### other third-party extensions ###
from urlparse import urlparse                       # helps check if "http" hasn't been added when user inputs URL
import httplib2                                     # for URL verification
    
possible = range(48,58) + range(65,91) + range(97,123)  # range of possible ord for alphanumeric random path


# Use a Class-based config to avoid needing a 2nd file
# os.getenv() enables configuration through OS environment variables
""" This stuff allows you to set configurations for the Flask app. It gets implemented below. """
class ConfigClass(object):
    
    # Flask settings
    SECRET_KEY =              os.getenv('SECRET_KEY',       'nerpocalypse')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',     'sqlite:///nerp_test.sqlite')

    CSRF_ENABLED = True

    # Flask-Mail settings
    MAIL_USERNAME =           os.getenv('MAIL_USERNAME',        'email@example.com')
    MAIL_PASSWORD =           os.getenv('MAIL_PASSWORD',        'password')
    MAIL_DEFAULT_SENDER =     os.getenv('MAIL_DEFAULT_SENDER',  '"MyApp" <noreply@example.com>')
    MAIL_SERVER =             os.getenv('MAIL_SERVER',          'smtp.gmail.com')
    MAIL_PORT =           int(os.getenv('MAIL_PORT',            '465'))
    MAIL_USE_SSL =        int(os.getenv('MAIL_USE_SSL',         True))

    # Flask-User settings
    USER_APP_NAME        = "AppName"                # Used by email templates

def create_app():

    app = flask.Flask(__name__)
    app.debug = True
    
    # Configurations set above in the ConfigClass ...
    app.config.from_object(__name__+'.ConfigClass') # from flask-user 
    
    # Initialize Flask extensions
    # QUESTION: How do we get a second table, for the Paths/URLS, into the db below??????
    db = SQLAlchemy(app)                            # Initialize Flask-SQLAlchemy
    mail = Mail(app)                                # Initialize Flask-Mail ... 
    

    # Define the User data model. Make sure to add flask.ext.user UserMixin !!!
    class User(db.Model, UserMixin):

        #__tablename__ = 'users'                                         

        id = db.Column(db.Integer, primary_key=True)

        # User authentication information
        # username = db.Column(db.String(50), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, server_default='')
        reset_password_token = db.Column(db.String(100), nullable=False, server_default='')

        # User email information
        email = db.Column(db.String(255), nullable=False, unique=True)
        confirmed_at = db.Column(db.DateTime())

        # User information
        #active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
        #first_name = db.Column(db.String(100), nullable=False, server_default='')
        #last_name = db.Column(db.String(100), nullable=False, server_default='')
        #registered_on = db.Column('registered_on' , db.DateTime)
 
        def __init__(self, email, password):
            self.password = password
            self.email = email
            #self.registered_on = datetime.utcnow()
     
        def is_authenticated(self):
            return True
     
        def is_active(self):
            return True
     
        def is_anonymous(self):
            return False
     
        def get_id(self):
            return unicode(self.id)
    
    class Path(db.Model):
    
        __tablename__ = 'paths'

        id = db.Column(db.Integer, primary_key=True)
        path = db.Column(db.String(50), nullable=False)
        url = db.Column(db.String(250), nullable=False)
        #url = db.Column(URLType)                                        # special URL datatype uses the 'furl' library. Check out the docs for it. Very neat stuff.
        creator_id = db.Column(db.Integer)
        #creator_id = db.Column(db.Integer, ForeignKey('users.id'))
        clicks = db.Column(db.Integer, default=0)
        #path_creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
   
        def __init__(self, path, url, creator_id):
            self.path = path
            self.url = url
            self.creator_id = creator_id

    ### INITIALIZE THE DB, USER MODEL, LOGIN MANAGER, ETC. ... ###
   
    db.create_all()                                 # Create all database tables if they don't exist ...

    db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
    user_manager = UserManager(db_adapter, app)     # Initialize Flask-User
    login_manager = LoginManager()                  # Initialize the Login manager? ...
    login_manager.init_app(app)                     # this needs a secret key, set above in the Config class

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))



    ### ORIGINAL CODE BELOW ###
    """ This stuff validates URLs and handles errors. """

    @app.before_request
    def validate():                                                 # runs before any app.route()
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

    @app.errorhandler(412)
    def precondition_failed(e):
        flash("put in a url, dumbass")
        return render_template('promo.html')
        #return render_template('final_temp_3.html', code=412, message="Please enter a URL."), 412

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
    #    return flask.redirect('/templates/final_temp_1.html'), 405
        return render_template('promo.html'), 405

    @app.errorhandler(409)
    def conflict(e):
        return render_template('final_temp_3.html', code=409, message="Short path already exists. Please choose a different path."), 409



    #### NEW CODE FOR LOGINS, REGISTRATION, LOGOUTS, ETC. ####
    
    @app.route('/login.html', methods=["GET", "POST"])
    #@login_required                                 # Use of @login_required decorator
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        email = request.form['email']
        password = request.form['password']
        registered_user = User.query.filter_by(password=password,email=email).first()
        if registered_user is None:
            flash('Username or Password is invalid' , 'error')
            return render_template('login.html')
        login_user(registered_user)
        flash('Logged in successfully')
        
        #return render_template('dashboard.html')
        return flask.redirect("http://people.ischool.berkeley.edu/~brian.carlo/server/dashboard.html")  # NOTE: FIX THIS SOMEDAY; USE RELATIVE PATH ON NERP.ME


        #return redirect(request.args.get('next') or url_for('index'))

    @app.route('/register.html', methods=['GET','POST'])
    def register():
        if request.method == 'GET':
            return render_template('register.html')
        user = User(request.form['email'] , request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('User successfully registered')
        app.logger.debug("NEW USER: Email=", user.email, " Password=", user.password)
        return render_template('dashboard.html')

        #return redirect(url_for('login'))
 
    @app.route('/logout')
    def logout():
        logout_user()
        return render_template('promo.html')


    ### EVERYTHING BELOW THIS IS (BASICALLY) ORIGINAL CODE, FROM NERP 1.0 ###

    @app.route('/home.html')        # Renders our landing page from the templates folder                                          
    def root():
        return render_template('promo.html')


    @app.route('/dashboard.html')   # THIS IS NEW!
    @login_required                 # Can't go to dashboard.html w/o login!
    def dashboard():
        
        user = current_user         
        items = Path.query.filter_by(creator_id=user.id).all()

        return render_template('dashboard.html', items=items)


    @app.route('/shorts', methods=['PUT', 'POST'])              # Where the magic happens
    def shorts_put():
        try:
            inputURL = str(request.form.get('url', '')).lower() # grabs value from 'url' key passed in http POST

            parsed = urlparse(inputURL)                         # creates urlparse object
            if parsed.scheme == "":                             # if the scheme doesn't exist ...
                inputURL = "http://" + inputURL                 # add "http" to the front so it'll work in the redirect
          
            h = httplib2.Http()                                 # open up a http object
            try:                                                # see if we can connect ...
                response = h.request(inputURL,'HEAD')           # YES? Then do an http request for the inputURL and return just the headers
                inputURL = response[0]['content-location']      # reset the URL to the main URL of the site (accounts for redirects, etc.)
                if inputURL[-1] != '/':                         
                    inputURL = inputURL + "/"                   # slap a '/' on the end of the URL to avoid duplicates

            except:                                             # NO? Then that URL is broken
                return render_template('final_temp_3.html', code="", message="That URL is broken. Try a different URL!") 

            app.logger.debug(inputURL)

                                                                # grab the value from the 'shortpath' key passed in http POST
            shortpath = str(request.form.get('shortpath', ''))  # for some reason str() matters here ...

            if not shortpath:                                   # this block triggers if the user sent only a URL and NO shortpath
                """
                if Path.query.filter_by(path=shortpath).first()
                #if db.get(inputURL):                            # check to see if the URL is already in the DB

                    shortpath = db[inputURL]                    # yeah? set it to the shortpath variable
                else:

                """

                myPath = ""                                 # no? create myPath of seven random chars
                for i in range(7):
                    myPath = myPath + chr(random.choice(possible))

                while Path.query.filter_by(path=myPath).first():
                #while db.get(myPath):                       # if myPath somehow already exists, create more versions ...
                    myPath = ""                             # ... until a unique myPath is created
                    for i in range(7):
                        myPath = myPath + chr(random.choice(possible))

                try:
                    new_path = Path(myPath,inputURL,current_user.id)
                except:
                    new_path = Path(myPath,inputURL,0)

                db.session.add(new_path)
                db.session.commit()

                flash("http://nerp.me/"+myPath)


                """
                db[inputURL] = myPath                       # add the URL to the dict as a key; now any future attempts to ..
                db[myPath] = inputURL                       # ... shorten the same URL (without a specified shortpath) will ...
                shortpath = myPath                          # ... return the same hash. And, of course, add the myPath key to the DB like normal.
                """

            else:                                               # if URL is sent WITH a shortpath, just add that key/value pair to the DB
                try:
                    new_path = Path(shortpath,inputURL,current_user.id)
                except:
                    new_path = Path(shortpath,inputURL,0)

                db.session.add(new_path)
                db.session.commit()

                flash("http://nerp.me/"+shortpath)
            
            try:
                if current_user.id:
                    return flask.redirect("http://people.ischool.berkeley.edu/~brian.carlo/server/dashboard.html")  
            except:
                return render_template('promo.html')



 #              db[shortpath] = inputURL


 #           return render_template('final_temp_2.html', url=inputURL, path=shortpath)

        except:
            abort(405)

    @app.route('/shorts/<shortpath>', methods=['GET'])
    def shorts_shortpath(shortpath):   
        try:
            path = Path.query.filter_by(path=shortpath).first()
            url = path.url
            #url = db[str(shortpath)]                            # use the path as the key to the DB to obtain the URL
            return flask.redirect(url)                          # redirect to that url! easy!
        except:
            abort(404)                                          # didn't work? womp, that path doesn't exist. throw 404.

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=int(environ['FLASK_PORT']))
