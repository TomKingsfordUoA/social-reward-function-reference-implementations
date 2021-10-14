FROM ros:melodic-ros-core

# Core system:
RUN apt update
RUN apt install -y software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt install -y python3.8 python3-pip python3.8-dev python python-pip
RUN apt install -y ros-melodic-ros-base
RUN rm /usr/bin/python3; ln -s /usr/bin/python3.8 /usr/bin/python3
RUN python3 -m pip install --upgrade pip

# Specific requirements:
RUN apt install -y ros-melodic-rospy
RUN python3 -m pip install rospkg
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
RUN apt install -y libsndfile1 libsndfile1-dev

WORKDIR /app
COPY ./pymo /app/pymo
COPY ./srf_reference_implementations /app/srf_reference_implementations
COPY ./docker-entrypoint.sh /app/docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python3", "srf_reference_implementations/cli.py", "--use_ros", "-t", "srf_reference_implementations/interfaces/test_resources/GENEA_sample_transcript_cleaned.json"]