#define COILS 8
#define SEP ','
#define END '\n'



int all_fire_pins[8] = {25, 29, 33, 37, 41, 45, 49, 53};
int all_sensor_pins[8] = {39, 27, 31, 47, 51, 23, 43, 35};
int all_voltage_pins[8] = {A7, A6, A5, A4, A3, A2, A1, A0};
int all_drain_pins[8] = {24, 28, 32, 36, 40, 44, 48, 52};
int all_HV_pins[8] = {22, 26, 30, 34, 38, 42, 46, 50};
int MAIN_HV_PIN = 13;
int fire_pins[COILS];
int sensor_pins[COILS];
int voltage_pins[COILS];
int drain_pins[COILS];
int HV_pins[COILS];

enum CoilgunState { OFFLINE, CHARGE, CHARGE_DONE, COUNTDOWN, FIRE };
CoilgunState currentState =  OFFLINE;

void setup() {
  // Setup all the pins
  for(int i=0; i < COILS ; i++) {
    fire_pins[i] = all_fire_pins[i];
    sensor_pins[i] = all_sensor_pins[i];
    voltage_pins[i] = all_voltage_pins[i];
    drain_pins[i] = all_drain_pins[i];
    HV_pins[i] = all_HV_pins[i];
  }
  
  for (int i = 0; i < 8; i++) {
    pinMode(all_fire_pins[i], OUTPUT);
    pinMode(all_sensor_pins[i], INPUT);
    pinMode(all_voltage_pins[i], INPUT);
    pinMode(all_drain_pins[i], OUTPUT);
    pinMode(all_HV_pins[i], OUTPUT);
    digitalWrite(all_fire_pins[i], LOW);

  }
  pinMode(MAIN_HV_PIN, OUTPUT);
  SetPins(all_HV_pins, "00000000", 8);
  // Begin serial communication
  Serial.begin(115200);

  // Setup LED strip
  setupLED();
}

void loop() {
  // put your main code here, to run repeatedly:

  String command = ReadSerial();

  if (command == "FIRE") {
    Fire();
  }
  else if (command == "VOLTAGE") {
    ReadVoltage();
  }
  else if (command == "ON") {
    ON();
  }
  else if (command == "OFF") {
    OFF();
  }
  else if (command == "HV") {
    HV();
  }
  else if (command == "DRAIN") {
    Drain();
  }
  else if (command == "SENSORS") {
    ReadSensors();
  }
  else if (command == "CHARGE") {
    Charge();
  }
  else if (command == "BLINK") {
    Blink();
  }
  else if (command == "DISPLAY_CHARGE") {
    DisplayCharge();
  }
  else if (command == "COUNTDOWN") {
    Countdown();
  }
  else if (command == "ABORT") {
    PrintSerial("ABORTING");
  }
  else if (command == "TEST") {
    PrintSerial("OK");
  }
  else {
    PrintSerial("UNKNOWN COMMAND... : " + command);
  }
}

String ReadSerial() {
  while (Serial.available() == 0) {
    // Wait for serial comunication and light up the LED-strip
    switch (currentState) {
      case OFFLINE: loopLED(); break;
      case CHARGE: break;
      case CHARGE_DONE: BlinkLED(); break;
      case COUNTDOWN: countdownLED(); break;
      case FIRE: break;
      default: break;
    }
  }
  // Flush serial
  delay(1);
  while (Serial.available() > 0) { Serial.read(); }

  // Read actual data
  PrintSerial("OK");
  return Serial.readStringUntil(END);
}

void PrintSerial(String message) {
  Serial.print(message);
  Serial.print(END);
}

void SendData(unsigned long data[], int size_of_data) {
  String content = "";
  for (int i = 0; i < size_of_data; i++) {
    if (i > 0) {
      content += SEP;
    }
    content += data[i];
  }
  PrintSerial(content);
}

void Countdown() {
  currentState = COUNTDOWN;
  startCountdownLed();
  PrintSerial("COUNTDOWN STARTED");
}

void Charge() {
  currentState = CHARGE;
  ChargeBar(0.0);
  PrintSerial("CHARGING COILGUN");
}

void DisplayCharge() {
  float charge_percent = ReadSerial().toFloat();
  ChargeBar(charge_percent);
  PrintSerial((String)"DISPLAY SET TO: " + charge_percent);
}

void Blink() {
  StartBlink();
  currentState = CHARGE_DONE;
}

void ON() {
  digitalWrite(MAIN_HV_PIN, LOW);
  PrintSerial("HV ON");
}

void OFF() {
  digitalWrite(MAIN_HV_PIN, HIGH);
  PrintSerial("HV OFF");
}

void Fire() {
  currentState = FIRE;
  // Shutdown LED-strip
  ChargeBar(0.0);
  unsigned long blocking_times[COILS];
  unsigned long trigger_time[COILS];
  unsigned long start_time = micros();

  // Fire the coils and read there velocity (blocking time)
  for (int i = 0; i < COILS; i++) {
    digitalWrite(fire_pins[i], HIGH);
    delayMicroseconds(10);
    blocking_times[i] = pulseIn(sensor_pins[i], LOW, 100000);
    trigger_time[i] = micros() - start_time;
  }

  // Reset all the pins
  for (int i = 0; i < COILS; i++) {
    digitalWrite(fire_pins[i], LOW);
  }

  SendData(blocking_times, COILS);
  SendData(trigger_time, COILS);
  currentState = OFFLINE;
}

void ReadVoltage() {
  unsigned long voltages[COILS];

  for (int i = 0; i < COILS; i++) {
    int average_voltage = 0;
    for (int j = 0; j < 4; j++) {
      average_voltage += analogRead(voltage_pins[i]);
    }
    voltages[i] = (unsigned long) (average_voltage / 4);
  }

  SendData(voltages, COILS);
}

void HV() {
  // Get a string of zeros and ones from the computer
  // Turn on HV for all the coils that has a 1
  String HV_command = ReadSerial();
  SetPins(HV_pins, HV_command, COILS);
  PrintSerial("HV pins set to: " + HV_command);
}

void Drain() {
  // Get a string of zeros and ones from the computer
  // Drain the all CBs that has a 1
  String drain_command = ReadSerial();
  SetPins(drain_pins, drain_command, COILS);
  PrintSerial("Drain pins set to: " + drain_command);
}

void ReadSensors() {
  unsigned long states[COILS];
  for (int i = 0; i < COILS; i++) {
    states[i] = digitalRead(sensor_pins[i]);
  }
  SendData(states, COILS);
}

void SetPins(int pins[], String pin_states, int nb_pins) {
  if (pin_states != "ABORT") {
    for (int i = 0; i < nb_pins; i++) {
      digitalWrite(pins[i], pin_states[i] == '1');
    }
  }
  else {
    PrintSerial("ABORTING");
  }
}
