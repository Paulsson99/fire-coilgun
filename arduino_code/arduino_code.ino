#define COILS 1
#define SEP ','
#define END '\n'

int fire_pins[COILS] = {20};
int sensor_pins[COILS] = {30};
int voltage_pins[COILS] = {A0};

void setup() {
  // Setup all the pins
  for (int i = 0; i < COILS; i++) {
    pinMode(fire_pins[i], OUTPUT);
    pinMode(sensor_pins[i], INPUT);
    pinMode(voltage_pins[i], INPUT);

    digitalWrite(fire_pins[i], LOW);
  }

  // Begin serial communication
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:

  while (Serial.available() == 0) {
    // Wait for command from the RP
  }

  String command = Serial.readStringUntil(END);

  if (command == "FIRE") {
    Fire();
  }
  else if (command == "VOLTAGE") {
    ReadVoltage();
  }
  else if (command == "TEST") {
    Serial.print("OK");
    Serial.print(END);
  }
  else {
    Serial.print("UNKNOWN COMMAND...");
    Serial.print(END);
  }
}

void SendData(unsigned long data[], int size_of_data) {
  String content = "";
  for (int i = 0; i < size_of_data; i++) {
    if (i > 0) {
      content += SEP;
    }
    content += data[i];
  }
  content += END;
  int test = Serial.print(content);
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
