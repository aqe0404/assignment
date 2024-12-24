import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import threading
import time  
import os
import pygame  # Switching from playsound to pygame for better sound control


class AlarmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alarm Clock")
        
        self.alarms = []
        self.currently_playing = False
        self.stop_signal = threading.Event()
        
        # Sound setup
        self.sound_directory = "sounds/"
        if not os.path.exists(self.sound_directory):
            os.makedirs(self.sound_directory)
        self.sound_options = [f for f in os.listdir(self.sound_directory) if f.endswith(('.mp3', '.wav'))]
        
        # Debug print to check the contents of sound_options
        print("Sound options:", self.sound_options)

        if not self.sound_options:
            self.sound_options = ["No Sounds Available"]

        # Initialize Pygame Mixer
        pygame.mixer.init()
        self.current_sound = None  # To track the currently playing sound

        # Start the alarm checking thread
        self.running = True
        self.check_thread = threading.Thread(target=self.check_alarms)
        self.check_thread.daemon = True
        self.check_thread.start()

        # GUI setup
        self.setup_gui()

    def setup_gui(self):
        tk.Label(self.root, text="Set Alarm (HH:MM:SS):").grid(row=0, column=0, padx=5, pady=10)
        self.time_entry = tk.Entry(self.root, width=20)
        self.time_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.root, text="Select Tone:").grid(row=1, column=0, padx=10, pady=5)
        self.selected_sound = tk.StringVar()
        self.selected_sound.set(self.sound_options[0])
        self.sound_menu = ttk.Combobox(self.root, textvariable=self.selected_sound, values=self.sound_options)
        self.sound_menu.grid(row=1, column=1, padx=10, pady=5)

        self.add_button = tk.Button(self.root, text="Add Alarm", command=self.add_alarm)
        self.add_button.grid(row=2, column=1, pady=10)

        self.alarm_listbox = tk.Listbox(self.root, width=50)
        self.alarm_listbox.grid(row=3, column=0, columnspan=3, pady=10)

        self.snooze_button = tk.Button(self.root, text="Snooze", command=self.snooze_alarm)
        self.snooze_button.grid(row=4, column=1, pady=10)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_alarm)
        self.stop_button.grid(row=4, column=2, pady=10)

        self.delete_button = tk.Button(self.root, text="Delete", command=self.delete_alarm)
        self.delete_button.grid(row=4, column=0, pady=10)

    def add_alarm(self):
        alarm_time = self.time_entry.get()
        tone = self.selected_sound.get()

        self.alarm_valid(alarm_time, tone)

    def alarm_valid(self, alarm_time, tone):
        try:
            datetime.strptime(alarm_time, "%H:%M:%S")
            if tone and tone != "No Sounds Available":
                self.alarms.append((alarm_time, tone))
                self.alarm_listbox.insert(tk.END, f"Alarm at {alarm_time} with tone {tone}")
                messagebox.showinfo("Success", "Alarm added successfully!")
            else:
                messagebox.showwarning("Error", "Please select a valid tone!")
        except ValueError:
            messagebox.showwarning("Error", "Invalid time format! Use HH:MM:SS.")

    def play_tone(self, tone):
        """Play the selected alarm tone."""
        try:
            audio_file = os.path.join(self.sound_directory, tone)
            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
            self.stop_alarm()  # Stop any existing sound before starting a new one

            self.current_sound = pygame.mixer.Sound(audio_file)
            self.currently_playing = True
            self.stop_signal.clear()
            
            self.current_sound.play(-1)  # Loop indefinitely until stopped

            start_time = time.time()
            while time.time() - start_time < 300:  # 5 minutes max
                if self.stop_signal.is_set():
                    break
                time.sleep(1)
            
            self.stop_alarm()  # Ensure sound stops after playback

        except pygame.error as e:
            messagebox.showwarning("Sound Error", f"Failed to play sound: {e}")
        except FileNotFoundError as e:
            messagebox.showwarning("Error", str(e))

    def check_alarms(self):
        while self.running:
            current_time = datetime.now().strftime("%H:%M:%S")
            for alarm in self.alarms[:]:  # Iterate over a copy to avoid modification during iteration
                if alarm[0] == current_time:
                    threading.Thread(target=self.play_tone, args=(alarm[1],)).start()
                    messagebox.showinfo("Alarm", f"Alarm ringing at {alarm[0]}!")
                    self.alarms.remove(alarm)
                    self.alarm_listbox.delete(0, tk.END)
                    for a in self.alarms:
                        self.alarm_listbox.insert(tk.END, f"Alarm at {a[0]} with tone {a[1]}")
            time.sleep(1)
   
    def stop_alarm(self):
        """Stop the currently ringing alarm."""
        if self.currently_playing and self.current_sound:
            self.current_sound.stop()
            self.stop_signal.set()
            self.currently_playing = False
            messagebox.showinfo("Stop", "Alarm stopped successfully!")

    def snooze_alarm(self):
        """Snooze the currently ringing alarm."""
        if self.currently_playing:
            self.stop_alarm()
            snoozed_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M:%S")
            self.alarms.append((snoozed_time, self.selected_sound.get()))
            self.alarm_listbox.insert(tk.END, f"Snoozed alarm at {snoozed_time} with tone {self.selected_sound.get()}")
            messagebox.showinfo("Snooze", f"Alarm snoozed to {snoozed_time}")
        else:
            messagebox.showwarning("Error", "No alarm is currently sounding!")
    
    def delete_alarm(self):
        selected_alarm_index = self.alarm_listbox.curselection()
        if not selected_alarm_index:
            messagebox.showwarning("Error", "No alarm selected!")
            return
        selected_alarm = self.alarm_listbox.get(selected_alarm_index)
        alarm_time = selected_alarm.split(" ")[2]
        tone = " ".join(selected_alarm.split(" ")[-3:]).replace("with tone ", "")
        self.alarms.remove((alarm_time, tone))
        self.alarm_listbox.delete(selected_alarm_index)
        messagebox.showinfo("Success", "Alarm deleted successfully!")

    def on_close(self):
        self.running = False
        self.stop_signal.set()
        pygame.mixer.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AlarmApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
