"""
Start SEHAT.

    python run.py

Use this instead of remembering uvicorn flags - it always loads the right
app object from the right folder, even if another project sits nearby.
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.chdir(HERE)

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    print(f"\n  SEHAT starting on http://127.0.0.1:{port}")
    print(f"  Folder: {HERE}")
    print("  Press CTRL+C to stop.\n")
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
