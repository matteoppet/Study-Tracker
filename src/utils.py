from PIL import Image, ImageTk
import sys
import os

def resource_path(relative_path):
  try:
    base_path = sys._MEIPASS
  except AttributeError:
    base_path = os.path.abspath(".")
  return os.path.join(base_path, relative_path)
