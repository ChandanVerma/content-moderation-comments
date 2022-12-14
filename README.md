# Content Moderation for Texts (Comments, Profile descriptions)
This repo does content moderation for text data in general. If any questions, please reach out to Data Science team (Sze Chi, Thulasiram, Chandan).

# Set-up .env file for testing comment moderation in local
There needs to be a `.env` file with following parameters.
```
ProcessNumCPUPerReplica=0.1
ProcessNumReplicas=1
ProcessMaxCon=100

PromotionNumCPUPerReplica=0.1
PromotionNumReplicas=1
PromotionMaxCon=100

LeetNumCPUPerReplica=0.1
LeetNumReplicas=1
LeetMaxCon=100

ModerateNumCPUPerReplica=0.01
ModerateNumGPUPerReplica=0.33
ModerateNumReplicas=1
ModerateMaxCon=100

CombineNumCPUPerReplica=0.1
CombineNumReplicas=1
CombineMaxCon=100

SnowflakeResultsQueue=content_moderation_text_comment-results_dev
SnowflakeProfileResultsQueue=content_moderation_text_profile-results_dev
AiModelBucket=lomotif-datalake-dev
```

# Additional variables for internal testing
For DS Team internal testing, we also need to add the following env vars to the `.env` file:
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-2
```

# For use in `g4dn.2xlarge` instance, use the following variables instead
```
TBC
```

# Instructions (Docker)
1) Ensure there are environment variables or `.env` file, see section above for environment variables.
2) Ensure GPU for docker is enabled. See section below.
3) Once the container is able to detect the GPU, we can follow the normal process of

```
docker-compose build
docker-compose up
```

# Enabling GPU for Docker
To enable the GPU for Docker, make sure Nvidia drivers for the system are installed. [Refer link for details](https://linuxconfig.org/how-to-install-the-nvidia-drivers-on-ubuntu-18-04-bionic-beaver-linux)

Commands which can help install Nvidia drivers are:
```
unbuntu-drivers devices
sudo ubuntu-drivers autoinstall
```

Then nvidia-docker2 tools needs to be installed.
To install follow the below instructions.
[Refer link for details](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

```
curl https://get.docker.com | sh   && sudo systemctl --now enable docker
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)    && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -    && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

# Testing the code locally
1) Test if the code is working as expected. Firstly on terminal, do:
```bash
ray start --head --port=6300
```
2) Then, deploy the ray services:
```bash
python serve_tasks/tasks.py
```
3) Run this:
```bash
python serve_demo.py
```

# More details about the output
Example output upon sending a request to the deployment service:
```python
{'TEXT': "Podem comentar no meu lomotif?', ..., 'Q isso em ⚡️❤️", 'USER_ID': 36359809, 'COUNTRY': 'BR', 'EVENT_TIME': '2022-09-20 00:17:35', 'ASSET_TYPE': 'comment', 'VIDEO_ID': 'ce450a28-ee6c-46b8-a045-c68dc64eb17d', 'VIDEO_URL': '', 'MESSAGE_RECEIVE_TIME': '2022-11-24 08:21:35.110073+00:00', 'MODEL_VERSION': '1.0.0', 'TO_BE_MODERATED': False, 'MODEL_ATTRIBUTES': {'LANG': 'pt', 'IS_EMAIL': False, 'IS_URL': False, 'IS_LONG': False, 'IS_LEETSPEAK_PROFANITY': False, 'AI_PREDICTION': False, 'AI_PROBABILITY': 0.041, 'PROCESS_DURATION': 0.14, 'MODEL_DURATION': 0.62, 'PROMOTION_DURATION': 0.0, 'LEET_DURATION': 0.03, 'COMBINE_DURATION': 0.81, 'TOTAL_DURATION': 0.81, 'STATUS': 0, 'TRANSLATED_TO_EN': 'can comment on my lomotif q this in'}}

{'TEXT': 'you $Uck @$$', 'USER_ID': 36359809, 'COUNTRY': 'BR', 'EVENT_TIME': '2022-09-20 00:17:35', 'ASSET_TYPE': 'profile', 'VIDEO_ID': '', 'VIDEO_URL': '', 'MESSAGE_RECEIVE_TIME': '2022-11-24 08:21:35.969893+00:00', 'MODEL_VERSION': '1.0.0', 'TO_BE_MODERATED': True, 'MODEL_ATTRIBUTES': {'LANG': 'en', 'IS_EMAIL': False, 'IS_URL': False, 'IS_LONG': False, 'IS_LEETSPEAK_PROFANITY': True, 'AI_PREDICTION': True, 'AI_PROBABILITY': 0.983, 'PROCESS_DURATION': 0.0, 'MODEL_DURATION': 0.02, 'PROMOTION_DURATION': 0.0, 'LEET_DURATION': 0.0, 'COMBINE_DURATION': 0.04, 'TOTAL_DURATION': 0.04, 'STATUS': 0, 'TRANSLATED_TO_EN': ''}}
```
- TEXT: Raw text sent for moderation.
- USER_ID: UID of user who posted comment or UID of profile description
- EVENT_TIME: action time
- ASSET_TYPE: type of input whether it is a comment or profile description
- VIDEO_ID: video id where comment was posted or empty string if it is profile description
<!-- - ASSET_TYPE: "profile" for profile description and "comment" for comment text -->
- MESSAGE_RECEIVE_TIME: UTC time where kinesis message is received by the deployment service.
- (PROCESSS/MODEL/PROMOTION/LEET/COMBINE/TOTAL)_DURATION: duration taken in seconds. Rounded to 2 decimal places.
- MODEL_VERSION: model version number.
- TO_BE_MODERATED: Sent to IES for manual moderation if True, accepted by AI if False
- LANG: language of text detected
- IS_EMAIL: True if contains an email address
- IS_URL: True if contains a URL website
- IS_LONG: True if the text is very long
- IS_LEETSPEAK_PROFANITY: True if leetspeak profanity is present
- AI_PREDICTION: True if NSFW text detected by AI, otherwise False
- AI_PROBABILITY: unsafe score of text in 3 decimal places
- TRANSLATED_TO_EN: translated text if text is non-english
<!-- - COUNTRY: As per MAIN_DB definition. -->
<!-- - CREATION_TIME: As per MAIN_DB definition. -->
- STATUS: 
    - 0: Prediction successful. 
    - 1: Processed text is of length 0 or language of text is out of scope. Defaults to TO_BE_MODERATED=True.
    - 2: Language of text if length 0. Defaults to TO_BE_MODERATED=True.
    - -1: Language of text is out of scope. Defaults to TO_BE_MODERATED=False.
    - 3: Some unknown error in the model that was caught by the try...except... loop. Prediction unsucessful. Defaults to TO_BE_MODERATED=True.




