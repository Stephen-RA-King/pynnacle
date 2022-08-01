FROM python:3.9-alpine
WORKDIR /apps/pynnacle/
COPY src/pynnacle/. .
COPY requirements/development.txt .
RUN ["pip", "install",  "--no-cache-dir", "-r", "development.txt"]
CMD ["python", "pynnacle.py"]
