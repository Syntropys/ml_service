import subprocess

def get_logs():
    try:
        # Run docker logs ml-service and capture stderr and stdout
        result = subprocess.run(
            ['docker', 'logs', 'ml-service'], 
            capture_output=True, 
            text=True
        )
        
        logs = result.stderr + "\n" + result.stdout
        
        # Find traceback
        lines = logs.split("\n")
        traceback_lines = []
        in_traceback = False
        
        for i, line in enumerate(lines):
            if "Traceback (most recent call last):" in line:
                in_traceback = True
                traceback_lines.append("--- TRACEBACK START ---")
                
            if in_traceback:
                traceback_lines.append(line)
                if line.startswith("ValueError:") or line.startswith("TypeError:") or line.startswith("Exception:"):
                    # End of traceback usually
                    traceback_lines.append("--- TRACEBACK END ---")
                    in_traceback = False
                    
        with open("error_traceback.txt", "w") as f:
            f.write("\n".join(traceback_lines))
            if not traceback_lines:
                f.write("No traceback found in logs. Last 50 lines:\n")
                f.write("\n".join(lines[-50:]))
                
        print("Logs extracted to error_traceback.txt")
        
    except Exception as e:
        print(f"Failed to get logs: {e}")

if __name__ == "__main__":
    get_logs()
