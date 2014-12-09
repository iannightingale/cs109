#!/home/ubuntu/anaconda/bin/python
"""
getEverything.py

Fetches new users and all their beers from a variety of locations.
"""

execfile("includes.py")

LOCATIONS = "../txt/locations.txt"
CITIES = "../cities.txt"

def getLocation(name):
    location = geolocator.geocode(name)
    if location == None:
        print "Bad location: %s" % location
        sys.exit(1)
    return (name, location.latitude, location.longitude, None)  

def backupLocations():
    # backup locations
    with open(LOCATIONS, 'w') as f:
        f.write(str(locations))

# STEP 1) get the local feed
def step1():
    backupLocations()
    name, lat, lng, max_id = locations.pop(0)
    print "STEP 1) Getting users from location: %s, max_id: %d" % (name, max_id if max_id else -1)
    results, max_id = localFeed(lat, lng, max_id)

    # we've finished this location
    if results == []:
        print "Finished searching for users in this location!"
        return;

    print "Total Users: %s" % query("SELECT COUNT(*) FROM users")[0][0]

    # else, add it back in with new max_id
    locations.append((name, lat, lng, max_id))

    backupLocations()

# STEP 2) Update the beer count
def step2():
    print "STEP 2) Getting Beer counts"
    
    for uid, username in query("SELECT id, username FROM users WHERE location != '' AND beercount = -1"):
        beercount, _ = userInfo(username)
        print "Beercount for %s (%d): %d" % (username, uid, beercount)
        if beercount == None:
            print "Bad beercount"
            sendEmail("Bad beercount: user_id %d" % user_id)
            sys.exit(1)
    
        checkResult(query("UPDATE users SET beercount = %s WHERE id = %s", beercount, uid))

# STEP 3) Collect the beers
def step3():
    print "STEP 3) Getting Beer counts"
    for user_id, username, offset in query("SELECT id, username, offset FROM users WHERE downloaded = 0 ORDER BY timestamp DESC"):
        print "Downloading: %s " % username

        while(True):
            print "offset: %d" % offset
            json = userBeers(username, offset)

            if(json == None):
                sendEmail("Bad json (user_id: %d, offset:%d)" % (user_id, offset))
                sys.exit(1)

            # actually store the data
            storeData(json, user_id)

            # break out of the loop
            if(json["response"]["beers"]["count"] != 25):
                break;

            offset += 25
            
            checkResult(query("UPDATE users SET offset = %s WHERE id = %s", offset, user_id))

        # say we updated it
        checkResult(query("UPDATE users SET downloaded = 1 WHERE id = %s", user_id))

if __name__ == "__main__":
    try:
        # actually get the location
        with open(LOCATIONS, 'r') as f:
            locations = eval(f.read())

        print "Read locations from file."

        """
        with open(CITIES, 'r') as f:
            locationNames = list(set(eval(f.read())))

        locations += map(getLocation, locationNames)
        print "Generated locations from names."
        """
    
        # iterate over locations
        while len(locations) > 0:
            step1()
            step2()
            step3()

        # we did it!
        sendEmail("Finished all locations!!!")
    
    except Exception as e:
        print "Error", sys.exc_info()[0]
        print traceback.format_exc()
        sendEmail("Error occurred in main!")
