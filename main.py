import tkinter as tk
from ui import Dashboard
import sequential
import parallel

root = tk.Tk()

app = Dashboard(
    root,
    run_seq=sequential.run_sequential,
    run_par=parallel.run_parallel
)

root.mainloop()