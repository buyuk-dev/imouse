How to package app for android?
===============================

**Need to use WSL**

    pip3 install --user --upgrade buildozer

    sudo apt update

    sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev dos2unix
    pip3 install --user --upgrade Cython==0.29.33 virtualenv  # the --user should be removed if you do this in a venv

    buildozer init
    buildozer -v android debug

    # Required if you get an error indicating something like: bash\r file not found.
    # dos2unix .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/imouse/gradlew
