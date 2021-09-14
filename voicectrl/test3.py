
from myVoice import myVoice
import snowboydecoder
import sys
import signal


interrupted = False


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted

def detect():
    # v.playVoice("在呢")
    # print("listing...")
    # vl = myVoice()
    # print(vl.getVoice())
    print("OK")

def rcbk(tmp):
    print("--->",tmp)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    v = myVoice()
    v.playVoice("你好,准备接受你的指令")

    model = "./小度.pmdl"
    detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)
    # main loop
    detector.start(detected_callback=detect,
                interrupt_check=interrupt_callback,
                audio_recorder_callback = rcbk,
                sleep_time=0.03)

    detector.terminate()


