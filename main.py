import sys
from agent import run_agent

def main():
    # Reconfigure stdout/stderr to UTF-8 to handle Unicode characters (emojis, etc.) on Windows
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    
    print("Starting Auto Meeting Scheduler Agent...")
    run_agent()

if __name__ == "__main__":
    main()
