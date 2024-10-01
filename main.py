import tkinter as tk
class main:
  armed = false
  print("Welcome To security Detection")
  phoneNumber=input("Enter your phone number to recieve threat alerts: ")
  root = tk.Tk()
  # Create a button
  button = tk.Button(window, text="Arm", command=lambda: print("Button clicked!"))
  button.pack(pady=20)
  # Run the main loop
  window.mainloop()
  def button_clicked():
    print("System Armed: "+ armed)
    armed= not armed
    #run with conditional

      
