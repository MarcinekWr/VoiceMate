FROM python:3.10

ENV QT_QPA_PLATFORM=offscreen

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libsm6 \
    libxcomposite1 \
    libxrender1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libglib2.0-0 \
    libnss3 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libx11-xcb1 \
    libxtst6 \
    libxcb1 \
    libxrandr2 \
    libxss1 \
    libxinerama1 \
    libfontconfig1 \
    libdbus-1-3 \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libglu1-mesa \
    libxv1 \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxcb-xfixes0 \
    libxcb-sync1 \
    libxcb-xkb1 \
    qtbase5-dev \
    qtbase5-dev-tools \
    qtwebengine5-dev \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/.streamlit

RUN bash -c 'echo -e "\
[general]\n\
email = \"admin@admin.com\"\n\
" > /root/.streamlit/credentials.toml'

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

ENV STREAMLIT_BROWSER_GATHERUSAGESTATS=false
ENV QTWEBENGINE_CHROMIUM_FLAGS="--no-sandbox"
ENV XDG_RUNTIME_DIR="/tmp/runtime-root"
RUN mkdir -p /tmp/runtime-root && chmod 700 /tmp/runtime-root
ENV PYTHONPATH=.

EXPOSE 80

CMD ["sh", "-c", "xvfb-run -a streamlit run app.py --server.port=80 --server.address=0.0.0.0"]
