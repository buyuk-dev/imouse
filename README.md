# Development state:

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
    - receives commands from the mouse client app and moves the mouse based on those commands.
    - plots the received movement commands in real time using basic matplotlib animation (not efficient but suffices for debugging purposes)
    - loads settings from json file

Bugs:
    - visualization code has a bug with matplotlib being started in a background thread rather than main
    - when client disconnects logs show a json decode error, need to handle disconnect more cleanly


### Mouse Client APK

Need to implement better filtering. Currently integrating accelerometer reading into speed and position leads to very noisy results and the mouse is not yet usable.


# References

[Implementing Positioning Algorithms Using Accelerometers](https://www.nxp.com/docs/en/application-note/AN3397.pdf) by Kurt Seifert and Oscar Camacho
[StackOverflow thread about accelerometer calibration](https://stackoverflow.com/questions/43364006/android-accelerometer-calibration)
[Clinometer App SourceCode](https://github.com/BasicAirData/Clinometer/blob/master/app/src/main/java/eu/basicairdata/clinometer/CalibrationActivity.java)
[Build Kivy Apps On Android Official Quickstart Guide](https://buildozer.readthedocs.io/en/latest/quickstart.html)
[Plyer Documentation](https://plyer.readthedocs.io/en/latest/api.html)
[How To Build And Package Kivy Android Application Using Github Actions Workflow](https://middlewaretechnologies.in/2023/07/how-to-build-and-package-kivy-android-application-using-github-actions-workflow.html)
[Buildozer.spec reference](https://buildozer.readthedocs.io/en/latest/specifications.html)