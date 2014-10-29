#!/usr/bin/env python
import shelve
from subprocess import check_output
import flask
from flask import request, render_template
from os import environ

app = flask.Flask(__name__)
app.debug = True

db = shelve.open("shorten.db")

import random                                           # helps set random path if user doesn't supply a shortpath
from urlparse import urlparse                           # helps check if "http" hasn't been added when user inputs URL
import httplib2                                         # for URL verification

possible = range(48,58) + range(65,91) + range(97,123)  # range of possible ord for alphanumeric random path


@app.route('/')                                         # Renders our landing page from the templates folder                                          
def root():
    return render_template('test2.html')

@app.before_request
def validate():
    if request.path == '/shorts':
        shortpath = str(request.form.get('shortpath')).strip()
        if shortpath == "":
            pass
        else:
            if db.get(shortpath):
                return 'Short path already taken', 415
            elif not shortpath.isalpha():
                return 'Unsupported Media Type', 415 

        inputURL = str(request.form.get('url')).lower().strip()
        if inputURL == None or inputURL == "":
            return 'Please enter a URL'

#        h = httplib2.Http()
#        response = h.request(inputURL, 'HEAD')
#        if int(response[0]['status']) < 400:
#            return 'Please enter a valid URL'
        
             

@app.route('/shorts', methods=['PUT', 'POST'])          # Where the magic happens
def shorts_put():

    inputURL = str(request.form.get('url', '')).lower() # grabs value from 'url' key passed in http POST

    parsed = urlparse(inputURL)                         # creates urlparse object
    if parsed.scheme == "":                             # if the scheme doesn't exist ...
        inputURL = "http://" + inputURL                 # add "http" to the front so it'll work in the redirect

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
    
    # if URL is sent WITH a shortpath, just add that key/value pair to the DB
    else:
        db[shortpath] = inputURL
    return "url =" + inputURL + " path=" + shortpath

@app.route('/shorts/<shortpath>', methods=['GET'])
def shorts_shortpath(shortpath):   
    if db.get(str(shortpath)):
        url = db[str(shortpath)]
        return flask.redirect(db[str(shortpath)])
    else:
        return render_template('404.html')        
    
if __name__ == "__main__":
    app.run(port=int(environ['FLASK_PORT']))
