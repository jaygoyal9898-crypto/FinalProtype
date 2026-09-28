import argparse
from .pipeline import process_video

def main():
    p=argparse.ArgumentParser(); p.add_argument('--video',required=True); p.add_argument('--conf',type=float,default=.30); a=p.parse_args(); aid,s=process_video(a.video,conf=a.conf); print({'analysis_id':aid,**s})
if __name__=='__main__': main()
