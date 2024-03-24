# Development state:

[![Watch the Demo Recording](https://img.youtube.com/vi/b-4CgelNyL0/hqdefault.jpg)](https://www.youtube.com/embed/b-4CgelNyL0)

## Current Features

Currently I'm testing all the apps on my Redmi 12 Pro with MIUI 14 with server running on my Windows 11 laptop.
Also implemented dummy sensor for testing client on windows with randomly generated signal.
Could improve it by pre-recording some actual accelerometer reading and replaying them in a loop in the future for easier testability.

Haven't yet build it for IOS but have plans to do so when i solve the signal filtering issues in current version.

### Calibration App

Guides the user throguh 7-step accelerometer calibration process.
Currently need to manually copy the calibration data from the app into client/calibration.json file.

### Mouse Server App

Features:
    - Handles movement and click commands from the client app.
    - plots the received movement commands in real time using basic matplotlib animation (not efficient but suffices for debugging purposes)
    - loads settings from json file.

Bugs:
    - Disconnecting and terminating server is not handled in a clean way.


### Mouse Client APK

With the help of Kalman Filter the movements became much better. There is still a lot of room to fine-tune the parameter, but I suppose
will have to clean up the code first to make it easier.

There is an issue that the signal appears to deteriorate the longer the app is running. Will need to review the filter and app state and perhaps change how its reset.

# References

1. [Implementing Positioning Algorithms Using Accelerometers](https://www.nxp.com/docs/en/application-note/AN3397.pdf) by Kurt Seifert and Oscar Camacho
2. [StackOverflow thread about accelerometer calibration](https://stackoverflow.com/questions/43364006/android-accelerometer-calibration)
3. [Clinometer App SourceCode](https://github.com/BasicAirData/Clinometer/blob/master/app/src/main/java/eu/basicairdata/clinometer/CalibrationActivity.java)
4. [Build Kivy Apps On Android Official Quickstart Guide](https://buildozer.readthedocs.io/en/latest/quickstart.html)
5. [Plyer Documentation](https://plyer.readthedocs.io/en/latest/api.html)
6. [How To Build And Package Kivy Android Application Using Github Actions Workflow](https://middlewaretechnologies.in/2023/07/how-to-build-and-package-kivy-android-application-using-github-actions-workflow.html)
7. [Buildozer.spec reference](https://buildozer.readthedocs.io/en/latest/specifications.html)
