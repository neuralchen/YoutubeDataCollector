#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#############################################################
# File: TextureAnalysis.py
# Created Date: Tuesday March 17th 2020
# Author: Chen Xuanhong
# Email: chenxuanhongzju@outlook.com
# Last Modified:  Wednesday, 18th March 2020 1:32:47 am
# Modified By: Chen Xuanhong
# Copyright (c) 2020 Shanghai Jiao Tong University
#############################################################

import torch
import torch.nn as nn
from torchvision import transforms as T
import cv2
import os
import numpy as np
from pathlib import Path
from json_config import write_config
import datetime

class TVLoss(nn.Module):
    def __init__(self,image_size=512):
        super(TVLoss,self).__init__()
        self.imageSizeH     = image_size[0]
        self.imageSizeW     = image_size[1]
        
    def forward(self,x):
        h_tv = torch.pow((x[:,1:,:]-x[:,:self.imageSizeH-1,:]),2).sum()
        w_tv = torch.pow((x[:,:,1:]-x[:,:,:self.imageSizeW-1]),2).sum()
        return (h_tv/self.imageSizeH+w_tv/self.imageSizeW)

class MeasureComplexity:
    def __init__(self, videos_path, sample_int=10):
        """
            videos_path: the directory to the videos
            sample_int:  sampling frames interval
        """
        self.extension  = ["mp4","avi","flv"]
        self.sample_int = 5
        self.transform  = []
        self.transform.append(T.ToTensor())
        self.transform.append(T.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)))
        self.transform  = T.Compose(self.transform)
        self.video_path = videos_path
        self.videos     = []
        self.__scanDir__()
    
    def __scanDir__(self):
        self.videos = []
        temp        = []
        for ext in self.extension:
            temp += Path(self.video_path).glob('*.%s'%ext)
        for video in temp:
            self.videos.append(video.__str__())

    def measureVideo(self, path):
        """
            measure the texture complexity of a video
            path: the path to your video
        """
        videoname   = Path(path).name
        print("\nprocessing video: %s"%path)
        cap         = cv2.VideoCapture(path)
        fps         = cap.get(cv2.CAP_PROP_FPS)
        print("video fps:%d"%fps)
        size        = (int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                        int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)))
        print("video frame size: H-%d, W-%d"%(size[0],size[1]))
        tvloss      = TVLoss(image_size=size)
        tvlist      = []
        i=0
        total_sample_frame = 0
        while(True):
            i+=1
            ret,image = cap.read()
            if ret:
                if i%self.sample_int==0:
                    total_sample_frame += 1
                    print("\r processing frame %d"%i,end='\r')
                    score = self.transform(image)
                    wocao  = tvloss(score)
                    tvlist += [wocao,]
            else:
                break
        mean = np.mean(tvlist)
        std  = np.std(tvlist)
        maxtv= np.max(tvlist)
        mintv= np.min(tvlist)
        # print("video tv mean:%.3f std:%.3f max:%.3f min:%.3f"%(mean,std,maxtv,mintv))
        cap.release()
        return {
            "video_name":   videoname,
            "total_frame":  i,
            "total_sample_frame": total_sample_frame,
            "height":       size[0],
            "width":        size[1],
            "mean_tv":      "%.3f"%mean,
            "std_tv":       "%.3f"%std,
            "max_tv":       "%.3f"%maxtv,
            "min_tv":       "%.3f"%mintv
        }
    
    def measureDir(self):
        results = []
        for item in self.videos:
            res = self.measureVideo(item)
            results.append(res)
        timeStr = datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d%H%M%S')
        json_path = os.path.join(self.video_path, "results-%s.json"%timeStr)
        write_config(json_path,results)
        

if __name__ == "__main__":
    videoPath = "D:\\Workspace\\Youtube\\downloads\\360p"
    wocao = MeasureComplexity(videoPath,200)
    wocao.measureDir()