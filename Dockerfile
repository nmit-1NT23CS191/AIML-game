# 1. Use the Web-VNC base image
FROM dorowu/ubuntu-desktop-lxde-vnc:focal

# 2. Set the working directory and non-interactive mode
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

# 3. Remove the expired Google Chrome repository to prevent apt-get crash
RUN rm -f /etc/apt/sources.list.d/google-chrome.list

# 4. Install Python and Tkinter
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-tk

# 5. KIOSK HACK: Uninstall the Linux taskbar and desktop background!
RUN apt-get remove -y lxpanel pcmanfm

# 6. Copy requirements and install them
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 7. Copy the rest of your game files into the container
COPY . .

# 8. Tell the container to launch your game automatically
RUN echo "@python3 /app/ai_arithmetic_maze_race_2.py" >> /etc/xdg/lxsession/LXDE/autostart