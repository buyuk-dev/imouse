BUILD_DIR=./build
CLIENT_SRC=./client
CALIB_SRC=./calibration
COMMON_SRC=./common
APK_DIR=./apk


# Make sure build directory exists
$(shell mkdir -p $(BUILD_DIR))


all: client calibration


client:
	@echo "Building Mouse Client APK..."
	cp -r $(CLIENT_SRC)/* $(BUILD_DIR)/
	cp -r $(COMMON_SRC) $(BUILD_DIR)/

	cd $(BUILD_DIR) && buildozer -v android debug
	mv $(BUILD_DIR)/bin/*.apk $(APK_DIR)/


calibration:
	@echo "Building Mouse Calibration APK..."
	cp -r $(CALIB_SRC)/* $(BUILD_DIR)/

	cd $(BUILD_DIR) && buildozer -v android debug
	mv $(BUILD_DIR)/bin/*.apk $(APK_DIR)/


clean:
	@echo "Cleaning build directory..."
	cd ${BUILD_DIR} && rm -rf *.py *.json *.ini *.spec common bin


.PHONY: all client calibration clean