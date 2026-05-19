# 1. Use a base image that has a virtual desktop and Web VNC built-in
FROM dorowu/ubuntu-desktop-lxde-vnc:focal

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Tell Ubuntu NOT to ask for timezone/keyboard inputs during the build
ENV DEBIAN_FRONTEND=noninteractive

# 4. FIX: Remove the expired Google Chrome repository to prevent apt-get update from crashing
RUN rm -f /etc/apt/sources.list.d/google-chrome.list

# 5. Install Python and Tkinter for the virtual environment
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-tk

# 6. Copy requirements and install them
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 7. Copy the rest of your game files into the container
COPY . .

# 8. Tell the container to launch your game automatically when the virtual desktop starts
RUN echo "@python3 /app/ai_arithmetic_maze_race_2.py" >> /etc/xdg/lxsession/LXDE/autostart