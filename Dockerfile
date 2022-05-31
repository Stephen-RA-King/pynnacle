FROM python:3.9-alpine
WORKDIR /apps/pynnacle/
COPY src/pynnacle/. .
COPY requirements/development.txt .
RUN ["pip", "install", "-r", "development.txt"]
CMD ["python", "pynnacle.py"]
