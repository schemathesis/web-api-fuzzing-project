FROM python:3.9-slim

RUN pip install fastapi==0.63.0 uvicorn==0.13.4

EXPOSE 80

COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
