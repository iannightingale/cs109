#!/home/ubuntu/anaconda/bin/python
"""
wordcloud.py

Creates a hi res and low res word cloud from the word whitelist.
"""
# includes
execfile("../includes.py")

# beer mask image
MASK_FILE = "../../img/beer_bottle.png"

timestamp = int(time.time())

LOW_RES = "../../img/beer_maps/low_res-%d.png" % timestamp
HIGH_RES = "../../img/beer_maps/high_res-%d.png" % timestamp


from wordcloud import WordCloud

print "Getting words"

# find the total amount of words
count = query("""SELECT sum(`count`) FROM word_whitelist""")[0][0]
count = float(count)

print "Sum: %f" % count

words = []

# get the words from the whitelist and calculate their frequences
sql = """SELECT word, count FROM word_whitelist ORDER BY `count` DESC"""
for word, frequency in query(sql):
    words.append((word, float(frequency) / count))

print "Creating cloud."

from scipy.misc import imread

mask = imread(MASK_FILE)

# generate the world cloud. This takes a while because the library is not parallelized.
wordcloud = WordCloud(font_path="/usr/share/fonts/truetype/msttcorefonts/Georgia.ttf", ranks_only=True, max_words = len(words),
    mask=mask, background_color="white")
wordcloud.fit_words(words)

print "Creating LOW RES image."
wordcloud.to_file(LOW_RES)

# low let's beef up the scale
wordcloud.scale = 12

print "Creating HI RES image."
img = wordcloud.to_image()
img.save(HIGH_RES, dpi=(100000,100000))