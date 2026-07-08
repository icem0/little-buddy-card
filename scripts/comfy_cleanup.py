import subprocess
import time

COMFYUI = "http://192.168.178.53:7801"

def comfyui_cleanup():
    """Entlädt Modelle aus VRAM und leert Queue/Cache für Ollama-Koexistenz."""
    print("🧹 VRAM Cleanup gestartet...")
    
    # 1. Models aus GPU werfen (Blockiert solange der Transfer dauert)
    print("Models werden von VRAM entladen...")
    subprocess.run(['curl', '-s', '-X', 'POST', f'{COMFYUI}/ComfyBackendDirect/free', '--max-time', '120'], capture_output=True)

    # 2. Cache & Queue aufräumen damit der nächste Run sauber startet
    print("Cache und Queue werden geleert...")
    subprocess.run(['curl', '-s', '-X', 'POST', f'{COMFYUI}/ComfyBackendDirect/clear_cache'])
    subprocess.run(['curl', '-s', '-X', 'POST', f'{COMFYUI}/ComfyBackendDirect/queue', 
                    '-H', 'Content-Type: application/json', '-d', '{"clear": true, "interrupt": true}'], 
                    capture_output=True)
    print("VRAM ist frei!")
