 FROM python:3.8
 ENV PYTHONUNBUFFERED 1
 RUN mkdir /code
 WORKDIR /code
 COPY requirements.txt /code/
# RUN apt-get install -y openssh-server
 RUN pip install -r requirements.txt --src /usr/local/src
 # if doesnt work switch back to all
 RUN python -m nltk.downloader popular
 COPY . /code/
