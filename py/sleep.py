#!/home/ubuntu/anaconda/bin/python
"""
sleep.py

Sleeps for a specified amount of time.

Usage: ./sleep.py SECS_TO_SLEEP
"""

execfile("includes.py")
if(len(sys.argv) == 2):
    sleepCountdown(int(sys.argv[1]))
    sendEmail("Finished Sleeping!")
else:
	print("Usage: ./sleep.py SECS_TO_SLEEP")

