# Content Moderation for Comments
This repo does content moderation for text data in general

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
AiModelBucket=datalake-dev
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
