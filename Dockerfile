FROM python:3.11-slim

WORKDIR /app

# 配置 pip 使用清华大学镜像
RUN mkdir -p /root/.pip && \
    echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple" > /root/.pip/pip.conf

# 替换所有 APT 源为国内镜像源
# RUN echo "deb https://mirrors.ustc.edu.cn/debian bookworm main" > /etc/apt/sources.list && \
#     echo "deb https://mirrors.ustc.edu.cn/debian-security bookworm-security main" >> /etc/apt/sources.list && \
#     echo "deb https://mirrors.ustc.edu.cn/debian bookworm-updates main" >> /etc/apt/sources.list && \
#     apt-get clean && \
#     apt-get update -o Acquire::http::Timeout="10" -o Acquire::Retries="3" && \
#     apt-get install -y --no-install-recommends redis-tools && \
#     rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY ./JieNote_backend/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY ./JieNote_backend /app

# 设置 PYTHONPATH
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]