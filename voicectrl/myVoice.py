'''
Created on 2020年1月31日

@author: zjf
'''
import speech_recognition as sr
from aip import AipSpeech
from playsound import playsound
import os
import numpy as np
import pyaudio
import audioop
import collections
import math
import wave
import os
import datetime
import subprocess
import time


#pip install SpeechRecognition
#pip install PocketSphinx
#pip install pyaudio
#pip install baidu-aip
#pip install playsound

#https://cloud.tencent.com/developer/article/1149294


class myVoice(object):

    def __init__(self):
        self.SAMPLE_RATE = 16000
        self.CHUNK = 2048 # RATE / number of updates per second
        self.SAMPLE_WIDTH = 2
        self.seconds_per_buffer = float(self.CHUNK) / self.SAMPLE_RATE
        self.energy_threshold =  self.__calcBackVoice()
        self.stream = None
    
    def getframerate(self):
        return self.SAMPLE_RATE
    
    def getsampwidth(self):
        return self.SAMPLE_WIDTH
    
    def getnchannels(self):
        return 1
    
    def __calcBackVoice(self):
        #计算背景音大小
        energy_threshold = 300  # minimum audio energy to consider for recording
        dynamic_energy_adjustment_damping = 0.15
        dynamic_energy_ratio = 1.5
        elapsed_time = 0
        
        p = pyaudio.PyAudio()
        stream=p.open(format=pyaudio.paInt16,channels=1,rate=self.SAMPLE_RATE,input=True,
                      frames_per_buffer=self.CHUNK)
        # adjust energy threshold until a phrase starts
        while True:
            elapsed_time += self.seconds_per_buffer
            if elapsed_time > 1: break #采集1秒
            buffer = stream.read(self.CHUNK)
            energy = audioop.rms(buffer, self.SAMPLE_WIDTH)  # energy of the audio signal
    
            # dynamically adjust the energy threshold using asymmetric weighted average
            damping = dynamic_energy_adjustment_damping ** self.seconds_per_buffer  # account for different chunk sizes and rates
            target_energy = energy * dynamic_energy_ratio
            energy_threshold = energy_threshold * damping + target_energy * (1 - damping)
        stream.close()
        return energy_threshold
    
    def _createVoice(self):
        if self.stream == None:
            p = pyaudio.PyAudio()
            stream=p.open(format=pyaudio.paInt16,channels=1,rate=self.SAMPLE_RATE,input=True,
                          frames_per_buffer=self.CHUNK)
            self.stream = stream
        return self.stream
    
    def _getSoundPiece(self):
        #获取声音片段
        pause_threshold = 0.8  # seconds of non-speaking audio before a phrase is considered complete
        non_speaking_duration = 0.5  # seconds of non-speaking audio to keep on both sides of the recording
        
        pause_buffer_count = int(math.ceil(pause_threshold / self.seconds_per_buffer))  # number of buffers of non-speaking audio during a phrase, before the phrase should be considered complete
        non_speaking_buffer_count = int(math.ceil(non_speaking_duration / self.seconds_per_buffer))  # maximum number of buffers of non-speaking audio to retain before and after a phrase
    
        stream=self._createVoice()
        
        frames = collections.deque()
        #检测说话开始
        old_energy = 0
        while True:
            buffer = stream.read(self.CHUNK)
            frames.append(buffer)
            if len(frames) > non_speaking_buffer_count:  # ensure we only keep the needed amount of non-speaking buffers
                frames.popleft()
        
            # detect whether speaking has started on audio input
            energy = audioop.rms(buffer, self.SAMPLE_WIDTH)  # energy of the audio signal
            if energy > self.energy_threshold and old_energy > self.energy_threshold: 
                break #两次超过能量值，则结束
            old_energy = energy
            
        #检测说话结束 
        pause_count = 0
        while True:
            buffer = stream.read(self.CHUNK)
            frames.append(buffer)
            # check if speaking has stopped for longer than the pause threshold on the audio input
            energy = audioop.rms(buffer, self.SAMPLE_WIDTH)  # unit energy of the audio signal within the buffer
            if energy > self.energy_threshold:
                pause_count = 0
            else:
                pause_count += 1
            if pause_count > pause_buffer_count:  # end of the phrase
                break
        return frames 
    
    def getVoice(self):
        frames = self._getSoundPiece()
        data = b"".join(frames)
        
        """ 你的 APPID AK SK """
        APP_ID = '18360185'
        API_KEY = 'GGa4gj9upEP671RW6xvBtmiR'
        SECRET_KEY = 'Nt4nAOuxFpZzlS0G1LtalOO0IlsnOGLP'
        client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
        
        # 识别本地文件
        vv = client.asr(data, 'wav', 16000, {
            'lan': 'zh',
            'dev_pid': 1537,
        })
        
        if "result" in vv:
            return vv["result"][0].strip('。')
        else:
            return vv
    
    
    def get_wave_filename(self,fileFullName):
        # MP3文件转换成wav文件
        # 判断文件后缀，是mp3的，直接处理为16k采样率的wav文件；
        # 是wav的，判断文件的采样率，不是8k或者16k的，直接处理为16k的采样率的wav文件
        # 其他情况，就直接返回AudioSegment直接处理
        fileSufix = fileFullName[fileFullName.rfind('.')+1:]
        # print(fileSufix)
        filePath = fileFullName[:fileFullName.find(os.sep)+1]
        # print(filePath)

        wavFile = fileFullName.replace(".mp3",".wav")#"wav_%s.wav" %datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        # wavFile = filePath + wavFile
        cmdLine = "ffmpeg -i \"%s\" -ar 16000 " %fileFullName
        cmdLine = cmdLine + "\"%s\"" %wavFile
        # print(cmdLine)
        # ret = subprocess.run(cmdLine,cwd="/opt/voicectrl/")
        ret = os.system(cmdLine)#"sh /opt/voicectrl/a.sh")
        print("ret code:%i" %ret)
        # file = open(wavFile, "rb")
        # file.read()
        ding_wav = wave.open(wavFile, 'rb')
        os.remove(fileFullName)
        os.remove(wavFile)
        return ding_wav

    def playVoice(self, strs):
        """ 你的 APPID AK SK """
        APP_ID = '18360185'
        API_KEY = 'GGa4gj9upEP671RW6xvBtmiR'
        SECRET_KEY = 'Nt4nAOuxFpZzlS0G1LtalOO0IlsnOGLP'
        client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
        
        result = client.synthesis(strs, 'zh', 1, {
        'vol': 5,
        })
        # 识别正确返回语音二进制 错误则返回dict 参照下面错误码
        if not isinstance(result, dict):
            with open('tmp.mp3', 'wb') as f:
                f.write(result)

        ding_wav = self.get_wave_filename("tmp.mp3")
        ding_data = ding_wav.readframes(ding_wav.getnframes())
        audio = pyaudio.PyAudio()
        stream_out = audio.open(
            format=audio.get_format_from_width(ding_wav.getsampwidth()),
            channels=ding_wav.getnchannels(),
            rate=ding_wav.getframerate(), input=False, output=True)
        stream_out.start_stream()
        stream_out.write(ding_data)
        time.sleep(0.2)
        stream_out.stop_stream()
        stream_out.close()
        audio.terminate()
         
        # playsound("tmp.mp3")
        # os.remove("tmp.mp3")
