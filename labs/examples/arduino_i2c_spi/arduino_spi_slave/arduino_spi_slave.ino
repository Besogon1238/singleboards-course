#include <GyverBME280.h>
#include <SPI.h>
GyverBME280 bme;
volatile float         g_temp     = 0.0;
volatile float         g_hum      = 0.0;
volatile float         g_press    = 0.0;
volatile bool          g_ok       = false;
volatile byte          g_buf[12];
volatile byte          g_idx      = 0;
volatile bool          g_done     = false;
volatile unsigned int  g_cnt      = 0;

void buf_load() {
  float t = g_temp;
  float h = g_hum;
  float p = g_press;
  noInterrupts();
  if (g_ok) {
    memcpy((void*)(g_buf + 0), &t, 4);
    memcpy((void*)(g_buf + 4), &h, 4);
    memcpy((void*)(g_buf + 8), &p, 4);
  }
  g_idx  = 0;
  SPDR   = g_buf[0];
  g_done = false;
  interrupts();
}
ISR(SPI_STC_vect) {
  (void)SPDR;
  g_idx++;
  if (g_idx < 12) {
    SPDR = g_buf[g_idx];
  } else {
    g_idx  = 0;
    g_done = true;
  }
  g_cnt++;
}
void setup() {
  Serial.begin(115200);
  delay(500);
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.println(F("Arduino SPI Slave + BME280"));
  Serial.println(F("=========================="));
  Wire.begin();
  if (bme.begin()) {
    g_ok = true;
    Serial.println(F("BME280 OK (I2C 0x76)"));
  } else {
    g_ok = false;
    Serial.println(F("ERROR: BME280 not found!"));
    Serial.println(F("Check SDA(A4), SCL(A5), 3.3V, GND."));
  }
  pinMode(SS,   INPUT_PULLUP);
  pinMode(SCK,  INPUT);
  pinMode(MOSI, INPUT);
  pinMode(MISO, OUTPUT);
  SPCR = _BV(SPE) | _BV(SPIE);
  sei();
  buf_load();
  Serial.println(F("SPI slave ready. Waiting for Lichee master..."));
  Serial.println(F("=============================================="));
}
void loop() {
  static uint32_t last = 0;
  uint32_t now = millis();
  if (now - last >= 1000) {
    if (g_ok) {
//      noInterrupts();
      g_temp  = bme.readTemperature();
      g_hum   = bme.readHumidity();
      g_press = bme.readPressure() / 100.0;
//      interrupts();
    }
    Serial.print(F("T:"));
    Serial.print(g_temp, 1);
    Serial.print(F(" H:"));
    Serial.print(g_hum, 1);
    Serial.print(F(" P:"));
    Serial.print(g_press, 1);
    Serial.print(F(" cnt:"));
    Serial.println(g_cnt);
    last = now;
  }
  if (g_done) {
    buf_load();
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }
}
