#Processing to run on Raspberry Pi
There are two step to process in Raspberrypi.
1. Running MQTT Broker by using EMQX on docker.
2. Running Consumer on docker
*****Teminal Command*****
1. Install docker:
   >> curl -sSL https://get.docker.com | sh
   >> sudo usermod -aG docker $USER
   >> docker --version
2.  Install MQTT Broker (EQMX) and Run on docker, we will use port 1883 for MQTT Broker and 18083 for EMQX UI management:
   >> sudo docker run -p 1883:1883 -p 18083:18083 emqx
   >> Go to raspberrypi.local:18083, Username: admin, Password: public
3. Running Consumer on Docker:
  First, we need to clone project from git_hub, then install some python library and run consumer. After it runs successful, we need build it as docker image. Then, we can run it on docker.
   >> git clone https://github.com/Rengsey/IoT_Fun_Final_Project_G9.git
   >> cd IoT_Final_Project_G9/Raspberry_Pi/Consumer
   >> source pivenv/bin/activate 
   >> pip install paho-mqtt --break-system-packages
   >> python consumer.py
   >> sudo docker build -t consumer . 
   >> sudo docker images
   >> sudo docker --env-file=.env consumer
   >> sudo docker ps
>   >    sudo docker ps
