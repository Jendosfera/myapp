[app]
title = Пожарная профилактика
package.name = firereader
package.domain = org.fire
source.dir = .
source.include_exts = py,json,png,jpg,kv
version = 0.1

requirements = python3==3.11.16,hostpython3==3.11.16,kivy==2.3.1,kivymd==1.1.1,pillow
orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
android.ndk = 25b

p4a.branch = develop
p4a.python_version = 3.11

[buildozer]
log_level = 2
warn_on_root = 1