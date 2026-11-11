[app]
title = Пожарная профилактика
package.name = firereader
package.domain = org.fire
source.dir = .
source.include_exts = py,json,png,jpg,kv
version = 0.1
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow
orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1