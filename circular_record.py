#!/usr/bin/env python3

import argparse
import os
import time

import cv2

from collections import deque

from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from picamera2 import Picamera2, MappedArray

def overlay_timestamp(request):
    ORIGIN = (0, 30)
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    SCALE = 1
    COLOR = (0, 255, 0)
    THICKNESS = 2

    timestamp = time.strftime("%Y-%m-%d %X")
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, timestamp, ORIGIN, FONT, SCALE, COLOR, THICKNESS)

if __name__ == "__main__":
    # command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=1280,
                        help="video frame height")
    parser.add_argument("--height", type=int, default=720,
                        help="video frame height")
    parser.add_argument("--fps", type=float, default=30.0,
                        help="frame rate")
    parser.add_argument("-o", "--output-dir", type=str, default="outputs",
                        help="output directory to store the circular recording")
    parser.add_argument("--segment-length", type=float, default=60.0,
                        help="length of each recording segment in [s]")
    parser.add_argument("--num-segments", type=int, default=300,
                        help="number of segments to keep circulate")
    args = parser.parse_args()

    # create output directory
    os.mkdir(args.output_dir)
    segment_path = os.path.join(args.output_dir, "segments.txt")

    # configure camera
    cam = Picamera2()
    vid_config = cam.create_video_configuration(
        controls={"FrameRate": args.fps},
        main={"size": (args.width, args.height), "format": "RGB888"}
    )
    cam.configure(vid_config)
    cam.pre_callback = overlay_timestamp

    # start camera and encoder
    encoder = H264Encoder()
    output = FileOutput()
    cam.start_recording(encoder, output)

    fileq = deque(maxlen=args.num_segments)
    while True:
        # start recording segment
        fpath = os.path.join(args.output_dir, time.strftime("vid_%Y-%m-%d_%H-%M-%S.h264"))
        output.fileoutput = fpath
        output.start()

        # delete file if necessary
        if len(fileq) == args.num_segments:
            os.remove(fileq[0])

        # update segments file
        fileq.append(fpath)
        with open(segment_path, "w") as f:
            f.writelines([f"file {fpath.split('/')[-1]}\n" for fpath in fileq])

        # wait for recording
        time.sleep(args.segment_length)
        output.stop()

    cam.stop_recording()
