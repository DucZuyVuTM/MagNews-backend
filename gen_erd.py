import sys
import os


# Add current directory into path, and Python can find 'app' module
sys.path.append(os.getcwd())


from eralchemy2 import render_er
from app.models import Base


def draw():
    try:
        render_er(Base, 'diagram.png')
        print("Created diagram.png successfully.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    draw()
