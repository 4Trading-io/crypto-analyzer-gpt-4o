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
    last_video_id: str | None
    thread: Thread
    
    def __init__(self, channel_id: str) -> None:
        self.channel_id = channel_id
        self.cache_filename = f"cache/youtube_rss_feed_parser_{channel_id}.json"
        self.last_video_id = None
        self.thread = None
        try:
            with open(self.cache_filename,"r") as f:
                last_video = json.load(f)
                self.last_video_id = last_video['id']
        except BaseException as ex:
            logging.info(f"could not load elder rss: {ex}")
        
        # if self.last_video_id is None:
        #     self.check()
    
    def check(self):
        feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}")
        if feed.entries:
            latest_video = feed.entries[0]
            
            video_id = latest_video.id
            
            if video_id != self.last_video_id:
                self.last_video_id = video_id
                logging.info(f"New Feed received from {self.channel_id} : {latest_video.title}")
                try:
                    with open(self.cache_filename,"w") as f:
                        json.dump(latest_video, f, indent=4)
                except BaseException as ex:
                    logging.warning(f"could not save new rss: {ex}")    
                return latest_video
        return None

    def check_always(self, callback: Callable[[object], None]) -> Thread:
        
        def thread_loop():
            logging.info(f"Start checking youtube channel {self.channel_id}")
            while True:
                try:
                    x = self.check()
                    if x: callback(x)
                except (InterruptedError, KeyboardInterrupt):
                    break
                except BaseException as e:
                    logging.exception(f"During Youtube Parser check something happened: ({str(e)})")
                
                try:
                    time.sleep(60)
                except BaseException as e:
                    break
            logging.info(f"Stop checking youtube channel {self.channel_id}")
        self.thread = Thread(target=thread_loop, name=f"feed_reader_{self.channel_id}", daemon=False)
        self.thread.start()
        return self.thread
    
    async def check_always_async(self, callback: Callable[[object], None]) -> Coroutine:
        
        logging.info(f"Start checking youtube channel {self.channel_id}")
        while True:
            try:
                x = self.check()
                if x: 
                    await callback(x)
            except (InterruptedError, KeyboardInterrupt):
                break
            except BaseException as e:
                logging.exception(f"During Youtube Parser check something happened: ({str(e)})")
            
            try:
                await asyncio.sleep(60)
            except BaseException as e:
                break
        logging.info(f"Stop checking youtube channel {self.channel_id}")

def test():
    
    def on_new_video(video):
        print(f"""New Video Received,
              Title: {video.title}
              Link: {video.link}
              """)
    thread = YoutubeFeedParser("UCGWSVnCaJOiKlOSpK8SSqbg").check_always(on_new_video)
    thread.join()

def test_async():
    
    async def on_new_video(video):
        print(f"""New Video Received,
              Title: {video.title}
              Link: {video.link}
              """)
        
    async def main():
        fp = YoutubeFeedParser("UCGWSVnCaJOiKlOSpK8SSqbg")
        await asyncio.gather(fp.check_always_async(on_new_video))
        
    asyncio.run(main())

# test_async()
# test()
    
            