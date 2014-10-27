#!/usr/bin/env python
import shelve
from subprocess import check_output
import flask
from flask import request
from flask import render_template
from os import environ

app = flask.Flask(__name__)
app.debug = True

db = shelve.open("shorten.db")


# This sets up the server-generated random hash if user doesn't supply a shortpath
import random
possible = range(48,58) + range(65,91) + range(97,123)


# This module helps us check to see if "http" hasn't been added when user inputs URL
from urlparse import urlparse


# Renders our landing page from the templates folder 
@app.route('/')
def root():
    return render_template('test_copy.html')

@app.before_request
def validate():
    if request.path == '/shorts':
        shortpath = str(request.form.get('shortpath'))
        if db.get(shortpath):
            return 'Short path already taken', 415
        elif not shortpath.isalpha():
            return 'Please use only letters for shortpath', 404 

        
       # inputURL = request.form.get('url')
       # if inputURL:
       #     return 'THERE IS A URL'



# Where the magic happens
@app.route('/shorts', methods=['PUT', 'POST'])
def shorts_put():

    app.logger.debug("whatup")

    inputURL = request.form.get('url', '')              # grabs value from 'url' key passed in http POST

    parsed = urlparse(inputURL)                         # creates urlparse object
    if parsed.scheme == "":                             # if the scheme doesn't exist ...
        inputURL = "http://" + inputURL                 # add "http" to the front so it'll work in the redirect

    # grab the value from the 'shortpath' key passed in http POST
    shortpath = str(request.form.get('shortpath', ''))  # for some reason str() matters here ...
 
    # this block triggers if the user sent only a URL and NO shortpath
    if not shortpath:
        if db.get(inputURL):                            # check to see if the URL is already in the DB
            shortpath = db[inputURL]                    # yeah? set it to the shortpath variable
        else:
            myHash = ""                                 # no? create a hash of seven random chars
            for i in range(7):
                myHash = myHash + chr(random.choice(possible))
       
            while db.get(myHash):                       # if that hash somehow exists, create more until a unique one is created
                myHash = ""
                for i in range(7):
                    myHash = myHash + chr(random.choice(possible))  

            db[inputURL] = myHash                       # add the URL to the dict as a key; now any future attempts to ..  
            db[myHash] = inputURL                       # ... shorten the same URL (without a specified shortpath) will ...
            shortpath = myHash                          # ... return the same hash. And, of course, add the hash key to the DB like normal.
    
    # if URL is sent WITH a shortpath, just add that key/value pair to the DB
    else:
        db[shortpath] = inputURL
    return "url =" + inputURL + " path=" + shortpath

@app.route('/shorts/<shortpath>', methods=['GET'])
def shorts_shortpath(shortpath):   
    url = db[str(shortpath)]
    # return flask.redirect(url)
    return flask.redirect(db[str(shortpath)])

    
if __name__ == "__main__":
    app.run(port=int(environ['FLASK_PORT']))
