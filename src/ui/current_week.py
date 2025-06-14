import tkinter as tk
from tkinter import ttk
import csv
from datetime import datetime, date, timedelta
from tkinter import messagebox
from tkinter.simpledialog import askstring
import json
from core.paths import DATA_CURRENT_WEEK, DATA_WEEKS_LOG, USER_CONFIG, ICON_PATH, GIFS_PATH, PROJECTS_CSV
from ui.style import StyleManager
from utils.utils import time_to_seconds, seconds_to_time
from PIL import ImageTk, Image, ImageSequence

FORMAT_TIME_STRING = "%h:%m:%s"
FORMAT_DAY_STRING = "%Y-%m-%d"

class TimerWindow(tk.Toplevel):
  def __init__(self, master, root):
    super().__init__()
    self.root = root
    self.master = master

    try: self.iconbitmap(ICON_PATH)
    except tk.TclError: self.iconbitmap("../assets/logo.ico")

    self.title("Study Time")
    self.minsize(300, 200)
    self.resizable(False, False)
    self.geometry(f"+{self.winfo_pointerx()}+{self.winfo_pointery()}")
    self.topmost = False
    self.attributes("-topmost", self.topmost)
    self.configure(bg=StyleManager.get_item_color("bg"))
    self.protocol("WM_DELETE_WINDOW", lambda: self.close())

    with open(USER_CONFIG, "r") as readf:
      data = json.load(readf)

    self.gif_image_path = GIFS_PATH + "/" + data["filename_gif"]
    self.gif = Image.open(self.gif_image_path)
    self.gif_frames = [ImageTk.PhotoImage(frame.copy().resize((340, 160), Image.LANCZOS)) for frame in ImageSequence.Iterator(self.gif)]
    self.frame_gif = 0

    self.total_tasks_todo = 0
    self.total_tasks_done = 0

    self.reset()

  def draw_timer(self):
    self.image_label = ttk.Label(self)
    self.image_label.pack(side="top", anchor="center")

    frame_timer_tasks = ttk.Frame(self)
    frame_timer_tasks.pack(side="top", expand=True, fill="both", padx=10, pady=10)

    timer_text = f"{(self.timer_hours):02d}:{(self.timer_minutes):02d}:{(self.timer_seconds):02d}"
    self.timer_label = ttk.Label(frame_timer_tasks, text=timer_text, font=(StyleManager.get_current_font(), 20, "bold"))
    self.timer_label.pack(side="left", padx=10)

    frame_tasks = ttk.Frame(frame_timer_tasks)
    frame_tasks.pack(side="right", expand=True, fill="both", padx=10)
    frame_title_and_button = ttk.Frame(frame_tasks)
    frame_title_and_button.pack(side="top", fill="both", expand=True)
    ttk.Label(frame_title_and_button, text="Tasks", font=(StyleManager.get_current_font(), 18, "bold")).pack(side="left")
    ttk.Button(frame_title_and_button, text="Add", width=4, command=lambda: self.add_new_task()).pack(side="right")

    self.tasks_listbox = tk.Listbox(frame_tasks, height=5, selectmode="single")
    self.tasks_listbox.pack(side="top", fill="both", expand=True, pady=5)
    self.tasks_listbox.bind("<Double-1>", lambda x: self.sign_task_done(x))

    self.progressbar = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode="determinate", takefocus=True, maximum=100)
    self.progressbar.pack(side="top", padx=10, fill="x", expand=True)

    ttk.Separator(self, orient="horizontal").pack(side="top", fill="x", pady=3)

    frame_buttons = ttk.Frame(self)
    frame_buttons.pack(side="top", fill="both", expand=True, padx=10, pady=10)
    ttk.Button(frame_buttons, text="Close", command=lambda: self.close()).pack(side="right")
    ttk.Button(frame_buttons, text="Reset", style="Red.TButton", command=lambda: self.reset_and_save()).pack(side="left")
    self.button_pin_window = ttk.Button(frame_buttons, text="Pin", command=lambda: self.pin_window())
    self.button_pin_window.pack(side="left")

  def add_new_task(self):
    new_task_name = askstring("New task", "What's is your new task?")
    formatted_task = f"{str(self.tasks_listbox.size()+1)}. " + new_task_name 
    self.total_tasks_todo += 1
    self.tasks_listbox.insert(0, formatted_task)

  def sign_task_done(self, event):
    selection = self.tasks_listbox.curselection()
    if selection:
      index = selection[0]
      text = self.tasks_listbox.selection_get()
      formatted_text = ' ✓ ' + text

      self.tasks_listbox.delete(index)
      self.tasks_listbox.insert(tk.END, formatted_text)

      self.total_tasks_done += 1
      self.update_progressbar()

  def update_progressbar(self):
    progress = (self.total_tasks_done) / self.total_tasks_todo * 100
    self.progressbar["value"] = progress 

  def animate_gif(self):  
    self.image_label.configure(image=self.gif_frames[self.frame_gif])
    self.image_label.image = self.gif_frames[self.frame_gif]

    self.frame_gif = (self.frame_gif + 1) % len(self.gif_frames)
    self.id_timer_gif = self.after(100, self.animate_gif)

  def save_log(self):
    def check_new_week():
      with open(USER_CONFIG, "r") as readf:
        data = json.load(readf)
      
      last_day_recorded = data["last_day"]
      today = date.today()
      today_string = f"{today.year} {today.month} {today.day}"

      if last_day_recorded == "":
        data["last_day"] = today_string
        
        with open(USER_CONFIG, "w") as outfile:
          outfile.write(json.dumps(data, indent=2))

        return False
      else:
        today = date.today()
        today_string = f"{today.year} {today.month} {today.day}"
        date1 = datetime(int(last_day_recorded.split(" ")[0]),int(last_day_recorded.split(" ")[1]), int(last_day_recorded.split(" ")[2]))
        date2 = datetime(int(today.year), (today.month), int(today.day))

        week1 = date1.isocalendar()[:2]
        week2 = date2.isocalendar()[:2]

        data["last_day"] = today_string

        with open(USER_CONFIG, "w") as outfile:
          outfile.write(json.dumps(data, indent=2))

        return week1 != week2

    def create_new_week_log():
      week_days = []
      total_time_studied = 0

      with open(DATA_CURRENT_WEEK, "r") as readf_current_week:
        reader = csv.DictReader(readf_current_week)

        for row in reader:
          week_days.append(row)
          time_to_add = row["Time"]
          total_time_studied += int(time_to_add)
        
      with open(DATA_WEEKS_LOG, "r") as readf_weeks:
        reader = csv.reader(readf_weeks)
        temp_data = list(reader)

      data_time = seconds_to_time(total_time_studied)
      text_to_write = FORMAT_TIME_STRING.replace("%h", f"{data_time[0]:02d}").replace("%m", f"{data_time[1]:02d}").replace("%s", f"{data_time[2]:02d}")
      temp_data.insert(1, [len(temp_data), text_to_write, week_days])

      with open(DATA_WEEKS_LOG, "w", newline="") as writef:
        writer = csv.writer(writef)
        writer.writerows(temp_data)

    def clear_current_week_table():
      fieldnames = []
      with open(DATA_CURRENT_WEEK) as f:
        reader = csv.DictReader(f)

        fieldnames = reader.fieldnames 

      f = open(DATA_CURRENT_WEEK, "w")
      f.truncate()
      f.close()

      with open(DATA_CURRENT_WEEK, "w", newline="") as csvfile:
        spamwriter = csv.writer(csvfile)

        spamwriter.writerow(fieldnames)
  
    week_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    current_day = f"{week_days[datetime.weekday(datetime.today())].capitalize()}, {datetime.today().strftime(FORMAT_DAY_STRING)}"
    time_studied = time_to_seconds(self.timer_hours, self.timer_minutes) + self.timer_seconds
    study_category = self.master.new_frame_value_selected_combobox.get()

    project_tracking = False
    try:
      ID_project = study_category.split(": ")[0]
      study_category = study_category.split(": ")[1]
      project_tracking = True
    except IndexError:
      pass

    if check_new_week():
      create_new_week_log()
      clear_current_week_table()

    time_to_add = 0
    with open(DATA_CURRENT_WEEK, "r") as tempdata:
      reader = csv.DictReader(tempdata)

      for row in reader:
        if str(row["Day"]) == str(current_day):
          time_to_add = int(row["Time"])
          break

    with open(DATA_CURRENT_WEEK, "r") as readf:
      reader = csv.reader(readf)
      data = list(reader)

    total_seconds = time_studied + time_to_add

    if time_to_add > 0: 
      data.pop(1)
      description = f"{row["Description"]}, {study_category.capitalize()}"
    else:
      description = study_category.capitalize()

    row_updated = [current_day, total_seconds, description]
    data.insert(1, row_updated)

    with open(DATA_CURRENT_WEEK, "w", newline="") as writef:
      writer = csv.writer(writef)
      writer.writerows(data)
    
    if project_tracking:
      with open(PROJECTS_CSV, "r") as readf:
        reader = csv.reader(readf)
        data_projects = list(reader)

      for row in data_projects[1:]:
        if int(row[0]) == int(ID_project):
          row[4] = int(row[4]) + time_studied 

      with open(PROJECTS_CSV, "w", newline="") as writef:
        writer = csv.writer(writef)
        writer.writerows(data_projects)


  def update_timer(self):
    if not self.check_goal_reached():
      if self.timer_seconds != 59:
        self.timer_seconds += 1
      else:
        self.timer_seconds = 0
        self.timer_minutes += 1

        if self.timer_minutes == 60:
          self.timer_minutes = 0
          self.timer_hours += 1

      self.timer_label.config(text=f"{(self.timer_hours):02d}:{(self.timer_minutes):02d}:{(self.timer_seconds):02d}")

      self.id_timer = self.after(1000, self.update_timer)
    else:
      messagebox.showinfo("Study Session", "Congratulation, you have reached your time session goal!")

  def check_goal_reached(self):
    if self.goal_selected != "No goal":
      try:
        goal_in_seconds = time_to_seconds(int(self.goal_formatted_time.split(" ")[0]), int(self.goal_formatted_time.split(" ")[1]))
      except IndexError:
        goal_in_seconds = time_to_seconds(int(self.goal_formatted_time.split(" ")[0]), 0)
      current_time_in_seconds = time_to_seconds(self.timer_hours, self.timer_minutes)

      if goal_in_seconds == current_time_in_seconds:
        self.reset_and_save()
        return True

  def reset(self):
    self.timer_hours = 0
    self.timer_minutes = 0
    self.timer_seconds = 0
    self.goal_selected = self.master.goal_study_time_selected.get()
    if self.goal_selected != "No goal": self.goal_formatted_time = self.goal_selected.replace("h", "").replace("m", "").replace("s", "")

    for widgets in self.winfo_children():
      widgets.destroy()

    self.id_timer = self.after(1000, self.update_timer)
    self.id_timer_gif = self.after(100, self.animate_gif)

    self.draw_timer()

  def reset_and_save(self):
    self.after_cancel(self.id_timer)
    self.save_log()
    self.reset()

  def close(self):
    save_and_close = True
    if not self.check_goal_reached():
      if messagebox.askyesno("Closing Timer", f"You have not reached your goal estabilished, are you sure you want to end the session?\n\nCurrent progress will be saved."):
        save_and_close = True
      else:
        save_and_close = False

    if save_and_close:
      self.progressbar.stop()
      self.save_log()
      self.destroy()
      self.root.controller.deiconify()
      self.root.controller.run()

  def pin_window(self):
    self.topmost = not self.topmost
    self.attributes("-topmost", self.topmost)

    if self.topmost:
      self.button_pin_window.config(text="Unpin")
    else:
      self.button_pin_window.config(text="Pin")

