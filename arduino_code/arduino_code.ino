#define COILS 1
#define SEP ','
#define END '\n'

int fire_pins[COILS] = {11};
int sensor_pins[COILS] = {1};
int voltage_pins[COILS] = {A5};
int drain_pins[COILS] = {13};
int HV_pins[COILS] = {12};
int MAIN_HV_PIN = 10;

void setup() {
  // Setup all the pins
  for (int i = 0; i < COILS; i++) {
    pinMode(fire_pins[i], OUTPUT);
    pinMode(sensor_pins[i], INPUT);
    pinMode(voltage_pins[i], INPUT);
    pinMode(drain_pins[i], OUTPUT);
    pinMode(HV_pins[i], OUTPUT);

    digitalWrite(fire_pins[i], LOW);
  }
  pinMode(MAIN_HV_PIN, OUTPUT);

  // Begin serial communication
  Serial.begin(115200);
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
  else if (command == "TEST") {
    PrintSerial("OK");
  }
  else {
    PrintSerial("UNKNOWN COMMAND...");
  }
}

String ReadSerial() {
  while (Serial.available() == 0) {
    // Wait for command from the RP
  }

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

void ON() {
  digitalWrite(MAIN_HV_PIN, LOW);
  PrintSerial("HV ON");
}

void OFF() {
  digitalWrite(MAIN_HV_PIN, HIGH);
  PrintSerial("HV OFF");
}

void Fire() {
  unsigned long blocking_times[COILS];

  // Fire the coils and read there velocity (blocking time)
  for (int i = 0; i < COILS; i++) {
    digitalWrite(fire_pins[i], HIGH);
    blocking_times[i] = pulseIn(sensor_pins[i], LOW, 10000);
  }

  // Reset all the pins
  for (int i = 0; i < COILS; i++) {
    digitalWrite(fire_pins[i], LOW);
  }

  SendData(blocking_times, COILS);
}

void ReadVoltage() {
  unsigned long voltages[COILS];

  for (int i = 0; i < COILS; i++) {
    voltages[i] = (unsigned long) analogRead(voltage_pins[i]);
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

void SetPins(int pins[], String pin_states, int nb_pins) {
  for (int i = 0; i < nb_pins; i++) {
    digitalWrite(pins[i], pin_states[i] == '1');
  }
}
