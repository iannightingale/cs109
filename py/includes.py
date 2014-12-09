import requests

""" GLOBAlS / CONSTANTS """
# API Constants
CLIENT_ID = "XXXXXXXXXXX"
CLIENT_SECRET = "XXXXXXXXXXX"
BASE_URL = "https://api.untappd.com/v4/"
ONE_HOUR = 3660 # (one hour and some change)
CURRENT_WAIT = 0

# API rate limit (total allowed requests)
RATE_LIMIT = -1

# amount of requests we have left
RATE_LIMIT_REMAINING = -1

# MySQL config
MYSQL_HOST = "localhost"
MYSQL_USER = "cs109"
MYSQL_PASSWORD = "XXXXXXXXXXX"
MYSQL_SELECT_USER = "cs109_select"
MYSQL_SELECT_PASSWORD = "XXXXXXXXXXX"
MYSQL_DB = "cs109"

# Last MySQL insert id
LAST_INSERT_ID = None

# Last recorded MySQL error
MYSQL_ERROR = ""

# Email constants
EMAIL_USER = "XXXXXXXXXXX@gmail.com"
EMAIL_PASSWORD = "XXXXXXXXXXX"

# Scraping constants

# beercount for a user that we'll download
DOWNLOAD_THRESHOLD = 1500

""" MISC """

import time
from datetime import datetime, timedelta

import os
from signal import *

# handles a ctrl-\ signal
def process_quit(signum, frame):
    sys.exit(1)

signal(SIGQUIT, process_quit)

# write a line to the current line in the terminal.
# @param sring String to write to the current line.
def sameLine(string):
    sys.stdout.write("\r" + string)
    sys.stdout.flush()

# Sleeps for a certain a specified amount of seconds, and show the countdown
# @param secs Amount of seconds to sleep for.
def sleepCountdown(secs):
    while True:
        try:
            temp = secs
            print "Sleeping for %d seconds." % secs
            print("DAYS:HOURS:MIN:SEC")
            while(secs >= 0):
                sec = timedelta(seconds=secs)
                d = datetime(1,1,1) + sec
                sameLine("%02d:%02d:%02d:%02d" % (d.day-1, d.hour, d.minute, d.second))
                time.sleep(1)
                secs -= 1
            break
        
        # Allow us to reload this file on a keyboard interrupt
        except KeyboardInterrupt:
            print "\nInterrupt detected."
            print "Press ctrl+\ to exit"
            execfile("includes.py")
            print "Includes reloaded."
            continue
        
        
    print "\nSlept %d secsonds." % temp

""" MYSQL """

import MySQLdb as mdb
import sys, traceback

import pandas.io.sql as psql

# return a Pandas data frame given a SQL query and optional parameters.
# @param query SQL query to execute
# @param arg1, arg2, arg3, etc. Parameters to passed into the SQL query (that replace %s parameters).
# @return Pandas data frame on success, None on failure
# @notes The SQL user used only has SELECT privelges on the MYSQL_DB database (for good reason).
def sqlDataFrame(query, *args):
    global MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_ERROR 
    df = None
    try:
        con = mdb.connect(MYSQL_HOST, MYSQL_SELECT_USER, MYSQL_SELECT_PASSWORD, MYSQL_DB);
        df = psql.read_sql(query, params=args, con=con)  

    # handle any exceptions
    except Exception as e:
        print traceback.format_exc()
        error = "MySQL Error %d: %s" % (e.args[0],e.args[1])
        print error
        MYSQL_ERROR = error
    finally:
        con.close()
        return df

# check the result of a MySQL query, emailing and quitting as necessary
# @param result Result of a query or sqlDataFrame function call.
def checkResult(result):
    global MYSQL_ERROR
    if result == None:
        sendEmail(MYSQL_ERROR)
        sys.exit(1)

# Exceutes a MySQL query given a SQL query and optional parameters.
# @param query SQL query to execute
# @param arg1, arg2, arg3, etc. Parameters to passed into the SQL query (that replace %s parameters).
# @return None on failure, the result of the query on success.
# @notes The SQL user used has all privileges on the MYSQL_DB database. USE WITH CAUTION.
def query(query, *args):
    global MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_ERROR, LAST_INSERT_ID
    result = None
    try:
        con = mdb.connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB);

        # handle unicode problems client side
        con.set_character_set('utf8')
        cur = con.cursor()
        
        # handle unicode errors server side
        cur.execute('SET NAMES utf8;') 
        cur.execute('SET CHARACTER SET utf8;')
        cur.execute('SET character_set_connection=utf8;')
         
        cur.execute(query, args)
        con.commit()
        LAST_INSERT_ID = cur.lastrowid

        result = cur.fetchall()

    except Exception as e:
        print traceback.format_exc()
        error = "MySQL Error %d: %s" % (e.args[0],e.args[1])
        print error
        MYSQL_ERROR = error
    
    finally:
        con.close()
        return result