class CreateNewLog(tk.Toplevel):
  def __init__(self, master):
    super().__init__(master)
    self.master = master
    self.title("Creation")
    self.minsize(400, 200)
    mouse_x = self.winfo_pointerx()
    mouse_y = self.winfo_pointery()
    self.geometry(f"+{mouse_x}+{mouse_y}")
    self.resizable(False, False)

    try: self.iconbitmap(ICON_PATH)
    except tk.TclError: self.iconbitmap("../assets/logo.ico")

    self.container = ttk.Frame(self)
    self.container.pack(fill="both")

    self.goal_study_time_options = ["No goal", "0h 30m", "0h 45m", "1h 0m", "1h 30m", "2h"]
    self.goal_study_time_selected = tk.StringVar(self)
    self.goal_study_time_selected.set(self.goal_study_time_options[0])

    self.selected_day = tk.StringVar(self)

    self.new_frame_category_selected = tk.StringVar()
    self.new_frame_category_selected.set("subject")
    self.old_frame_category_selected = tk.StringVar()
    self.old_frame_category_selected.set("subject")

    self.new_frame_value_selected_combobox = tk.StringVar()
    self.old_frame_value_selected_combobox = tk.StringVar()

    with open(USER_CONFIG, "r") as readf:
      data = json.load(readf)
      readf.close()

    self.new_frame_values_combobox = data["subjects"]
    self.old_frame_values_combobox = data["subjects"]

    self.new_frame_value_selected_combobox.set(self.new_frame_values_combobox[0])
    self.old_frame_value_selected_combobox.set(self.old_frame_values_combobox[0])

    self.run()

  def run(self):
    notebook = ttk.Notebook(self.container)
    notebook.pack(expand=True, fill="both")

    frame_current_log = ttk.Frame(notebook)
    frame_old_log = ttk.Frame(notebook)

    frame_current_log.pack(fill="both", expand=True)
    frame_old_log.pack(fill="both", expand=True)

    notebook.add(frame_current_log, text="Create new log")
    notebook.add(frame_old_log, text="Add log")

    self.draw_current_log(frame_current_log)
    self.draw_old_log(frame_old_log)

  def draw_current_log(self, frame):
    def update_list_category():
      self.new_frame_values_combobox.clear()
      self.new_frame_label_combobox.config(text=f"Select {self.new_frame_category_selected.get()}:")

      if self.new_frame_category_selected.get() == "projects":

        with open(PROJECTS_CSV, "r") as readf:
          reader = csv.DictReader(readf)

          for row in reader:
            if row["Status"] == "Not Started":
              self.new_frame_values_combobox.append(f"{row['ID']}: {row['Name']}")
      else:
        with open(USER_CONFIG, "r") as readf:
          data = json.load(readf)
          readf.close()
        self.new_frame_values_combobox = data["subjects"]

      self.new_frame_value_selected_combobox.set(self.new_frame_values_combobox[0])
      self.new_frame_combobox.config(values=self.new_frame_values_combobox)

    ttk.Label(frame, text="Study time!", font=(StyleManager.get_current_font(), 15, "bold")).pack(side="top", anchor="w", padx=10, pady=10)

    frame_current_day = ttk.Frame(frame)
    frame_current_day.pack(side="top", fill="x", padx=10)
    ttk.Label(frame_current_day, text="Current day:").pack(side="left")
    ttk.Label(frame_current_day, text=datetime.today().strftime('%Y-%m-%d')).pack(side="right")

    ttk.Separator(frame, orient="horizontal").pack(side="top", fill="x", padx=10, pady=10)

    frame_study_time_goal = ttk.Frame(frame)
    frame_study_time_goal.pack(side="top", fill="x", padx=10)
    ttk.Label(frame_study_time_goal, text="Study time goal:").pack(side="left")
    study_time_goal_menu = ttk.Combobox(frame_study_time_goal, textvariable=self.goal_study_time_selected, values=self.goal_study_time_options)
    study_time_goal_menu.pack(side="right")

    label_frame_tracking_category = ttk.Labelframe(frame, text="Tracking Category")
    label_frame_tracking_category.pack(side="top", fill="x", padx=10, pady=(5,0))

    frame_radiobuttons = ttk.Frame(label_frame_tracking_category)
    frame_radiobuttons.pack(side="top", padx=5, pady=5)
    radiobutton_subjects = ttk.Radiobutton(frame_radiobuttons, text="Subjects", variable=self.new_frame_category_selected, value="subject", command=lambda: update_list_category())
    radiobutton_subjects.pack(side="left")
    radiobutton_projects = ttk.Radiobutton(frame_radiobuttons, text="Projects", variable=self.new_frame_category_selected, value="projects", command=lambda: update_list_category())
    radiobutton_projects.pack(side="right", padx=(30, 0))

    frame_combobox = ttk.Frame(label_frame_tracking_category)
    frame_combobox.pack(side="top", fill="x", padx=5, pady=10)
    self.new_frame_label_combobox = ttk.Label(frame_combobox, text="Select subject:")
    self.new_frame_label_combobox.pack(side="left")
    self.new_frame_combobox = ttk.Combobox(frame_combobox, textvariable=self.new_frame_value_selected_combobox, values=self.new_frame_values_combobox)
    self.new_frame_combobox.pack(side="right", fill="x")

    ttk.Separator(frame, orient="horizontal").pack(fill="x", side="top", padx=10, pady=10)

    frame_buttons = ttk.Frame(frame)
    frame_buttons.pack(side="top", fill="x", padx=10)
    button_start_timer = ttk.Button(frame_buttons, text="Start", command=lambda: self.start_timer())
    button_start_timer.pack(side="right")
    button_cancel = ttk.Button(frame_buttons, text="Cancel", command=lambda: self.destroy())
    button_cancel.pack(side="left")

  def draw_old_log(self, frame):
    def update_list_category():
      self.old_frame_values_combobox.clear()
      self.old_frame_label_combobox.config(text=f"Select {self.new_frame_category_selected.get()}:")

      if self.old_frame_category_selected.get() == "projects":

        with open(PROJECTS_CSV, "r") as readf:
          reader = csv.DictReader(readf)

          for row in reader:
            if row["Status"] == "Not Started":
              self.old_frame_values_combobox.append(f"{row['ID']}: {row['Name']}")
      else:
        with open(USER_CONFIG, "r") as readf:
          data = json.load(readf)
          readf.close()
        self.old_frame_values_combobox = data["subjects"]

      self.old_frame_value_selected_combobox.set(self.old_frame_values_combobox[0])
      self.old_frame_combobox.config(values=self.old_frame_values_combobox)

    ttk.Label(frame, text="Forgot to log your session?", font=(StyleManager.get_current_font(), 15, "bold")).pack(side="top", anchor="w", padx=10, pady=10)

    frame_select_day = ttk.Frame(frame)
    frame_select_day.pack(side="top", fill="x", padx=10)
    ttk.Label(frame_select_day, text="Select week-day:").pack(side="left")

    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    week_dates = [(start_of_week + timedelta(days=i)).day for i in range(7)]
    options_days = [f"{week_days[i]}, {week_dates[i]}"for i in range(0,7)]
    self.selected_day.set(options_days[week_dates.index(today.day)])
    days_current_week = ttk.Combobox(frame_select_day, textvariable=self.selected_day, values=options_days)
    days_current_week.pack(side="right")

    ttk.Separator(frame, orient="horizontal").pack(fill="x", side="top", padx=10, pady=10)

    frame_select_time = ttk.Frame(frame)
    frame_select_time.pack(side="top", fill="x", padx=10)
    ttk.Label(frame_select_time, text="Insert time:").pack(side="left")

    self.hours_inserted_stringvar = tk.StringVar()
    self.minutes_inserted_stringvar = tk.StringVar()

    ttk.Label(frame_select_time, text="minutes").pack(side="right", padx=5)
    ttk.Entry(frame_select_time, textvariable=self.minutes_inserted_stringvar, width=4).pack(side="right")

    ttk.Label(frame_select_time, text="hours").pack(side="right", padx=5)
    ttk.Entry(frame_select_time, textvariable=self.hours_inserted_stringvar, width=4).pack(side="right")

    label_frame_tracking_category = ttk.Labelframe(frame, text="Tracking Category")
    label_frame_tracking_category.pack(side="top", fill="x", padx=10, pady=(5,0))

    frame_radiobuttons = ttk.Frame(label_frame_tracking_category)
    frame_radiobuttons.pack(side="top", padx=5, pady=5)
    radiobutton_subjects = ttk.Radiobutton(frame_radiobuttons, text="Subjects", variable=self.old_frame_category_selected, value="subject", command=lambda: update_list_category())
    radiobutton_subjects.pack(side="left")
    radiobutton_projects = ttk.Radiobutton(frame_radiobuttons, text="Projects", variable=self.old_frame_category_selected, value="projects", command=lambda: update_list_category())
    radiobutton_projects.pack(side="right", padx=(30, 0))

    frame_combobox = ttk.Frame(label_frame_tracking_category)
    frame_combobox.pack(side="top", fill="x", padx=5, pady=10)
    self.old_frame_label_combobox = ttk.Label(frame_combobox, text="Select subject:")
    self.old_frame_label_combobox.pack(side="left")
    self.old_frame_combobox = ttk.Combobox(frame_combobox, textvariable=self.old_frame_value_selected_combobox, values=self.old_frame_values_combobox)
    self.old_frame_combobox.pack(side="right", fill="x")

    ttk.Separator(frame, orient="horizontal").pack(fill="x", side="top", padx=10, pady=10)

    frame_buttons = ttk.Frame(frame)
    frame_buttons.pack(side="top", fill="x", padx=10, pady=(0,10))
    button_start_timer = ttk.Button(frame_buttons, text="Insert", command=lambda: self.insert_old_log())
    button_start_timer.pack(side="right")
    button_cancel = ttk.Button(frame_buttons, text="Cancel", command=lambda: self.destroy())
    button_cancel.pack(side="right")

  def insert_old_log(self):
    hours = self.hours_inserted_stringvar.get()
    minutes = self.minutes_inserted_stringvar.get()

    if hours == "" or minutes == "":
      messagebox.showerror("Empty values", "Values of hours or minutes cannot be empty.")
    else:
        
      hours = abs(int(hours))
      minutes = abs(int(minutes))
      day_log = self.selected_day.get()
      time_to_seconds_new_log = time_to_seconds(hours, minutes)
      subject = self.old_frame_value_selected_combobox.get()

      new_time_logged = False

      rows_to_write = []
      with open(DATA_CURRENT_WEEK, "r") as readf:
        reader = csv.DictReader(readf)

        formatted_day_log = int(day_log.split(", ")[1])
        for row in reader:
          day_current_row = int(row["Day"].split(", ")[1].split("-")[1])

          if day_current_row == formatted_day_log:
            time_in_seconds_current_day = time_to_seconds(
              int(row["Time"].split(" ")[0].replace("h", "")),
              int(row["Time"].split(" ")[1].replace("m", "")),
            ) + int(row["Time"].split(" ")[2].replace("s", ""))

            updated_time_to_log +=  time_in_seconds_current_day
            subject = row["Description"] + ", " + subject.capitalize()

            current_row_updated = {key: value  for key, value in row.items()}
            current_row_updated["Time"] = updated_time_to_log
            current_row_updated["Description"] = subject
            rows_to_write.append(current_row_updated)
            
            new_time_logged = True
          else:
            rows_to_write.append(row)

      
        if not new_time_logged:
          count = 0
          for row in rows_to_write:
            day_current_row = int(row["Day"].split(", ")[1].split("-")[1])

            if day_current_row <= formatted_day_log-1 or day_current_row >= formatted_day_log:
              formatted_day = str(day_log.split(", ")[0]) + ", " + str(f"{datetime.today().month:02d}") + "-" + str(day_log.split(", ")[1])

              new_row_to_write = {key: "" for key in row.keys()}
              new_row_to_write["Day"] = formatted_day
              new_row_to_write["Time"] = time_to_seconds_new_log
              new_row_to_write["Description"] = subject

              if formatted_day_log < day_current_row: count += 1

              rows_to_write.insert(count, new_row_to_write)
              break
            
            count += 1
          readf.close()

      with open(DATA_CURRENT_WEEK, "w", newline="") as writef:
        writer = csv.DictWriter(writef, fieldnames=rows_to_write[0].keys())
        writer.writeheader()
        writer.writerows(rows_to_write)

      try:
        ID_project = subject.split(": ")[0]

        with open(PROJECTS_CSV, "r") as readf_projects:
          reader = csv.reader(readf_projects)

          rows = []
          for row in reader:
            try:
              if int(row[0]) == int(ID_project):
                row[4] = int(row[4]) + time_to_seconds_new_log
            except ValueError:
              pass

            rows.append(row)
          readf_projects.close()
        
        with open(PROJECTS_CSV, "w", newline="") as writef_projects:
          writer = csv.writer(writef_projects)
          writer.writerows(rows)

      except IndexError:
        pass

      self.master.clear_widgets()
      self.master.load_data()
      self.master.draw_table()
      self.destroy()

  def start_timer(self):
    self.master.controller.withdraw()
    self.destroy()
    TimerWindow(self, self.master)

