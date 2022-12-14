import os

os.environ["TRANSFORMERS_CACHE"] = "../models"
import sys
import pandas as pd
import logging
import traceback
import requests
import shutil
import time
import ray
import json
import boto3
import torch

torch.hub.set_dir("./models")

from ray import serve
from pathlib import Path

sys.path.append(str(Path(os.getcwd()).parent))
sys.path.append(str(Path(os.getcwd())))

from src.utils.data_processing import (
    is_promotion,
    is_leet_speak_profanity,
    process_text,
    remove_emoji,
    map_pred_to_result,
    translate_to_en,
    lang_detect,
)
from src.utils.download_models import download_models_helper
from src.utils.generate_outputs import output_template
from detoxify import Detoxify
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# from dotenv import load_dotenv

# load_dotenv("./.env")

# loggers
logger = logging.getLogger("ray")
logger.setLevel("INFO")

LANG_IN_SCOPE = ["en", "it", "fr", "pt", "es"]


@serve.deployment(
    max_concurrent_queries=os.environ["ProcessMaxCon"],
    num_replicas=os.environ["ProcessNumReplicas"],
    ray_actor_options={
        "num_cpus": float(os.environ["ProcessNumCPUPerReplica"]),
    },
)
class ProcessTextServe:
    def __init__(
        self,
    ):
        pass

    def __call__(self, text):
        """Detect language of text and clean text by removing emojis \
        and non-alphabetic symbols.

        Args:
            text (str): text to moderate

        Returns:
            tuple: language detected (str), original input text (str), \
            text without emojis (str), text without emojis and symbols (str), \
            time in seconds for this step (float)
        """
        start = time.time()
        try:
            text_noemoji = remove_emoji(text)
            text_clean = process_text(text_noemoji)
            lang = lang_detect(text_clean)
        except Exception as e:
            lang, text_noemoji, text_clean = "", "", ""
            self.logger.error(e, "\n Traceback: \n{}".format(traceback.format_exc()))

        process_duration = time.time() - start

        return lang, text, text_noemoji, text_clean, process_duration


@serve.deployment(
    max_concurrent_queries=os.environ["PromotionMaxCon"],
    num_replicas=os.environ["PromotionNumReplicas"],
    ray_actor_options={
        "num_cpus": float(os.environ["PromotionNumCPUPerReplica"]),
    },
)
class PromotionDetectServe:
    def __init__(
        self,
    ):
        pass

    def __call__(self, lang, text):
        """Detect if there are URLs, emails in text or if the text is very long \
        and may be spammy.

        Args:
            lang (str): language of text detected
            text (str): text to moderate
        Returns:
            tuple: True if email is present else False (bool), \
            True if URL is present else False (bool), True if text is \
            too long else False (bool), time taken in seconds for this step (float)
        """
        start = time.time()
        if lang in LANG_IN_SCOPE:
            is_email, is_url, is_long = is_promotion(text, length_threshold=150)
        else:
            is_email, is_url, is_long = False, False, False

        promo_duration = time.time() - start

        return is_email, is_url, is_long, promo_duration


@serve.deployment(
    max_concurrent_queries=os.environ["LeetMaxCon"],
    num_replicas=os.environ["LeetNumReplicas"],
    ray_actor_options={
        "num_cpus": float(os.environ["LeetNumCPUPerReplica"]),
    },
)
class LeetDetectServe:
    def __init__(
        self,
    ):
        pass

    def __call__(self, lang, text_noemoji):
        """Detect if leetspeak profanity is present.

        Args:
            lang (str): language of text detected
            text_noemoji (str): text without emojis

        Returns:
            tuple: True if leetspeak profanity is present else False (bool), \
            time taken in seconds for this step (float)
        """
        start = time.time()
        if lang in LANG_IN_SCOPE:
            is_leetspeak_profanity = is_leet_speak_profanity(text_noemoji)
        else:
            is_leetspeak_profanity = False

        leet_duration = time.time() - start

        return is_leetspeak_profanity, leet_duration


