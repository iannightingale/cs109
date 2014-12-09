#!/home/ubuntu/anaconda/bin/python
"""
wrangleData.py

Wrangles all the data fetched by getEverything.py, 
then sleeps for an hour to wait for more data to wrangle.
"""

# includes 
execfile("includes.py")
from geopy.distance import great_circle

# Geolocate every user
def step1():
    print "Updating..."
    results = query("SELECT id, username, location FROM users WHERE location <> '' AND lat IS NULL")
    i = 0

    for user_id, username, location in results:
        sameLine("Geolocating: %s (%d/%d)                  " % (username, i, len(results)))
        location = geolocator.geocode(location)
        if location == None:
            lat, lng = -1, -1
        else:
            lat, lng = location.latitude, location.longitude
        result = query("UPDATE users SET lat = %s, lng = %s WHERE id = %s", lat, lng, user_id)
        checkResult(result)
    
        i += 1

    print "\nFinished! step 1" 

# Calculate the distance for every rating
def step2():
    sql = """SELECT DISTINCT users.id, ratings.beer_id, users.lat, users.lng, breweries.lat, breweries.lng
        FROM ratings
        LEFT JOIN users ON ratings.user_id = users.id
        LEFT JOIN beers ON beers.id = beer_id
        LEFT JOIN breweries ON breweries.id = brewery_id
        WHERE users.lat <> -1 AND users.lat IS NOT NULL
        AND distance = -1
        AND user_rating > 0
        AND (breweries.lat <> 0 AND breweries.lng <> 0)
    """

    print "Querying..."
    results = query(sql)
    i = 0
    print "Updating..."
    for user_id, beer_id, lat1, lng1, lat2, lng2 in results:
        	sameLine("%d/%d" % (i, len(results)))
        	i += 1
        	km = great_circle((lat1, lng1), (lat2, lng2)).km
        	result = query("UPDATE ratings SET distance = %s WHERE user_id = %s AND beer_id = %s",
                       km, user_id, beer_id)
        	checkResult(result)
    print "\nFinished step 2!"

import re

# Tokenize every description
def step3():
    pattern1 = re.compile('[^\w\s]+')
    pattern2 = re.compile('\s+')
    beers = query("SELECT id, name, description FROM beers WHERE parsed = 0")
    checkResult(beers)
    i = 0
    print "Tokenizing.."
    for beer_id, name, description in beers:
        print("Tokenizing: %s (%d/%d)" % (name, i, len(beers)))

        tokens = pattern2.sub(' ', pattern1.sub('', description)).upper().strip().split(' ')

        for token in tokens:
            # watch for empty string case
            if token == "":
                continue
            
            word_ids = query("SELECT id FROM words WHERE word = %s", token)
            # insert the word
            if(len(word_ids) == 0):
                result = query("INSERT INTO words (word) VALUES(%s)", token)
                checkResult(result)
                word_id = LAST_INSERT_ID;
            else:
                word_id = word_ids[0][0]

            result = query("""INSERT INTO description_words (beer_id, word_id) VALUES(%s, %s) 
                ON DUPLICATE KEY UPDATE count = count + 1""", beer_id, word_id)

            checkResult(result)

        result = query("UPDATE beers SET parsed = 1 WHERE id = %s", beer_id)
        checkResult(result)

        i += 1
        
    # update Word Counts in Whitelist
    result = query("""UPDATE word_whitelist LEFT JOIN (SELECT word_id, sum(`count`) as cnt FROM description_words GROUP BY word_id) as tmp 
    ON word_whitelist.id = tmp.word_id
    SET word_whitelist.count = tmp.cnt
    WHERE tmp.word_id IS NOT NULL""")
    checkResult(result)
    
    print "\nFinished step 3!"

if __name__ == "__main__":
    try:
        # update superusers table with geo coordinates
        while True:
            step1()
            step2()
            step3()
            sleepCountdown(ONE_HOUR)
            
    except Exception as e:
           print "Error", sys.exc_info()[0]
           print traceback.format_exc()
           sendEmail("Error occurred in getLocations!")
