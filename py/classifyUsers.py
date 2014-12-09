#!/home/ubuntu/anaconda/bin/python
"""
classifyUsers.py

Classifies all users and output the results into ../txt/
"""

execfile("includes.py")

# creates an output from the current unix timestamp
OUTPUT = "../txt/classifyOutput-%d.txt" % int(time.time())

results = []

i = 0

for user_id, count in query("SELECT user_id, count(*) FROM ratings GROUP BY user_id"):

    print "Getting #%d" % i
    
    i += 1

    # pull data for this user
    beers = sqlDataFrame("""SELECT ratings.*, beers.*, avg_rating FROM `ratings` LEFT JOIN beers ON (beer_id = beers.id) LEFT JOIN breweries
           ON brewery_id = breweries.id WHERE ratings.user_id = %s AND ratings.user_rating > 0 AND ratings.user_id IS NOT NULL""", user_id)
           
    try:
        results.append(((user_id, count), classify(beers)))
        # write this out every time just in case. The IO is neglibilge compared to how long the classifier is,
        # and we want to handle failure.
        with open(OUTPUT, 'w') as f:
            f.write(str(results))

    # We don't really care what went wrong, but it's good to print out in case something's failing that shouldn't be
    except Exception as e:
        print e