@serve.deployment(
    max_concurrent_queries=os.environ["ModerateMaxCon"],
    num_replicas=os.environ["ModerateNumReplicas"],
    ray_actor_options={
        "num_cpus": float(os.environ["ModerateNumCPUPerReplica"]),
        "num_gpus": float(os.environ["ModerateNumGPUPerReplica"]),
    },
)
class ModerateTextServe:
    def __init__(self):
        try:
            logger.info("Downloading models from S3...")
            download_models_helper(root="./models")
            logger.info("All model files downloaded.")
            self.tokenizer = AutoTokenizer.from_pretrained(
                "Helsinki-NLP/opus-mt-ROMANCE-en", cache_dir="./models"
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                "Helsinki-NLP/opus-mt-ROMANCE-en", cache_dir="./models"
            ).to("cuda")
            self.en_m = Detoxify(
                model_type="original",
                checkpoint="./models/checkpoints/toxic_original-c1212f89.ckpt",
                device="cuda",
            )
            self.pt_m = Detoxify(
                model_type="multilingual",
                checkpoint="./models/checkpoints/multilingual_debiased-0b549669.ckpt",
                device="cuda",
            )
            self.sqs_client = boto3.client("sqs")

            if "de" in LANG_IN_SCOPE:
                self.de_tokenizer = None
                self.de_model = None

            self.max_trans_len = 150
            self.to_translate = True
            self.romance_lang = [
                "ca",
                "an",
                "la",
                "pt",
                "lij",
                "rm",
                "lmo",
                "gl",
                "it",
                "vec",
                "fr",
                "fur",
                "co",
                "scn",
                "mwl",
                "oc",
                "sc",
                "frp",
                "nap",
                "lad",
                "es",
                "lld",
                "ro",
                "wa",
            ]

        except Exception as e:
            logger.error(e, "\n Traceback: \n{}".format(traceback.format_exc()))
            assert False  # force quit the script

    def __call__(self, lang, text_clean):
        """Run detoxify profanity detection here.

        Args:
            lang (str): language of text detected
            text_clean (str): text without emojis and symbols

        Returns:
            tuple: True if profanity is detected else False (bool), \
            time taken in seconds for this step (float), translated text \
            if language detected is not English (str)
        """
        start = time.time()
        trans = ""
        if lang in LANG_IN_SCOPE:
            if len(text_clean) != 0:
                if lang == "en":
                    # if len(text_clean) <= self.max_trans_len:
                    #     trans = translate_to_en(
                    #         text_clean, self.tokenizer, self.model
                    #     )  # has a cap in length
                    #     model_pred = self.en_m.predict([trans])
                    # else:
                    model_pred = self.en_m.predict([text_clean])

                elif lang in ["it", "fr", "pt", "es"]:
                    model_pred = self.pt_m.predict([text_clean])

                    if self.to_translate and len(text_clean) <= self.max_trans_len:
                        trans = translate_to_en(text_clean, self.tokenizer, self.model)
                elif lang == "de":
                    if len(text_clean) <= self.max_trans_len:
                        trans = translate_to_en(
                            text_clean, self.de_tokenizer, self.de_model
                        )  # translation model has a cap in length
                        model_pred = self.en_m.predict([trans])
                    else:
                        model_pred = None

                elif lang in self.romance_lang:
                    if len(text_clean) <= self.max_trans_len:
                        trans = translate_to_en(
                            text_clean, self.tokenizer, self.model
                        )  # translation model has a cap in length
                        model_pred = self.en_m.predict([trans])
                    else:
                        model_pred = None

            else:
                model_pred = None

        else:
            model_pred = None
            model_duration = -1

        model_duration = time.time() - start

        return model_pred, model_duration, trans


