FROM python:3.10-slim
WORKDIR /app
COPY ./src /app
RUN pip install flask requests
CMD ["python", "node.py"]