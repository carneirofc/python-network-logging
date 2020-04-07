FROM python:3.8
ADD log_server /log_server.py
RUN mkdir /var/log/log_server
CMD ["python", "/log_server.py", "-f", "/var/log/log_server/", "--port", "9020", "--stdout"]
