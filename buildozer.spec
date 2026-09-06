[app]

# (str) Title of your application
title = Mutaba3a

# (str) Package name
package.name = mutaba3a

# (str) Package domain (needed for android/ios packaging)
package.domain = org.reem

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,ttf

# (str) Application versioning
version = 0.1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3==3.11.9,kivy==2.3.0,plyer==2.1.0,requests==2.31.0,python-dateutil==2.9.0.post0,pyjnius,certifi

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# -----------------------------------------------------------------------------
# ANDROID
# -----------------------------------------------------------------------------

# (list) Permissions
# INTERNET: needed for geocoding / prayer times API / Firebase sync
# ACCESS_FINE_LOCATION / ACCESS_COARSE_LOCATION: needed for GPS-based prayer times
# ACCESS_NETWORK_STATE: needed to detect online/offline before syncing
# RECEIVE_BOOT_COMPLETED: needed later for reminder notifications surviving reboot
# POST_NOTIFICATIONS: needed on Android 13+ to show reminder notifications
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_NETWORK_STATE,RECEIVE_BOOT_COMPLETED,POST_NOTIFICATIONS

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 24

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android SDK version to use
#android.sdk = 33

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid excess Internet downloads or save time
# when an update is due and you just want to test/build your package
android.skip_update = False

# (bool) Accept all SDK licenses automatically
android.accept_sdk_license = True

# (str) python-for-android branch to use, defaults to master
#p4a.branch = master

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
