def output_template(kinesis_event, message_receive_time):
    """Template for storing outputs to be sent to SQS and stored \ 
    in Snowflake table.

    Args:
        kinesis_event (json): request payload
        message_receive_time (str): timestamp when request message is received

    Returns:
        dict: default dictionary for storing outputs
        
    """

    default_time = "0000-00-00 00:00:00.000000+00:00"
    # general outputs
    outputs = {}
    # outputs["TEXT"] = kinesis_event['text']
    # outputs['USER_ID'] = kinesis_event['user_id']
    # outputs['EVENT_TIME'] = kinesis_event['event_time']
    # outputs['VIDEO_ID'] = kinesis_event['video_id']
    # outputs['COUNTRY'] = kinesis_event['country']
    # outputs['VIDEO_URL'] = kinesis_event['video_url']
    # if len(kinesis_event['video_id']) == 0:
    #     outputs['ASSET_TYPE'] = 'profile'
    # else:
    #     outputs['ASSET_TYPE'] = 'comment'

    outputs["TEXT"] = kinesis_event['text']
    outputs['USER_ID'] = kinesis_event['user_id']
    outputs['COUNTRY'] = kinesis_event['country']
    outputs['EVENT_TIME'] = kinesis_event['event_time']
    outputs["ASSET_TYPE"] = kinesis_event['asset_type']     
    outputs['VIDEO_ID'] = kinesis_event['video_id'] 
    outputs['VIDEO_URL'] = kinesis_event['video_url'] 
    outputs["MESSAGE_RECEIVE_TIME"] = message_receive_time

    # model-specific outputs
    outputs["MODEL_VERSION"] = "1.0.0"
    outputs["TO_BE_MODERATED"] = False
    outputs["MODEL_ATTRIBUTES"] = {}
    outputs["MODEL_ATTRIBUTES"]["LANG"] = ""
    outputs["MODEL_ATTRIBUTES"]["IS_EMAIL"] = False
    outputs["MODEL_ATTRIBUTES"]["IS_URL"] = False
    outputs["MODEL_ATTRIBUTES"]["IS_LONG"] = False
    outputs["MODEL_ATTRIBUTES"]["IS_LEETSPEAK_PROFANITY"] = False
    outputs["MODEL_ATTRIBUTES"]["AI_PREDICTION"] = False
    outputs["MODEL_ATTRIBUTES"]["AI_PROBABILITY"] = -1
    outputs["MODEL_ATTRIBUTES"]["PROCESS_DURATION"] = -1
    outputs["MODEL_ATTRIBUTES"]["MODEL_DURATION"] = -1
    outputs["MODEL_ATTRIBUTES"]["PROMOTION_DURATION"] = -1
    outputs["MODEL_ATTRIBUTES"]["LEET_DURATION"] = -1
    outputs["MODEL_ATTRIBUTES"]["COMBINE_DURATION"] = -1
    outputs["MODEL_ATTRIBUTES"]["TOTAL_DURATION"] = -1
    outputs["MODEL_ATTRIBUTES"]["STATUS"] = -1
    outputs["MODEL_ATTRIBUTES"]["TRANSLATED_TO_EN"] = ""

    return outputs