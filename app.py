
# Re-export the final all-in-one app.py file for the ADI Learning Tracker

import shutil

# Copy the existing app.py file to a new location for download
shutil.copy("app.py", "/mnt/data/app.py")

print("✅ The final app.py file has been re-exported and is ready for download.")
