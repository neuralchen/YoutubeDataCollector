#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#############################################################
# File: YoutubeSpider.py
# Created Date: Sunday March 15th 2020
# Author: Chen Xuanhong
# Email: chenxuanhongzju@outlook.com
# Last Modified:  Thursday, 19th March 2020 2:49:30 pm
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
        self.proxy_str                  = "socks5://%s:%s@%s:%d/"%(proxy["username"],proxy["passwd"],proxy["proxy_server"],proxy["port"])
        self.proxy_username             = proxy["username"]
        self.proxy_passwd               = proxy["passwd"]
        self.proxy_url                  = proxy["proxy_server"]
        self.proxy_port                 = proxy["port"]
        self.google_ok                  = False
        if download_dir is None:
            download_dir = "./downloads"
        self.download_dir_360p          = os.path.join(download_dir,"360p")
        self.download_dir_1080p          = os.path.join(download_dir,"1080p")
        if download:
            if not os.path.exists(self.download_dir_360p):
                os.makedirs(self.download_dir_360p)
            if not os.path.exists(self.download_dir_1080p):
                os.makedirs(self.download_dir_1080p)

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

    def youtube_search(self, query_str, max_res):
        """
            query_str:  the key word to search in the youtube.com
            max_res:    maximum results number
        """
        if not self.google_ok:
            print("Can not continue to process since the google api build failed!")
            return
        youtube = self.youtube
        print("start to search.....")
        res_json_list = []
        total_results = 0
        request_body = youtube.search().list(
            q=query_str,
            part='id,snippet',
            maxResults=self.max
            )
        search_response = request_body.execute()
        res_json_list   = search_response["items"]
        print("results page 1 finished")
        total_results   = len(search_response["items"])
        page_num = 1 
        if total_results < max_res:
            while(total_results<max_res):
                request_body = youtube.search().list_next(request_body,search_response)
                search_response = request_body.execute()
                res_json_list   += search_response["items"]
                total_results   += len(search_response["items"])
                page_num += 1
                print("results page %d finished"%page_num)
        else:
            res_json_list = res_json_list[:max_res]
        self.__process_results__(res_json_list)
        print("Finish to process all results!")

    def __process_results__(self,res_list):
        videos = []
        for item in res_list:
            if item['id']['kind'] == 'youtube#video':
                if item['snippet']['liveBroadcastContent'] != 'live':
                    video_json = {
                        "title"         : item['snippet']['title'],
                        "description"   : item['snippet']['description'],
                        "url"           : self.url_preffix+item['id']['videoId'],
                        "id"            : item['id']['videoId']
                    }   

                    videos.append(video_json)
            else:
                print("ignore live program!")
                
        
        timeStr = datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d%H%M%S')
        write_config(os.path.join(self.res_json_path, "results-%s.json"%timeStr),videos)
        print("save results list successfully!")
        if self.download:
            print("Start to download the results")
            self.__download__(videos)
            
    
    def __download__(self, res_list):
        format_flag = 0
        socks.setdefaultproxy()
        socket.socket = socks.socksocket
        for item in res_list:
            # ydl_opt = ({'proxy':self.proxy_str})#geo_verification_proxy   
            ydl_opt = ({
                # "proxy":self.proxy_str
             })
            video_url = item["url"]
            with youtube_dl.YoutubeDL(ydl_opt) as ydl:
                # ydl.download([video_url])
                try:
                    info_dict = ydl.extract_info(video_url, download=False)
                    wocao = info_dict["formats"]
                    format_flag = 0
                    for temp in wocao:
                        if temp["format_id"] == "134":
                            format_flag +=1
                        elif temp["format_id"] == "137":
                            format_flag +=1
                except Exception as err:
                    print(err)
                    print("Failed to download this video!")
                    format_flag = 0
                
            if format_flag == 2:
                print("The video contains 1080p and 360p!")
                # ydl_opt = ({'format_id':'134','proxy':self.proxy_str,'outtmpl':r"%(id)s.%(ext)s"})
                ydl_opt = ({'format_id':'134','outtmpl':r"%(id)s.%(ext)s"})
                with youtube_dl.YoutubeDL(ydl_opt) as ydl:
                    print("download 360p video...")
                    try:
                        ydl.download([video_url])
                        shutil.move("./"+item["id"]+".mp4",self.download_dir_360p)
                    except Exception as err:
                        print(err)
                        print("Failed to download this video!")
                # ydl_opt = ({'format_id':'137','proxy':self.proxy_str,'outtmpl':r"%(id)s.%(ext)s"})
                ydl_opt = ({'format_id':'137','outtmpl':r"%(id)s.%(ext)s"})
                with youtube_dl.YoutubeDL(ydl_opt) as ydl:
                    print("download 1080p video...")
                    try:
                        ydl.download([video_url])
                        shutil.move("./"+item["id"]+".mp4",self.download_dir_1080p)
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
    wocao.youtube_search("NASA",8)