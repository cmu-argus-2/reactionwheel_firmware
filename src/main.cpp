#include <Arduino.h>

#include <SimpleFOC.h>

// Setup 3-pin PWM BLDC driver. Instantiating this class will initialize all the
// necessary PWM timer/counters for the current board type.
BLDCDriver3PWM driver = BLDCDriver3PWM(11, 10, 9, 8);

void setup() {

  // use monitoring with serial
  Serial.begin(115200);
  // enable more verbose output for debugging
  // comment out if not needed
  SimpleFOCDebug::enable(&Serial);

  // pwm frequency to be used [Hz]
  // for atmega328 fixed to 32kHz
  // esp32/stm32/teensy configurable
  driver.pwm_frequency = 32000;
  // power supply voltage [V]
  driver.voltage_power_supply = 10;
  // Max DC voltage allowed. Defaults to voltage_power_supply
  driver.voltage_limit = 5;

  // driver init
  if (!driver.init()){
    Serial.println("Driver init failed!");
    return;
  }
  else {
    Serial.println("Driver successfully initialized!");
  }

  // enable driver
  driver.enable(); // This should bring pin 8 high == connected to the DRV8313 enable pin.
  Serial.println("Driver ready!");
  _delay(1000);
}

void loop() {
    // setting pwm
    // phase A: 3V
    // phase B: 4V
    // phase C: 5V
    driver.setPwm(3,4,5);
}