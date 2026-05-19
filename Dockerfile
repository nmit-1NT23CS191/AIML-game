# 1. Use a base image that has a virtual desktop and Web VNC built-in
FROM dorowu/ubuntu-desktop-lxde-vnc:focal

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install Python and Tkinter for the virtual environment
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-tk

# 4. Copy requirements and install them
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your game files into the container
COPY . .

# 6. Tell the container to launch your game automatically when the virtual desktop starts
RUN echo "@python3 /app/ai_arithmetic_maze_race_2.py" >> /etc/xdg/lxsession/LXDE/autostart