 FROM python:3
 ENV PYTHONUNBUFFERED 1
 RUN mkdir /code
 WORKDIR /code
 COPY requirements.txt /code/
 RUN pip install -r requirements.txt --src /usr/local/src
 RUN python -m nltk.downloader all
 COPY . /code/
