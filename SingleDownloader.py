#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#############################################################
# File: SingleDownloader.py
# Created Date: Sunday August 16th 2020
# Author: Chen Xuanhong
# Email: chenxuanhongzju@outlook.com
# Last Modified:  Sunday, 16th August 2020 3:10:29 pm
# Modified By: Chen Xuanhong
# Copyright (c) 2020 Shanghai Jiao Tong University
#############################################################


from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import socks
import socket
from   json_config import write_config
import datetime
import os
import youtube_dl
import shutil
 
class YoutubeSpider:
    """YoutubeSpider class.
    YoutubeSpide is designed to search and download video from youtube.com.
    Parameters list of the object constructor:
    google_api_info:      this param must be a dict:
                        {
                            "DEVELOPER_KEY"             : "the developer key",
                            "YOUTUBE_API_SERVICE_NAME"  : "youtube",
                            "YOUTUBE_API_VERSION"       : "v3"
                        }
    max_res_per_page:   max results number in per result page
    download:           whether to download the results
    download_dir:       The directory to save the videos
    proxy:              this is the proxy dict, if you do not use a proxy just ignore it
                        {
                            "proxy_server"  : "127.0.0.1",
                            "username"      : "hehe",
                            "passwd"        : "ohuo",
                            "port"          : "1080"
                        }
    """
    def __init__(self, google_api_info, max_res_per_page=50, download=False, download_dir=None, proxy=None):
    
        self.DEVELOPER_KEY              = google_api_info["DEVELOPER_KEY"]
        self.YOUTUBE_API_SERVICE_NAME   = google_api_info["YOUTUBE_API_SERVICE_NAME"]
        self.YOUTUBE_API_VERSION        = google_api_info["YOUTUBE_API_VERSION"]
        self.max                        = max_res_per_page
        self.url_preffix                = "https://www.youtube.com/watch?v="
        self.res_json_path              = "./result_json"
        self.download                   = download
        # self.proxy_str                  = r"%s:%s@%s:%d"%(proxy["username"],proxy["passwd"],proxy["proxy_server"],proxy["port"])
        # self.proxy_str                  = r"%s:%d"%(proxy["proxy_server"],proxy["port"])#socks5://username:password@hostname:port
        self.proxy_str                  = "https://%s:%s@%s:%d/"%(proxy["username"],proxy["passwd"],proxy["proxy_server"],proxy["port"])
        self.proxy_username             = proxy["username"]
        self.proxy_passwd               = proxy["passwd"]
        self.proxy_url                  = proxy["proxy_server"]
        self.proxy_port                 = proxy["port"]
        self.google_ok                  = False
        if download_dir is None:
            download_dir = "./downloads"
        self.download_dir          = os.path.join(download_dir,"videos")
        if download:
            if not os.path.exists(self.download_dir):
                os.makedirs(self.download_dir)

        if not os.path.exists(self.res_json_path ):
            os.makedirs(self.res_json_path )

        if proxy:
            print("Need a proxy!")
            socks.setdefaultproxy(
                    socks.PROXY_TYPE_HTTP,
                    # socks.PROXY_TYPE_SOCKS4,
                    proxy["proxy_server"],
                    proxy["port"],
                    username=proxy["username"],
                    password=proxy["passwd"]
                    )
            socket.socket = socks.socksocket
        try:
            self.youtube = build(self.YOUTUBE_API_SERVICE_NAME, self.YOUTUBE_API_VERSION,
                        developerKey=self.DEVELOPER_KEY)
            self.google_ok = True
            print("Success to build the youtube data api!")
        except:
            self.google_ok = False
            print("Failed to build the youtube data api!")
            
    
    def Download(self, video_url):
        format_flag = 0
        socks.setdefaultproxy()
        socket.socket = socks.socksocket
        # ydl_opt = ({'proxy':self.proxy_str})#geo_verification_proxy   
        ydl_opt = ({
            "proxy":self.proxy_str
            })
        video_url = video_url
        with youtube_dl.YoutubeDL(ydl_opt) as ydl:
            # ydl.download([video_url])
            try:
                info_dict = ydl.extract_info(video_url, download=False)
                wocao = info_dict["formats"]
                format_flag = 0
                timeStr = datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d%H%M%S')
                write_config(os.path.join(self.res_json_path, "nimabi-%s.json"%timeStr),wocao)
                for temp in wocao:
                    if temp["format_id"] == "137":
                        format_flag +=1
                        video_tile = info_dict["title"]
            except Exception as err:
                print(err)
                print("Failed to download this video!")
                format_flag = 0
                
            if format_flag == 1:
                print("The video contains 1080p!")
                # ydl_opt = ({'format_id':'137','proxy':self.proxy_str,'outtmpl':r"%(id)s.%(ext)s"})
                ydl_opt = ({'format':'137',
                            'outtmpl':r"%(id)s.%(ext)s",
                            "proxy":self.proxy_str,
                            "writesubtitles": True
                        })
                with youtube_dl.YoutubeDL(ydl_opt) as ydl:
                    print("download 1080p video...")
                    try:
                        ydl.download([video_url])
                        shutil.move("./"+video_url+".mp4",self.download_dir)
                    except Exception as err:
                        print(err)
                        print("Failed to download this video!")
 
if __name__ == '__main__':
    google_info = {
        "DEVELOPER_KEY"             : "AIzaSyAWZRNt9ne-Xm-55snzLeYtYLsS19NjkLY",
        "YOUTUBE_API_SERVICE_NAME"  : "youtube",
        "YOUTUBE_API_VERSION"       : "v3"
    }
    # use the huawei proxy
    proxy_info = {
        "proxy_server"  : "202.120.39.161",
        "username"      : "sjtulab",
        "passwd"        : "sjtulab",
        "port"          : 8888
    }
    # proxy_info = {
    #     "proxy_server"  : "127.0.0.1",
    #     "username"      : "",
    #     "passwd"        : "",
    #     "port"          : 1080
    # }
    wocao = YoutubeSpider(google_info,50,True,proxy=proxy_info)
    wocao.Download("o12KsNmoMhQ")