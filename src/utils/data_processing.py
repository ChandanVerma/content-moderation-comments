import numpy as np
import regex as re
import demoji
import pycld2 as cld2

from urlextract import URLExtract
from better_profanity import profanity

# Pre-sets
extractor = URLExtract()

profanity.load_censor_words(
    whitelist_words=["god", "kkk", "omg", "lmao", "lmfao", "damn", "plss", "gai", "wtf"]
)
blacklist_words = ["whatsapp", "text", "****", "f***", "s***"]
profanity.add_censor_words(blacklist_words)


def is_promotion(text, length_threshold):
    """Detect if there are URLs, emails in text or if the text is very long \
    and may be spammy.

    Args:
        text (str): text to moderate
        length_threshold (int): maximum length of a text allowable

    Returns:
        _type_: _description_
    """
    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    urls = extractor.find_urls(text)

    is_email = len(emails) > 0
    is_url = len(urls) > 0
    is_long = len(text) > length_threshold

    return is_email, is_url, is_long


def is_leet_speak_profanity(text):
    """Detect if leetspeak profanity is present.

    Args:
        text (str): text to moderate

    Returns:
        bool: True if leetspeak profanity if detected else False
    """
    return profanity.contains_profanity(text)


def process_text(cmt):
    """Remove metions, numbers, symbols, and lowercase

    Args:
        cmt (str): text to moderate

    Returns:
        str: lowercase text without mentions, numbers, symbols
    """
    tokens = cmt.split(" ")
    for m in tokens:
        if len(m) > 0 and m[0] == "@":
            cmt = re.sub(m, "", cmt)
    cmt = re.sub(r"[0-9]+", "", cmt)
    cmt = re.sub("[^A-Za-z0-9]+", " ", cmt)
    cmt = cmt.lower().strip()
    return cmt


def remove_emoji(text):
    """Remove emojis in text

    Args:
        text (str): text to moderate

    Returns:
        str: text without emojis
    """
    text = demoji.replace(text, "")
    return text


def map_pred_to_result(pred, prob_threshold=0.5):
    """Map prediction softmax probabilities to moderation result

    Args:
        pred (dict): keys are labels and values are softmax probabilities
        prob_threshold (float, optional): Confidence threshold for softmax \
        probabilities. Defaults to 0.5.

    Returns:
        tuple: True if to be moderated else False (bool), value of maximum softmax \
        probability (float)
    """
    labels = list(pred.keys())
    probs = np.array(list(pred.values())).squeeze()
    max_prob = probs[np.argmax(probs)]
    if max_prob > prob_threshold:
        return True, max_prob
    else:
        return False, max_prob


def translate_to_en(text, tokenizer, model):
    """Translate text to english

    Args:
        text (str): text to moderate
        tokenizer (huggingface Tokenizer): translation tokenizer
        model (huggingface Model): translation model

    Returns:
        str: translated text
    """
    batch = tokenizer([text], return_tensors="pt").to("cuda")
    generated_ids = model.generate(**batch)
    trans = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    trans = trans.lower()
    return trans


def lang_detect(text):
    """Detect language of text

    Args:
        text (str): text to moderate

    Returns:
        str: language of text detected
    """
    isReliable, textBytesFound, details = cld2.detect(text, bestEffort=True)
    return details[0][1]