@serve.deployment(
    route_prefix="/moderate_comment",
    max_concurrent_queries=os.environ["CombineMaxCon"],
    num_replicas=os.environ["CombineNumReplicas"],
    ray_actor_options={
        "num_cpus": float(os.environ["CombineNumCPUPerReplica"]),
    },
)
class CommentModerateModel:
    def __init__(
        self,
    ):
        try:
            self.process_text = ProcessTextServe.get_handle(sync=False)
            self.model_promo = PromotionDetectServe.get_handle(sync=False)
            self.model_leet = LeetDetectServe.get_handle(sync=False)
            self.model_text = ModerateTextServe.get_handle(sync=False)
            self.sqs_client = boto3.client("sqs")
        except Exception as e:
            logger.error(e, "\n Traceback: \n{}".format(traceback.format_exc()))
            assert False  # force quit the script

    async def __call__(self, starlette_request):
        logger.info("Message received.")
        try:
            start = time.time()
            kinesis_event = await starlette_request.json()
            message_receive_time = pd.Timestamp.utcnow()
            outputs = output_template(kinesis_event, message_receive_time)
            text_id = "{}".format(kinesis_event["user_id"])
            text = kinesis_event["text"]

            (lang, text, text_noemoji, text_clean, process_duration) = await (
                await self.process_text.remote(text)
            )
            logger.info("[{}] Text processed. Language: {}".format(text_id, lang))
            if lang in LANG_IN_SCOPE:
                is_email, is_url, is_long, promotion_duration = await (
                    await self.model_promo.remote(lang, text)
                )
                logger.info("[{}] Checked for spam and promotions.".format(text_id))
                is_leetspeak_profanity, leet_duration = await (
                    await self.model_leet.remote(lang, text_noemoji)
                )
                logger.info("[{}] Checked for leet profanity.".format(text_id))
                model_pred, model_duration, trans = await (
                    await self.model_text.remote(lang, text_clean)
                )
                logger.info("[{}] Checked for other NSFW content.".format(text_id))

                if model_pred is not None:
                    pred, prob = map_pred_to_result(model_pred)
                    outputs["MODEL_ATTRIBUTES"]["STATUS"] = 0
                else:
                    pred = True
                    prob = -1
                    outputs["MODEL_ATTRIBUTES"]["STATUS"] = 1

                outputs["MODEL_ATTRIBUTES"]["COMBINE_DURATION"] = round(
                    time.time() - start, 2
                )
                if is_email or is_url or is_long or is_leetspeak_profanity or pred:
                    outputs["TO_BE_MODERATED"] = True

                outputs["MODEL_ATTRIBUTES"]["IS_EMAIL"] = is_email
                outputs["MODEL_ATTRIBUTES"]["IS_URL"] = is_url
                outputs["MODEL_ATTRIBUTES"]["IS_LONG"] = is_long
                outputs["MODEL_ATTRIBUTES"][
                    "IS_LEETSPEAK_PROFANITY"
                ] = is_leetspeak_profanity
                outputs["MODEL_ATTRIBUTES"]["AI_PREDICTION"] = pred
                outputs["MODEL_ATTRIBUTES"]["AI_PROBABILITY"] = round(prob, 3)
                outputs["MODEL_ATTRIBUTES"]["MODEL_DURATION"] = round(model_duration, 2)
                outputs["MODEL_ATTRIBUTES"]["LEET_DURATION"] = round(leet_duration, 2)
                outputs["MODEL_ATTRIBUTES"]["PROMOTION_DURATION"] = round(
                    promotion_duration, 2
                )
                outputs["MODEL_ATTRIBUTES"]["PROCESS_DURATION"] = round(
                    process_duration, 2
                )
                outputs["MODEL_ATTRIBUTES"]["TRANSLATED_TO_EN"] = trans

                outputs["MODEL_ATTRIBUTES"]["TOTAL_DURATION"] = round(
                    (pd.Timestamp.utcnow() - message_receive_time).total_seconds(), 2
                )

            elif len(lang) == 0:
                outputs["TO_BE_MODERATED"] = True
                outputs["MODEL_ATTRIBUTES"]["STATUS"] = 2

            outputs["MESSAGE_RECEIVE_TIME"] = str(outputs["MESSAGE_RECEIVE_TIME"])
            outputs["MODEL_ATTRIBUTES"]["LANG"] = lang

            # Send message to SQS queue
            logger.info(
                "[{}] Attempting to send output to SQS: {}.".format(
                    text_id, os.environ["SnowflakeResultsQueue"]
                )
            )
            msg = json.dumps(outputs)
            response = self.sqs_client.send_message(
                QueueUrl=os.environ["SnowflakeResultsQueue"],
                DelaySeconds=0,
                MessageBody=msg,
            )
            logger.info(
                "[{}] Sent outputs to SQS: {}.".format(
                    text_id, os.environ["SnowflakeResultsQueue"]
                )
            )

        except Exception as e:
            outputs["MESSAGE_RECEIVE_TIME"] = str(outputs["MESSAGE_RECEIVE_TIME"])
            outputs["TO_BE_MODERATED"] = True
            outputs["MODEL_ATTRIBUTES"]["STATUS"] = 3
            logger.error(e, "\n Traceback: \n{}".format(traceback.format_exc()))

            # Send message to SQS queue
            logger.info(
                "[{}] Attempting to send output to SQS: {}.".format(
                    text_id, os.environ["SnowflakeResultsQueue"]
                )
            )
            msg = json.dumps(outputs)
            response = self.sqs_client.send_message(
                QueueUrl=os.environ["SnowflakeResultsQueue"],
                DelaySeconds=0,
                MessageBody=msg,
            )
            logger.info(
                "[{}] Sent outputs to SQS: {}.".format(
                    text_id, os.environ["SnowflakeResultsQueue"]
                )
            )

        return outputs

