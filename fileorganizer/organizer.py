import os
import time
import shutil
import logging
import threading
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import tkinter as tk
from tkinter import filedialog,messagebox,scrolledtext

try:
    with open("config.json") as f:
        CONFIG=json.load(f)
except FileNotFoundError:
   {
       "watch_directory":{
           "Images":{"extension":[".png",".jpg",".gif"],"name_pattern":["photo"],"content_keyword":["Images"]},
            "Documents": {"extensions": [".pdf", ".txt"], "name_patterns": ["report"], "content_keywords": ["document"]},
            "Videos": {"extensions": [".mp4", ".avi"], "name_patterns": ["video"], "content_keywords": ["video"]},
            "Others": {"extensions": [], "name_patterns": [], "content_keywords": []}

       },
       "log_file":"File_Organizer.log"
   }

   logging.basicConfig(
       filename=CONFIG["log_file"],
       level=logging.INFO,
       format="%(asctime)s - %(levelname)s - %(message)s"

)
logger = logging.getLogger(__name__)

class FileClassifier:
   def classify(self,file_path):
    file_path=Path(file_path)
    if not file_path.exists():
       return "Others"
    
    ext=file_path.suffix.lower()
    name=file_path.stem.lower()

    for catogary,rule in CONFIG["rules"].items():
       if ext in rule["extensions"] or any(p in name for p in rule["patterns_extensions"]):
         return catogary
 
    try:
       if ext in [".txt",".pdf"]:
          with open (file_path ,"r",encoding="utf-8",error="ignore")as f:
            content=f.read(1000).lower()
            for catogary,rule in CONFIG["rules"].items():
                if any(k in content for k in rule["content_keywords"]):
                   return catogary
    except:
       pass
    
    return "Others"
   
class FileMover:
   def move_file(self,file_path,category):
      file_path=Path(file_path)
      dest_dir=Path(CONFIG["Organized_based"])/category
      dest_dir.mkdir(parents=True,exist_ok=True)
      dest_path=dest_dir / file_path.name

      counter=1
      while dest_path.exists():
         dest_path=dest_dir/f"{dest_path.stem}-{counter}{dest_path.suffix}"
         counter+=1

      shutil.move(str(file_path),str(dest_path))  
      logger.info(f"Moved{file_path}to{dest_path}")
      return dest_path
   
class FileHandler:
   def __init__(self):
      self.mover=FileMover()
      self.classifer=FileClassifier()

   def on_created(self,event):
      if not event.is_directory:
          category=self.classifier.classify(event.src_path)
          self.mover.move_file(event.src_path,category)

class DirectoryMonitors:
   def __init__(self,watch_dir):
      self.watch_dir=watch_dir
      self.observer=Observer()
      self.handle=FileHandler()
      self.observer.schedule(self.handler,path=watch_dir,recursive=True)

   def start(self):
      logger.info(f"Start Monitoring{self.watch_dir}")
      self.observer.start()
      try:
         while True:
            time.sleep(1)
      except KeyboardInterrupt:
       self.stop()

   def stop(self):
      self.observer.stop()
      self.observer.join()
      logger.info(f"Stop Monitoring")

class OrganizerGUI:
   def __init__(self,root):
      self.root=root
      self.root.title("Smart Organizer File")
      self.monitor=None
      self.monitor_thread=None

   # Widgets
      tk.Label(root, text="Watch Directory:").pack()
      self.watch_entry = tk.Entry(root, width=50)
      self.watch_entry.insert(0, CONFIG["watch_directory"])
      self.watch_entry.pack()
      tk.Button(root, text="Browse", command=self.browse).pack()
        
      self.start_btn = tk.Button(root, text="Start Monitoring", command=self.start_monitoring)
      self.start_btn.pack()
      self.stop_btn = tk.Button(root, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
      self.stop_btn.pack()
        
      self.log_text = scrolledtext.ScrolledText(root, width=80, height=20)
      self.log_text.pack()
      tk.Button(root, text="Refresh Log", command=self.refresh_log).pack()
        
      self.refresh_log()

   def browse(self):
      dir_path = filedialog.askdirectory()
      if dir_path:
         self.watch_entry.delete(0, tk.END)
         self.watch_entry.insert(0, dir_path)

   def start_monitoring(self):
      watch_dir = self.watch_entry.get()
      if not watch_dir:
        messagebox.showerror("Error", "Select a watch directory")
        return
        
        CONFIG["watch_directory"] = watch_dir
        with open("config.json", "w") as f:
            json.dump(CONFIG, f, indent=4)
        
        self.monitor = DirectoryMonitors(watch_dir)
        self.monitor_thread = threading.Thread(target=self.monitor.start, daemon=True)
        self.monitor_thread.start()
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

   def stop_monitoring(self):
        if self.monitor:
            self.monitor.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

   def refresh_log(self):
        try:
            with open(CONFIG["log_file"], "r") as f:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, f.read())
        except FileNotFoundError:
            self.log_text.insert(tk.END, "No log file yet.")

# CLI Mode (run with --cli)
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        monitor = DirectoryMonitors(CONFIG["watch_directory"])
        monitor.start()
    else:
        root = tk.Tk()
        OrganizerGUI(root)
        root.mainloop()

   
   