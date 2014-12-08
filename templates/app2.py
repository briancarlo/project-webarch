#!/usr/bin/env python
import shelve
from subprocess import check_output
import flask
from flask import request, render_template, abort
from os import environ

app = flask.Flask(__name__)
app.debug = True


### NEW CODE FOR LOGINS ###
"""
from flask.ext.login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
    return User.get(userid)
"""
#########################


db = shelve.open("shorten.db")

import random                                           # helps set random path if user doesn't supply a shortpath
from urlparse import urlparse                           # helps check if "http" hasn't been added when user inputs URL
import httplib2                                         # for URL verification

possible = range(48,58) + range(65,91) + range(97,123)  # range of possible ord for alphanumeric random path

@app.route('/home.html')                                # Renders our landing page from the templates folder                                          
def root():
    return render_template('final_temp_1.html')


#### NEW CODE FOR LOGINS ####

@app.route('/login.html')
#@app.route('/login.html', methods=["GET", "POST"])
def login():
    """
    form = LoginForm()
    if form.validate_on_submit():
        # login and validate the user...
        login_user(user)
        flash("Logged in successfully.")
        return redirect(request.args.get("next") or url_for("index"))
    """
    # return render_template("login.html", form=form)
    return render_template('login.html')


#################################


@app.before_request
def validate():                                                 # runs before any app.route()
    if request.path == '/shorts':                               # if the server request is to '/shorts' ...
        shortpath = str(request.form.get('shortpath')).strip()  # grab the shortpath
        if shortpath == "":                         
            pass                                                # if there's no path, no worries
        else:
            if db.get(shortpath):                               # otherwise, check to see if the path is already a key in the DB
                abort(409)                                      # .. and if it's there, throw the 409

        inputURL = str(request.form.get('url')).lower().strip() # grab the URL
        if inputURL == None or inputURL == "":                  # if it's not there ...
            abort(412)                                          # throw the 412

@app.errorhandler(412)
def precondition_failed(e):
    return render_template('final_temp_3.html', code=412, message="Please enter a URL."), 412

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(405)
def method_not_allowed(e):
#    return flask.redirect('/templates/final_temp_1.html'), 405
    return render_template('final_temp_1.html'), 405

@app.errorhandler(409)
def conflict(e):
    return render_template('final_temp_3.html', code=409, message="Short path already exists. Please choose a different path."), 409


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
            if db.get(inputURL):                            # check to see if the URL is already in the DB
                shortpath = db[inputURL]                    # yeah? set it to the shortpath variable
            else:
                myPath = ""                                 # no? create myPath of seven random chars
                for i in range(7):
                    myPath = myPath + chr(random.choice(possible))

                while db.get(myPath):                       # if myPath somehow already exists, create more versions ...
                    myPath = ""                             # ... until a unique myPath is created
                    for i in range(7):
                        myPath = myPath + chr(random.choice(possible))

                db[inputURL] = myPath                       # add the URL to the dict as a key; now any future attempts to ..
                db[myPath] = inputURL                       # ... shorten the same URL (without a specified shortpath) will ...
                shortpath = myPath                          # ... return the same hash. And, of course, add the myPath key to the DB like normal.

        else:                                               # if URL is sent WITH a shortpath, just add that key/value pair to the DB
           db[shortpath] = inputURL
        
        return render_template('final_temp_2.html', url=inputURL, path=shortpath)

    except:
        abort(405)

@app.route('/shorts/<shortpath>', methods=['GET'])
def shorts_shortpath(shortpath):   
    try:
        url = db[str(shortpath)]                            # use the path as the key to the DB to obtain the URL
        return flask.redirect(db[str(shortpath)])           # redirect to that url! easy!
    except:
        abort(404)                                          # didn't work? womp, that path doesn't exist. throw 404.
if __name__ == "__main__":
    app.run(port=int(environ['FLASK_PORT']))