@serve.deployment(
    route_prefix="/moderate_profile_desc",
    max_concurrent_queries=os.environ["CombineMaxCon"],
    num_replicas=os.environ["CombineNumReplicas"],
    ray_actor_options={
        "num_cpus": float(os.environ["CombineNumCPUPerReplica"]),
    },
)
class ProfileModerateModel:
    def __init__(
        self,
    ):
        try:
            self.process_text = ProcessTextServe.get_handle(sync=False)
            self.model_promo = PromotionDetectServe.get_handle(sync=False)
            self.model_leet = LeetDetectServe.get_handle(sync=False)
            self.model_text = ModerateTextServe.get_handle(sync=False)
            self.sqs_client = boto3.client("sqs")
        except Exception as e:
            logger.error(e, "\n Traceback: \n{}".format(traceback.format_exc()))
            assert False  # force quit the script

    async def __call__(self, starlette_request):
        logger.info("Message received.")
        try:
            start = time.time()
            kinesis_event = await starlette_request.json()
            message_receive_time = pd.Timestamp.utcnow()
            outputs = output_template(kinesis_event, message_receive_time)
            text_id = "{}".format(kinesis_event["user_id"])
            text = kinesis_event["text"]

            (lang, text, text_noemoji, text_clean, process_duration) = await (
                await self.process_text.remote(text)
            )
            logger.info("[{}] Text processed. Language: {}".format(text_id, lang))
            if lang in LANG_IN_SCOPE:
                is_email, is_url, is_long, promotion_duration = await (
                    await self.model_promo.remote(lang, text)
                )
                logger.info("[{}] Checked for spam and promotions.".format(text_id))
                is_leetspeak_profanity, leet_duration = await (
                    await self.model_leet.remote(lang, text_noemoji)
                )
                logger.info("[{}] Checked for leet profanity.".format(text_id))
                model_pred, model_duration, trans = await (
                    await self.model_text.remote(lang, text_clean)
                )
                logger.info("[{}] Checked for other NSFW content.".format(text_id))

                if model_pred is not None:
                    pred, prob = map_pred_to_result(model_pred)
                    outputs["MODEL_ATTRIBUTES"]["STATUS"] = 0
                else:
                    pred = True
                    prob = -1
                    outputs["MODEL_ATTRIBUTES"]["STATUS"] = 1

                outputs["MODEL_ATTRIBUTES"]["COMBINE_DURATION"] = round(
                    time.time() - start, 2
                )
                if is_email or is_url or is_long or is_leetspeak_profanity or pred:
                    outputs["TO_BE_MODERATED"] = True

                outputs["MODEL_ATTRIBUTES"]["IS_EMAIL"] = is_email
                outputs["MODEL_ATTRIBUTES"]["IS_URL"] = is_url
                outputs["MODEL_ATTRIBUTES"]["IS_LONG"] = is_long
                outputs["MODEL_ATTRIBUTES"][
                    "IS_LEETSPEAK_PROFANITY"
                ] = is_leetspeak_profanity
                outputs["MODEL_ATTRIBUTES"]["AI_PREDICTION"] = pred
                outputs["MODEL_ATTRIBUTES"]["AI_PROBABILITY"] = round(prob, 3)
                outputs["MODEL_ATTRIBUTES"]["MODEL_DURATION"] = round(model_duration, 2)
                outputs["MODEL_ATTRIBUTES"]["LEET_DURATION"] = round(leet_duration, 2)
                outputs["MODEL_ATTRIBUTES"]["PROMOTION_DURATION"] = round(
                    promotion_duration, 2
                )
                outputs["MODEL_ATTRIBUTES"]["PROCESS_DURATION"] = round(
                    process_duration, 2
                )
                outputs["MODEL_ATTRIBUTES"]["TRANSLATED_TO_EN"] = trans

                outputs["MODEL_ATTRIBUTES"]["TOTAL_DURATION"] = round(
                    (pd.Timestamp.utcnow() - message_receive_time).total_seconds(), 2
                )

            elif len(lang) == 0:
                outputs["TO_BE_MODERATED"] = True
                outputs["MODEL_ATTRIBUTES"]["STATUS"] = 2

            outputs["MESSAGE_RECEIVE_TIME"] = str(outputs["MESSAGE_RECEIVE_TIME"])
            outputs["MODEL_ATTRIBUTES"]["LANG"] = lang

            # Send message to SQS queue
            logger.info(
                "[{}] Attempting to send output to SQS: {}.".format(
                    text_id, os.environ["SnowflakeProfileResultsQueue"]
                )
            )
            msg = json.dumps(outputs)
            response = self.sqs_client.send_message(
                QueueUrl=os.environ["SnowflakeProfileResultsQueue"],
                DelaySeconds=0,
                MessageBody=msg,
            )
            logger.info(
                "[{}] Sent outputs to SQS: {}.".format(
                    text_id, os.environ["SnowflakeProfileResultsQueue"]
                )
            )

        except Exception as e:
            outputs["MESSAGE_RECEIVE_TIME"] = str(outputs["MESSAGE_RECEIVE_TIME"])
            outputs["TO_BE_MODERATED"] = True
            outputs["MODEL_ATTRIBUTES"]["STATUS"] = 3
            logger.error(e, "\n Traceback: \n{}".format(traceback.format_exc()))

            # Send message to SQS queue
            logger.info(
                "[{}] Attempting to send output to SQS: {}.".format(
                    text_id, os.environ["SnowflakeProfileResultsQueue"]
                )
            )
            msg = json.dumps(outputs)
            response = self.sqs_client.send_message(
                QueueUrl=os.environ["SnowflakeProfileResultsQueue"],
                DelaySeconds=0,
                MessageBody=msg,
            )
            logger.info(
                "[{}] Sent outputs to SQS: {}.".format(
                    text_id, os.environ["SnowflakeProfileResultsQueue"]
                )
            )

        return outputs


