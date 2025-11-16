i have a security camera system. which has 4 camera agents (raspberry pi zero 2) and 1 central server (raspberry pi 4). i have a new raspberry pi 5 with 16gb memory which is my ai server.

The main central server manages accepts api calls from each of the 4 camera agents, holds the database and it also serves up a central website as the security camera user interface. the api is python based and the website runs under nginx
on the central central server, i have two service agents that run as separate python screens:
    1. conversion process of videos in the h264 format to mp4 using ffmpeg. 
    2. optimisation of .mp4 files to a smaller format.

The central server detects motion events. when a motion event occurs, it takes 2 pictures, one picture when the event is detected and one picture 4 seconds later. it also takes about a 60 second video where ~30 seconds happens before the motion detection event occurs and ~30 seconds happens after.  