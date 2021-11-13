import os
import time
import picamera
import threading
from datetime import datetime

from logger import logger

class BrewCamera():
    def __init__(self, interval=10):
        self.lastCaptureTimestamp = None
        self.interval = interval
        self.warmupTime = 0.3

    def spawnBackgroundCapture(self):
        thread = threading.Thread(target=self.captureOnIntervalForever, args=())
        thread.daemon = True
        thread.start()
        logger.info("spawned camera capture daemon at interval: {}".format(self.interval))

    def captureOnIntervalForever(self):
        while True:
            time.sleep(self.interval - self.warmupTime)
            self.capture()

    def capture(self):
        try:
            logger.debug('Capturing image')
            with picamera.PiCamera() as camera:
                camera.resolution = (1297, 972)
                camera.rotation = 180
                camera.annotate_background = picamera.Color('black')
                camera.annotate_text_size = 50 # (values 6 to 160, default is 32)
                camera.annotate_text = datetime.now().strftime('%A %d %b %Y %H:%M:%S')

                # Camera warm-up time
                time.sleep(self.warmupTime)
                camera.capture('assets/foo.jpg')
                self.lastCaptureTime = datetime.now()
                os.replace('assets/foo.jpg', 'assets/capture.jpg')

        except picamera.exc.PiCameraMMALError as error:
            logger.error('Picamera MMAL exception. Retrying picture in 1 second', es={
                'error': str(error),
                'exception': error.__class__.__name__
            })
            time.sleep(1)
            self.capture()