""" EMAIL """

import smtplib, email
from email.mime.text import MIMEText

# Sends an email
# @param body Body of the email to send
def sendEmail(body):
    global EMAIL_USER, EMAIL_PASSWORD
    try:
        smtp_host = 'smtp.gmail.com'
        smtp_port = 587
        server = smtplib.SMTP()
        server.connect(smtp_host,smtp_port)
        server.ehlo()
        server.starttls()
        server.login(EMAIL_USER,EMAIL_PASSWORD)
        fromaddr = "CS109 Server"
        tolist = ["iannightingale@college.harvard.edu"]
        sub = "CS109 Notification"

        msg = email.MIMEMultipart.MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = email.Utils.COMMASPACE.join(tolist)
        msg['Subject'] = sub  
        msg.attach(MIMEText(body))
        msg.attach(MIMEText('\nLove, cs109.inight.in', 'plain'))
        server.sendmail(EMAIL_USER,tolist,msg.as_string())
        
    except Exception as e:
        print traceback.format_exc()
        error = "Email failed to send (error %d): %s" % (e.args[0],e.args[1])
        print error
        MYSQL_ERROR = error
    
""" API REQUESTS """

# Generic Untappd API request
# @param method Name of API call
# @param parameters Optional paremters to send with the call
def apiRequest(method, params={}):
    global RATE_LIMIT, RATE_LIMIT_REMAINING
    print "Rate Limit Remaining: %d" % RATE_LIMIT_REMAINING
    
    if(RATE_LIMIT_REMAINING <= 1 and RATE_LIMIT_REMAINING != -1):
        sleepCountdown(ONE_HOUR)
    
    # add our client id and secret
    params["client_id"] = CLIENT_ID
    params["client_secret"] = CLIENT_SECRET
    response = requests.get(BASE_URL + method, params=params)
    
    try:
        json = response.json()
    except JSONDecodeError as err:
        raise(err)
    
    # make sure we got expected json back
    if not json or "meta" not in json or "code" not in json["meta"]:
        raise Exception("Error: %d: No additional info available" % response.status_code)

    # check the meta from the json
    if json["meta"]["code"] != 200:
        # handle weird 501s we're getting and sleep
        if json["meta"]["code"] == 501:
            print "Received 501 (something went wrong). Trying again in 10 seconds."
            sleepCountdown(10)
            return apiRequest(method, params)
            
        # handle a 500 and sleep for a whole hour
        if json["meta"]["code"] == 500:
            print "Received 500 (something's wrong on their end). Trying again in an hour."
            sleepCountdown(ONE_HOUR)
            return apiRequest(method, params)
        
        # handle an unknown exception
        RATE_LIMIT_REMAINING = 0
        raise Exception("Error %d (%s): %s" % (json["meta"]["code"], json["meta"]["error_detail"], json["meta"]["error_detail"]))
        
	# update global rate limit information
    RATE_LIMIT = int(response.headers["X-Ratelimit-Limit"])
    RATE_LIMIT_REMAINING = int(response.headers["X-Ratelimit-Remaining"])

    # we did it!
    return json

# helper for downloading beers
# @param json JSON object contain all the beers.
# @param user_id ID of the user.
def storeData(json, user_id):
    # iterate over all the items
    for item in json["response"]["beers"]["items"]:
        brewery = item["brewery"]
        beer = item["beer"]
        location = brewery["location"]  

        # get the user rating for the beer
        score = item["rating_score"]

        # add beer
        sql = """INSERT INTO beers (id, brewery_id, name, description, abv, ibu, style, global_rating) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE timestamp = CURRENT_TIMESTAMP"""
        params = (beer["bid"],
                  brewery["brewery_id"],
                  beer["beer_name"], 
                  beer["beer_description"], 
                  beer["beer_abv"], 
                  beer["beer_ibu"],
                  beer["beer_style"], 
                  beer["rating_score"])

        result = query(sql, *params)
        checkResult(result)

        # add brewery
        sql = """INSERT INTO breweries (id, name, city, state, country, lat, lng) VALUES(%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE timestamp = CURRENT_TIMESTAMP"""

        params = (brewery["brewery_id"],
                  brewery["brewery_name"],
                  location["brewery_city"],
                  location["brewery_state"],
                  brewery["country_name"],
                  location["lat"],
                  location["lng"])

        result = query(sql, *params)
        checkResult(result)

        # add user rating
        sql = """INSERT INTO ratings (beer_id, user_id, user_rating) VALUES(%s, %s, %s)
            ON DUPLICATE KEY UPDATE timestamp = CURRENT_TIMESTAMP"""

        result = query(sql, beer["bid"], user_id, score)
        checkResult(result)

