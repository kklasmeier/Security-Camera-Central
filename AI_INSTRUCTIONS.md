i have a security camera system. which has 5 camera agents (raspberry pi zero 2) and 1 central server (raspberry pi 4) and an AI server (Raspberry pi  5 with 16gb memory) running Ollama.

The main central server manages accepts api calls from each of the 5 camera agents, holds the database and it also serves up a central website as the security camera user interface. the api is python based and the website runs under nginx. The central central server, There service agents that run as separate python screens:
    1. conversion process of videos in the h264 format to mp4 using ffmpeg. 
    2. optimisation of .mp4 files to a smaller format.
    3. AI agent interaction

Each AI agent detects motion events. when a motion event occurs, it takes 2 pictures, one picture when the event is detected and one picture 4 seconds later. it also takes about a 60 second video where ~30 seconds happens before the motion detection event occurs and ~30 seconds happens after. Everything gets posted to the Central Server. 

Project interactions:
* I am a product own who gives requirements and i work with you to come up with designs and apporaches.
* You act as an architect and collaborate with the product owner for designs
* You are the developer who develop code

This project is already built and in a maintenance phase where we will fix defect and where we will extend capabilites with new features.

