# Squarez Android port

Android WebView port of [Squarez PSP browser port](https://github.com/itsamenathan/Squarez-PSP-port), with direct drag controls on the player square. The touch grab area extends **8 game pixels** beyond each side. PSP face buttons remain available.

## Download APK

Open [GitHub Actions](https://github.com/joesnose/squarez-android-port/actions/workflows/build-apk.yml). Select **Build Squarez Android APK** → **Run workflow**. After a successful run, download `squarez-android-debug-apk` from the workflow's Artifacts and extract `app-debug.apk`.

The workflow fetches game source and assets from its original repository automatically. The build and touch behavior are not yet verified on a device.

Original source and credits: [itsamenathan/Squarez-PSP-port](https://github.com/itsamenathan/Squarez-PSP-port).
