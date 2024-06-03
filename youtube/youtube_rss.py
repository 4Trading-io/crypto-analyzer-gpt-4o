import feedparser
import json
import logging
import time
import asyncio
from threading import Thread
from typing import Callable, Coroutine

logging.basicConfig(level=logging.INFO)

class YoutubeFeedParser:
    
    channel_id: str
    cache_filename: str
    processed_videos_filename: str
    last_video_id: str | None
    processed_videos: set
    thread: Thread
    
    def __init__(self, channel_id: str) -> None:
        self.channel_id = channel_id
        self.cache_filename = f"cache/youtube_rss_feed_parser_{channel_id}.json"
        self.processed_videos_filename = f"cache/processed_videos_{channel_id}.json"
        self.last_video_id = None
        self.processed_videos = set()
        self.thread = None
        self._load_last_video_id()
        self._load_processed_videos()
        
    def _load_last_video_id(self):
        try:
            with open(self.cache_filename, "r") as f:
                last_video = json.load(f)
                self.last_video_id = last_video['id']
        except FileNotFoundError:
            logging.info(f"No cache file found for channel {self.channel_id}. Starting fresh.")
        except BaseException as ex:
            logging.warning(f"Could not load last video ID: {ex}")
    
    def _load_processed_videos(self):
        try:
            with open(self.processed_videos_filename, "r") as f:
                self.processed_videos = set(json.load(f))
        except FileNotFoundError:
            logging.info(f"No processed videos file found for channel {self.channel_id}. Starting fresh.")
        except BaseException as ex:
            logging.warning(f"Could not load processed videos: {ex}")
    
    def _save_last_video_id(self, latest_video):
        try:
            with open(self.cache_filename, "w") as f:
                json.dump(latest_video, f, indent=4)
        except BaseException as ex:
            logging.warning(f"Could not save new RSS: {ex}")
    
    def _save_processed_videos(self):
        try:
            with open(self.processed_videos_filename, "w") as f:
                json.dump(list(self.processed_videos), f, indent=4)
        except BaseException as ex:
            logging.warning(f"Could not save processed videos: {ex}")

    def check(self):
        feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}")
        if feed.entries:
            latest_video = feed.entries[0]
            video_id = latest_video.id
            
            if video_id != self.last_video_id and video_id not in self.processed_videos:
                self.last_video_id = video_id
                self.processed_videos.add(video_id)
                logging.info(f"New Feed received from {self.channel_id}: {latest_video.title}")
                self._save_last_video_id(latest_video)
                self._save_processed_videos()
                return latest_video
        return None

    def check_always(self, callback: Callable[[object], None]) -> Thread:
        
        def thread_loop():
            logging.info(f"Start checking YouTube channel {self.channel_id}")
            while True:
                try:
                    x = self.check()
                    if x: callback(x)
                except (InterruptedError, KeyboardInterrupt):
                    break
                except BaseException as e:
                    logging.exception(f"During YouTube Parser check something happened: ({str(e)})")
                
                try:
                    time.sleep(60)
                except BaseException as e:
                    break
            logging.info(f"Stop checking YouTube channel {self.channel_id}")
        self.thread = Thread(target=thread_loop, name=f"feed_reader_{self.channel_id}", daemon=False)
        self.thread.start()
        return self.thread
    
    async def check_always_async(self, callback: Callable[[object], None]) -> Coroutine:
        
        logging.info(f"Start checking YouTube channel {self.channel_id}")
        while True:
            try:
                x = self.check()
                if x: 
                    await callback(x)
            except (InterruptedError, KeyboardInterrupt):
                break
            except BaseException as e:
                logging.exception(f"During YouTube Parser check something happened: ({str(e)})")
            
            try:
                await asyncio.sleep(60)
            except BaseException as e:
                break
        logging.info(f"Stop checking YouTube channel {self.channel_id}")

def test():
    
    def on_new_video(video):
        print(f"""New Video Received,
              Title: {video.title}
              Link: {video.link}
              """)
    thread = YoutubeFeedParser().check_always(on_new_video)
    thread.join()

def test_async():
    
    async def on_new_video(video):
        print(f"""New Video Received,
              Title: {video.title}
              Link: {video.link}
              """)
        
    async def main():
        fp = YoutubeFeedParser()
        await asyncio.gather(fp.check_always_async(on_new_video))
        
    asyncio.run(main())