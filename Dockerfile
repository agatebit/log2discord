# syntax=docker/dockerfile:1

FROM python:3.9.19-bookworm
WORKDIR ./
COPY . .
RUN apt update && apt install -y systemd curl && pip install requests ruamel-yaml && chmod +x /log2discord.sh main.py;
CMD ["/log2discord.sh"]
