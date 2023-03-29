FROM python:latest

WORKDIR /usr/src/app

COPY  ./ ./

RUN pip install -r ./requirements.txt

CMD ["python3" ,"test.py", ">", "output.log", "2>", "error.log"]
