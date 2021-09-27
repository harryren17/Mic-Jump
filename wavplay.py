
#this file contains the code to play audio files

import pyaudio
import wave
import numpy as np
import time
import threading

file = 'sample1.wav'
chunk = 1024
wf = wave.open(file, 'rb')
frames = wf.getnframes()
rate = wf.getframerate()
length = frames / float(rate)    

#function below (playFile) taken from: https://realpython.com/playing-and-recording-sound-python/
def playFile(file):
    time.sleep(1)
    chunk = 1024  
    wf = wave.open(file, 'rb')
    p1 = pyaudio.PyAudio()
    stream1 = p1.open(format = p1.get_format_from_width(wf.getsampwidth()),
                    channels = wf.getnchannels(),
                    rate = wf.getframerate(),
                    output = True)
    data = wf.readframes(chunk)
    w = 0
    while len(data) > 5:
        stream1.write(data)
        data = wf.readframes(chunk)
    stream1.stop_stream
    stream1.close()
    p1.terminate()

def getDataLength(file):
    #returns an int for the number of bars calculated in the audio file
    p = pyaudio.PyAudio()
    stream = p.open(
    format = p.get_format_from_width(wf.getsampwidth()),
    channels = wf.getnchannels(),
    rate = wf.getframerate(),
    output = True)
    b = 0
    while True:
        try:
            data = np.frombuffer(wf.readframes(chunk),dtype=np.int16)
            peak=np.average(np.abs(data))*2
            bar = int(peak)
            bars="#"*int(50*peak/2**11)
            b += 1
        except:
            stream.stop_stream()
            stream.close()
            p.terminate()
            return b
            
def genBarHeights(b,file):
    #returns length of time, list of barheights corresponding to vol peaks, and 
    #calculates an appropriate delay time to sync audio playing and 
    # terrain generation

    wf = wave.open(file, 'rb')
    frames = wf.getnframes()
    rate = wf.getframerate()
    length = frames / float(rate) 
    p2 = pyaudio.PyAudio()
    stream2 = p2.open(
    format = p2.get_format_from_width(wf.getsampwidth()),
    channels = wf.getnchannels(),
    rate = wf.getframerate(),
    output = True)
    start = time.time()
    barHeights = []
    while True:       
        try:
            data = np.frombuffer(wf.readframes(chunk),dtype=np.int16)  
            peak=np.average(np.abs(data))*2
            bar = int(50*peak/2**11)
            bars="#"*int(50*peak/2**11)
            #b += 1
            barHeights.append(bar)
        except: #when data type != 16 bit int( audio ends)
            t = start - time.time()
            stream2.stop_stream()
            stream2.close()
            p2.terminate()
            return  t, barHeights, b/length#(length/b)*1.18577
    