class Home(ttk.Frame):
  def __init__(self, root, controller):
    super().__init__(root)
    self.controller = controller
    self.pack(side="top", anchor="n", expand=True, fill="both")
    self.pack_propagate(False)
    self.configure(width=(self.winfo_width()/2)+100)

    self.headers_name = []
    self.data = []

    self.load_data()

  def draw_table(self):
    style = ttk.Style()
    
    # TITLE FRAME + BUTTON CREATE NEW LOG
    title_frame = ttk.Frame(self)
    title_frame.pack(fill="x")

    ttk.Label(title_frame, text="Current week", font=(StyleManager.get_current_font(), 15, "bold")).pack(side="left")

    create_new_log_button = ttk.Button(title_frame, text="Create new log", command=lambda: self.create_new_log())
    create_new_log_button.pack(side="right")

    # CURRENT DAY FRAME
    current_day_frame = ttk.Frame(self)
    current_day_frame.pack(fill="x", pady=10)
    ttk.Label(current_day_frame, text=f"Today is:").pack(side="left")
    ttk.Label(current_day_frame, text=datetime.today().strftime(FORMAT_DAY_STRING), font=(StyleManager.get_current_font(), 9, "bold")).pack(side="left")

    self.headers_name.insert(0, "Goal")
    self.treeview = ttk.Treeview(
      self,
      columns=self.headers_name,
      show="headings",
      height=5,
    )

    # insert data to the treeview
    for heading in self.headers_name:
      self.treeview.heading(heading, text=heading)

      if heading == "Time":
        self.treeview.column(heading, width=140, anchor='center')
      elif heading == "Goal":
        self.treeview.column(heading, width=50, anchor='center')
      else:
        self.treeview.column(heading, width=140, anchor='w')
        
    for row_data in self.data:
      values_to_insert = []

      for key, value in row_data.items():
        if key == "Time":
          total_time_studied = value

          with open(USER_CONFIG, "r") as readf:
            reader = json.load(readf)
            readf.close()

          goal = reader["session_goal"]
          goal_to_seconds = time_to_seconds(int(goal[0]), int(goal[1]))

          if int(total_time_studied) >= int(goal_to_seconds): values_to_insert.insert(0, "👍")
          else: values_to_insert.insert(0, "👎")

          data_seconds_in_time = seconds_to_time(int(total_time_studied))
          value = FORMAT_TIME_STRING.replace("%h", f"{data_seconds_in_time[0]:02d}").replace("%m", f"{data_seconds_in_time[1]:02d}").replace("%s", f"{data_seconds_in_time[2]:02d}")

        values_to_insert.append(value)

      self.treeview.insert(
        "",
        tk.END,
        values=values_to_insert,
      )

    for item_id in self.treeview.get_children():
      values = self.treeview.item(item_id, "values")
      item_day = values[1].split(", ")

      if item_day[1] == datetime.today().strftime(FORMAT_DAY_STRING):
        self.treeview.item(item_id, tags="current_day") 

    self.treeview.tag_configure("current_day", background="#cce5ff", foreground="black" if StyleManager.get_current_theme().lower() == "light" else StyleManager.get_item_color("bg"))
    
    self.treeview.pack(side="left", fill="both", expand=True)
    

  def clear_widgets(self):
    for widgets in self.winfo_children():
      widgets.destroy()

  def load_data(self):
    self.data.clear()

    with open(DATA_CURRENT_WEEK, newline="") as tempdata:
      reader = csv.DictReader(tempdata)

      self.headers_name = reader.fieldnames

      for row in reader:
        current_row = {}

        for key, value in row.items():
          current_row[key] = str(value.capitalize())

        self.data.append(current_row)

  def create_new_log(self):
    CreateNewLog(self)