# download the beers for a given user
# @param username User's username.
# @param offset (optional) Offset to start from (because the API only returns 25 at a time)
def userBeers(username, offset=0):
    try:
        json = apiRequest("user/beers/" + username, {"offset":offset})
        
    except Exception as inst:
        print inst
        print traceback.format_exc()
        return None
    
    return json
    

# download the info for a given user.
# @param username User's username.
# @return (the user's beer_count, the user's location)
def userInfo(username):
    try:
        json = apiRequest("user/info/" + username)
    
    except Exception as inst:
        print inst
        return None, None
    
    # retrieve the beers from the jason object
    total_beers = json["response"]["user"]["stats"]["total_beers"]
    
    # set location to the empty string if they don't have one
    location = "" if "location" not in json["response"]["user"] else json["response"]["user"]["location"]
    
    return total_beers, location

import geopy 
from geopy.geocoders import Nominatim
geolocator = Nominatim(timeout=10)

# inserts all the users from a local feed given a lat and lng
# @lat Latitude to search around.
# @lng Longitude to search around.
# @max_id (optional) Max id of checkin to pass to API (so we can search deeper into the feed).
# @return (array of MySQL query results, the minimum checkin id that we saw)
def localFeed(lat, lng, max_id=None):
    try:
        # make the API request
        params = {"lat":lat, "lng":lng}
        if max_id == None:
            params["max_id"] = max_id
        json = apiRequest("thepub/local/", params)
    except Exception as inst:
        print inst
        return None, max_id
    
    # get the checkins from the json object
    checkins = json["response"]["checkins"]["items"]
    results = []
    checkin_ids = []
    
    # no more checkins to be found
    if checkins == []:
        return results, -1
    
    # insert every user from the checkin
    for item in checkins:
        user = item["user"]
        uid = user["uid"]
        username = user["user_name"]
        location = "" if "location" not in user else user["location"]
        result = query("INSERT IGNORE INTO users (id, username, location) VALUES(%s, %s, %s)", uid, username, location)
        results.append(result)
        checkin_ids.append(item["checkin_id"])
    
    return results, min(checkin_ids)

""" CLASSIFYING """
import sklearn.cross_validation
from sklearn.ensemble import RandomForestClassifier
import sklearn.grid_search

# Returns classification info given a dataset of beers
# @param beers Beer Pandas Data Frame
def classify(beers):
    beers.dropna()
    # remove beers with no data
    beers2 = beers[beers.ibu != 0]
    beers2 = beers2[beers2.abv != 0]
    
    # change ratings to integers
    target = beers2.user_rating*2
    
    # drop ratings and subset for features we want
    beers3 = beers2.drop("user_rating", 1)
    beers4 = beers3[["distance", "global_rating", "abv", "ibu", "style", "avg_rating"]]
    
    # discretize styles
    styles = {}
    count= 0
    for style in set(beers4.style):
        styles[style] = count
        count +=1
    beers5 = beers4.replace(styles)
    
    # append size to our output list
    rating_count = len(beers5)
    
    # to matrix and split test/train
    fit_matrix = beers5.as_matrix()
    Xtrain, Xtest, Ytrain, Ytest = sklearn.cross_validation.train_test_split(fit_matrix,target,test_size = 0.33, random_state=42)
    
    # parameter tuning step
    k = range(1,60)
    params = {"n_estimators": k}
    classifier = sklearn.ensemble.RandomForestClassifier(n_estimators=k, random_state=42)
    grid_class = sklearn.grid_search.GridSearchCV(classifier, params, cv=10, scoring="f1")
    # extract and report results
    results = grid_class.fit(Xtrain,Ytrain)
    k_tuned = results.best_params_["n_estimators"]

    # now test
    classifier = sklearn.ensemble.RandomForestClassifier(n_estimators=k_tuned, random_state=42)
    yhat = classifier.fit(Xtrain, Ytrain).predict(Xtest)
    multiclass_score = sklearn.metrics.accuracy_score(Ytest, yhat, normalize=True)
    imps = classifier.fit(Xtrain, Ytrain).feature_importances_
    top_feature = beers5.columns[list(imps).index(max(imps))]
    
    # binarize
    cutoff = np.percentile(beers2.user_rating, 75)
    yhat2 = (yhat >= cutoff*2)
    Ytest2 = (Ytest >=cutoff*2)
    binary_score = sklearn.metrics.accuracy_score(Ytest2, yhat2, normalize=True)
    
    return rating_count, multiclass_score, binary_score, top_feature
    
""" GRAPHING """
import numpy as np
import scipy as sp
import pandas as pd
import sklearn
import seaborn as sns
from matplotlib import pyplot as plt

import matplotlib.pylab as pylab

# Initialization steps that have to be run in a cell directly (and can't be included)
def init():
    # change default figure size
    pylab.rcParams['figure.figsize'] = 10, 6