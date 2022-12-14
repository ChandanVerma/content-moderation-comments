import os
import sys
import requests
import logging
import json
import pickle
import traceback
import tracemalloc

tracemalloc.start()

from pathlib import Path

sys.path.append(str(Path(os.getcwd()).parent))
sys.path.append(str(Path(os.getcwd())))

# loggers
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ray")
logger.setLevel("INFO")

if __name__ == "__main__":
    try:
        comment = "Podem comentar no meu lomotif?', ..., 'Q isso em ⚡️❤️"
        kinesis_event = {
            'event_time':"2022-09-20 00:17:35",
            'text':comment,
            'user_id':36359809,
            'video_id':"ce450a28-ee6c-46b8-a045-c68dc64eb17d",
            'country': "BR", 
            'video_url': "",
            'asset_type': "comment"
        }
        profile_desc = "you $Uck @$$"
        # text = "hello beautiful world"
        # text = "visit my website at www.abc.com"
        # text = "give me your whatsapp"

        kinesis_event_2 = {
            'event_time':"2022-09-20 00:17:35",
            'text':profile_desc,
            'user_id':36359809,
            'video_id':"",
            'country': "BR",
            'video_url': "",
            'asset_type': "profile"
        }
        resp_1 = requests.get("http://0.0.0.0:8000/moderate_comment", json=kinesis_event, timeout=5)
        if resp_1.status_code == 200:
            output = resp_1.json()
            logger.info("Rayserve tasks successful. Output: {}".format(output))

        else:
            logger.error(
                "Error in rayserve tasks. Status code: {} \nTraceback: {}".format(
                    resp_1.status_code, resp_1.text
                )
            )
        resp_2 = requests.get("http://0.0.0.0:8000/moderate_profile_desc", json=kinesis_event_2, timeout=5)
        if resp_2.status_code == 200:
            output = resp_2.json()
            logger.info("Rayserve tasks successful. Output: {}".format(output))

        else:
            logger.error(
                "Error in rayserve tasks. Status code: {} \nTraceback: {}".format(
                    resp_2.status_code, resp_2.text
                )
            )
    except:
        assert False, logger.error(
            "Lomotif could not be processed due to: {}. \nTraceback: {}".format(
                traceback.format_exc()
            )
        )
