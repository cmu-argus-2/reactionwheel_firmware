#include <Arduino.h>

#include <SimpleFOC.h>

// BLDC motor instance.
//  BLDCMotor(int pp, (optional R, KV))
//  - pp  - pole pair number
//  - R   - phase resistance value - optional
//  - KV  - motor KV rating [rpm/V] - optional
BLDCMotor motor = BLDCMotor(6, 2.03);
// Setup 3-pin PWM BLDC driver. Instantiating this class will initialize all the
// necessary PWM timer/counters for the current board type.
BLDCDriver3PWM driver = BLDCDriver3PWM(11, 10, 9, 8);

// MagneticSensorI2C(uint8_t _chip_address, float _cpr, uint8_t _angle_register_msb)
//  chip_address         - I2C chip address
//  bit_resolution       - resolution of the sensor. 12 for AS5600.
//  angle_register_msb   - angle read register msb. 0x0E for AS5600.
//  bits_used_msb        - number of used bits in msb register
// MagneticSensorI2C sensor = MagneticSensorI2C(0x36, 12, 0x0E, 4);
//  instance of AS5600 sensor (provided in
//  https://docs.simplefoc.com/magnetic_sensor_i2c#quick-configuration-for-common-sensors)
MagneticSensorI2C sensor = MagneticSensorI2C(AS5600_I2C);

// instantiate the commander
Commander command = Commander(Serial);
void doTarget(char* cmd) { command.scalar(&motor.target, cmd); }
void doLimit(char* cmd) { command.scalar(&motor.voltage_limit, cmd); }
void onTarget(char* cmd){ command.target(&motor,cmd); }

void setup() {

  // use monitoring with serial
  Serial.begin(115200);
  // enable more verbose output for debugging
  // comment out if not needed
  SimpleFOCDebug::enable(&Serial);

  // pwm frequency to be used [Hz]
  // for atmega328 fixed to 32kHz
  // esp32/stm32/teensy configurable
  driver.pwm_frequency = 32000; // originally 32 kHz, 4 kHz looks a LITTLE better / less cogging.
  // power supply voltage [V]
  driver.voltage_power_supply = 8;
  // Max DC voltage allowed. Defaults to voltage_power_supply
  // 2.5" Hard Drive: Each phase's windings == 4 Ohms, and probably shouldn't
  // have any more than 500 mA == 0.5 A through them at any given time.
  // Therefore, set maximum voltage to 2 to limit current to 0.5 A.
  driver.voltage_limit = 2.5;

  // driver init
  if (!driver.init()){
    Serial.println("Driver init failed!");
    return;
  }
  Serial.println("Driver successfully initialized!");

  // configure i2C
  Wire.setClock(400000);
  // initialise magnetic sensor hardware
  sensor.init();
  Serial.println("Sensor ready");

  // link the motor and the driver
  motor.linkDriver(&driver);
  // link the motor and the sensor.
  motor.linkSensor(&sensor);

  // Adding motor constraints.
  // Set the resistance of each motor phase. Note that this is the resistance
  // Of an invidual phase to the common pin. If you're measuring from one phase
  // to another in wye config, divide that resistance by two.
  motor.phase_resistance = 2.03;
  // limit the voltage to be set to the motor
  // start very low for high resistance motors
  // current = voltage / resistance, so try to be well under 1Amp
  motor.current_limit = 0.6;
  // NOTE: I think adjusting this current limit is ultimately what will limit
  // our top speed--as if we can't torque enough at speed, then we can't
  // accelerate. Back-EMF will also play a role, but just keep this in mind.
  // Driver max voltage is also an upper bound to watch.

  // open loop control config
  // motor.controller = MotionControlType::velocity;

  // Closed-loop control config
  motor.torque_controller = TorqueControlType::voltage;
  motor.controller = MotionControlType::torque;
  motor.voltage_sensor_align = 0.6;

  // init motor hardware
  if(!motor.init()){
    Serial.println("Motor init failed!");
    return;
  }
  Serial.println("Motor successfully initialized!");

  // TODO: Initialize FOC?
  if (!motor.initFOC()) {
    Serial.println("Motor FOC init failed!");
  }
  Serial.println("Motor FOC initialized successfully!");

  // set the target velocity [rad/s]
  motor.target = 1; // Closed loop, this is a voltage

  // add target command T
  command.add('T', doTarget, "target");
  command.add('L', doLimit, "voltage limit");
  command.add('M',onTarget,"target setting");

  // // enable driver
  // driver.enable(); // This should bring pin 8 high == connected to the DRV8313 enable pin.
  // Serial.println("Driver ready!");
  // _delay(1000);

  Serial.println("Motor ready!");
  Serial.println("Set target velocity [rad/s]");
  _delay(1000);
}

void loop() {
    // // setting pwm
    // // phase A: 3V
    // // phase B: 4V
    // // phase C: 5V
    // driver.setPwm(3,4,5);

    // open loop velocity movement
    // using motor.voltage_limit and motor.velocity_limit
    // to turn the motor "backwards", just set a negative target_velocity
    // motor.move(target_velocity);
    motor.loopFOC();
    motor.move();

    // user communication
    command.run();
}