if __name__ == "__main__":
    env_vars = {
        "AWS_ROLE_ARN": os.environ.get("AWS_ROLE_ARN"),
        "AWS_WEB_IDENTITY_TOKEN_FILE": os.environ.get("AWS_WEB_IDENTITY_TOKEN_FILE"),
        "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION"),
        "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY"),
        "AiModelBucket": os.environ.get("AiModelBucket"),
        "SnowflakeResultsQueue": os.environ["SnowflakeResultsQueue"],
        "SnowflakeProfileResultsQueue": os.environ["SnowflakeProfileResultsQueue"],
        "TRANSFORMERS_CACHE": os.environ["TRANSFORMERS_CACHE"],
    }
    runtime_env = {"env_vars": {}}

    for key, value in env_vars.items():
        if value is not None:
            runtime_env["env_vars"][key] = value

    ray.init(address="auto", namespace="serve", runtime_env=runtime_env)
    serve.start(detached=True, http_options={"host": "0.0.0.0"})

    logger.info("The environment variables in rayserve are: {}".format(runtime_env))
    logger.info("All variables are: {}".format(env_vars))

    logger.info("Starting rayserve server.")
    logger.info("Deploying modules.")

    ProcessTextServe.deploy()
    PromotionDetectServe.deploy()
    LeetDetectServe.deploy()
    ModerateTextServe.deploy()
    CommentModerateModel.deploy()
    ProfileModerateModel.deploy()

    logger.info("Deployment completed.")
    logger.info("Waiting for requests...")
