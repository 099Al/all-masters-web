import os
import signal

import psutil

def print_children(pid, indent=0):
    try:
        parent = psutil.Process(pid)
        print(" " * indent + f"{parent.pid} - {parent.name()}")
        for child in parent.children(recursive=True):
            print(" " * (indent + 4) + f"{child.pid} - {child.name()}")
    except psutil.NoSuchProcess:
        print(f"Process {pid} not found")

def find_by_name(name: str):
    """Find processes by name and print their tree"""
    found = False
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and name.lower() in proc.info['name'].lower():
            found = True
            print_children(proc.info['pid'])
    if not found:
        print(f"No process found with name '{name}'")


def stop():
    PORT = 8000

    for conn in psutil.net_connections(kind="inet"):
        if conn.laddr.port == PORT and conn.pid:
            try:
                p = psutil.Process(conn.pid)
                print(f"Убиваю PID={p.pid}, имя={p.name()}")
                p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"Не удалось завершить PID={conn.pid}: {e}")

# Example: find uvicorn/python processes and their children
# find_by_name("uvicorn")

# stop_process(11664)

stop()