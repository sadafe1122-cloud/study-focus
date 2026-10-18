[app]
title = Study Focus
package.name = studyfocus
package.domain = org.erfan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav
version = 1.0
requirements = python3,kivy==2.3.0,plyer,pyjnius,android,arabic-reshaper,python-bidi==0.4.2,six,future
orientation = all
fullscreen = 1
android.permissions = POST_NOTIFICATIONS,WAKE_LOCK,READ_EXTERNAL_STORAGE,READ_MEDIA_AUDIO
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
