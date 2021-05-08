
#include "IRTool.h"


volatile bool lockIr = false;  // Primitive locking for gating the IR LED.
uint32_t sendReqCounter = 0;
uint32_t lastSendTime = 0;

void debug(const char *str) {
#if DEBUG
  if (isSerialGpioUsedByIr()) return;  // Abort.
  uint32_t now = millis();
  Serial.printf("%07u.%03u: %s\n", now / 1000, now % 1000, str);
#endif  // DEBUG
}

void doRestart(const char* str, const bool serial_only) {
//#if MQTT_ENABLE
//  if (!serial_only)
//    mqttLog(str);
//  else
//#endif  // MQTT_ENABLE
//    debug(str);
//  delay(2000);  // Enough time for messages to be sent.
  ESP.restart();
  delay(5000);  // Enough time to ensure we don't return.
}

// Count how many values are in the String.
// Args:
//   str:  String containing the values.
//   sep:  Character that separates the values.
// Returns:
//   The number of values found in the String.
uint16_t countValuesInStr(const String str, char sep) {
  int16_t index = -1;
  uint16_t count = 1;
  do {
    index = str.indexOf(sep, index + 1);
    count++;
  } while (index != -1);
  return count;
}

// Dynamically allocate an array of uint16_t's.
// Args:
//   size:  Nr. of uint16_t's need to be in the new array.
// Returns:
//   A Ptr to the new array. Restarts the ESP if it fails.
uint16_t * newCodeArray(const uint16_t size) {
  uint16_t *result;

  result = reinterpret_cast<uint16_t*>(malloc(size * sizeof(uint16_t)));
  // Check we malloc'ed successfully.
  if (result == NULL)  // malloc failed, so give up.
    doRestart(
        "FATAL: Can't allocate memory for an array for a new message! "
        "Forcing a reboot!", true);  // Send to serial only as we are in low mem
  return result;
}


#if SEND_GLOBALCACHE
// Parse a GlobalCache String/code and send it.
// Args:
//   irsend: A ptr to the IRsend object to transmit via.
//   str: A GlobalCache formatted String of comma separated numbers.
//        e.g. "38000,1,1,170,170,20,63,20,63,20,63,20,20,20,20,20,20,20,20,20,
//              20,20,63,20,63,20,63,20,20,20,20,20,20,20,20,20,20,20,20,20,63,
//              20,20,20,20,20,20,20,20,20,20,20,20,20,63,20,20,20,63,20,63,20,
//              63,20,63,20,63,20,63,20,1798"
//        Note: The leading "1:1,1," of normal GC codes should be removed.
// Returns:
//   bool: Successfully sent or not.
bool parseStringAndSendGC(IRsend *irsend, const String str) {
  uint16_t count;
  uint16_t *code_array;
  String tmp_str;

  // Remove the leading "1:1,1," if present.
  if (str.startsWith("1:1,1,"))
    tmp_str = str.substring(6);
  else
    tmp_str = str;

  // Find out how many items there are in the string.
  count = countValuesInStr(tmp_str, ',');

  // Now we know how many there are, allocate the memory to store them all.
  code_array = newCodeArray(count);

  // Now convert the strings to integers and place them in code_array.
  count = 0;
  uint16_t start_from = 0;
  int16_t index = -1;
  do {
    index = tmp_str.indexOf(',', start_from);
    code_array[count] = tmp_str.substring(start_from, index).toInt();
    start_from = index + 1;
    count++;
  } while (index != -1);
  irsend->sendGC(code_array, count);  // All done. Send it.
  free(code_array);  // Free up the memory allocated.
  if (count > 0)
    return true;  // We sent something.
  return false;  // We probably didn't.
}
#endif  // SEND_GLOBALCACHE


// Parse an Air Conditioner A/C Hex String/code and send it.
// Args:
//   irsend: A Ptr to the IRsend object to transmit via.
//   irType: Nr. of the protocol we need to send.
//   str: A hexadecimal string containing the state to be sent.
// Returns:
//   bool: Successfully sent or not.
bool parseStringAndSendAirCon(IRsend *irsend, const decode_type_t irType,
                              const String str) {
  uint8_t strOffset = 0;
  uint8_t state[kStateSizeMax] = {0};  // All array elements are set to 0.
  uint16_t stateSize = 0;

  if (str.startsWith("0x") || str.startsWith("0X"))
    strOffset = 2;
  // Calculate how many hexadecimal characters there are.
  uint16_t inputLength = str.length() - strOffset;
  if (inputLength == 0) {
    debug("Zero length AirCon code encountered. Ignored.");
    return false;  // No input. Abort.
  }

  switch (irType) {  // Get the correct state size for the protocol.
    case DAIKIN:
      // Daikin has 2 different possible size states.
      // (The correct size, and a legacy shorter size.)
      // Guess which one we are being presented with based on the number of
      // hexadecimal digits provided. i.e. Zero-pad if you need to to get
      // the correct length/byte size.
      // This should provide backward compatiblity with legacy messages.
      stateSize = inputLength / 2;  // Every two hex chars is a byte.
      // Use at least the minimum size.
      stateSize = std::max(stateSize, kDaikinStateLengthShort);
      // If we think it isn't a "short" message.
      if (stateSize > kDaikinStateLengthShort)
        // Then it has to be at least the version of the "normal" size.
        stateSize = std::max(stateSize, kDaikinStateLength);
      // Lastly, it should never exceed the "normal" size.
      stateSize = std::min(stateSize, kDaikinStateLength);
      break;
    case FUJITSU_AC:
      // Fujitsu has four distinct & different size states, so make a best guess
      // which one we are being presented with based on the number of
      // hexadecimal digits provided. i.e. Zero-pad if you need to to get
      // the correct length/byte size.
      stateSize = inputLength / 2;  // Every two hex chars is a byte.
      // Use at least the minimum size.
      stateSize = std::max(stateSize,
                           (uint16_t) (kFujitsuAcStateLengthShort - 1));
      // If we think it isn't a "short" message.
      if (stateSize > kFujitsuAcStateLengthShort)
        // Then it has to be at least the smaller version of the "normal" size.
        stateSize = std::max(stateSize, (uint16_t) (kFujitsuAcStateLength - 1));
      // Lastly, it should never exceed the maximum "normal" size.
      stateSize = std::min(stateSize, kFujitsuAcStateLength);
      break;
    case HITACHI_AC3:
      // HitachiAc3 has two distinct & different size states, so make a best
      // guess which one we are being presented with based on the number of
      // hexadecimal digits provided. i.e. Zero-pad if you need to to get
      // the correct length/byte size.
      stateSize = inputLength / 2;  // Every two hex chars is a byte.
      // Use at least the minimum size.
      stateSize = std::max(stateSize,
                           (uint16_t) (kHitachiAc3MinStateLength));
      // If we think it isn't a "short" message.
      if (stateSize > kHitachiAc3MinStateLength)
        // Then it probably the "normal" size.
        stateSize = std::max(stateSize,
                             (uint16_t) (kHitachiAc3StateLength));
      // Lastly, it should never exceed the maximum "normal" size.
      stateSize = std::min(stateSize, kHitachiAc3StateLength);
      break;
    case MWM:
      // MWM has variable size states, so make a best guess
      // which one we are being presented with based on the number of
      // hexadecimal digits provided. i.e. Zero-pad if you need to to get
      // the correct length/byte size.
      stateSize = inputLength / 2;  // Every two hex chars is a byte.
      // Use at least the minimum size.
      stateSize = std::max(stateSize, (uint16_t) 3);
      // Cap the maximum size.
      stateSize = std::min(stateSize, kStateSizeMax);
      break;
    case SAMSUNG_AC:
      // Samsung has two distinct & different size states, so make a best guess
      // which one we are being presented with based on the number of
      // hexadecimal digits provided. i.e. Zero-pad if you need to to get
      // the correct length/byte size.
      stateSize = inputLength / 2;  // Every two hex chars is a byte.
      // Use at least the minimum size.
      stateSize = std::max(stateSize, (uint16_t) (kSamsungAcStateLength));
      // If we think it isn't a "normal" message.
      if (stateSize > kSamsungAcStateLength)
        // Then it probably the extended size.
        stateSize = std::max(stateSize,
                             (uint16_t) (kSamsungAcExtendedStateLength));
      // Lastly, it should never exceed the maximum "extended" size.
      stateSize = std::min(stateSize, kSamsungAcExtendedStateLength);
      break;
    default:  // Everything else.
      stateSize = IRsend::defaultBits(irType) / 8;
      if (!stateSize || !hasACState(irType)) {
        // Not a protocol we expected. Abort.
        debug("Unexpected AirCon protocol detected. Ignoring.");
        return false;
      }
  }
  if (inputLength > stateSize * 2) {
    debug("AirCon code to large for the given protocol.");
    return false;
  }

  // Ptr to the least significant byte of the resulting state for this protocol.
  uint8_t *statePtr = &state[stateSize - 1];

  // Convert the string into a state array of the correct length.
  for (uint16_t i = 0; i < inputLength; i++) {
    // Grab the next least sigificant hexadecimal digit from the string.
    uint8_t c = tolower(str[inputLength + strOffset - i - 1]);
    if (isxdigit(c)) {
      if (isdigit(c))
        c -= '0';
      else
        c = c - 'a' + 10;
    } else {
      debug("Aborting! Non-hexadecimal char found in AirCon state:");
      debug(str.c_str());
      return false;
    }
    if (i % 2 == 1) {  // Odd: Upper half of the byte.
      *statePtr += (c << 4);
      statePtr--;  // Advance up to the next least significant byte of state.
    } else {  // Even: Lower half of the byte.
      *statePtr = c;
    }
  }
  if (!irsend->send(irType, state, stateSize)) {
    debug("Unexpected AirCon type in send request. Not sent.");
    return false;
  }
  return true;  // We were successful as far as we can tell.
}

#if SEND_PRONTO
// Parse a Pronto Hex String/code and send it.
// Args:
//   irsend: A ptr to the IRsend object to transmit via.
//   str: A comma-separated String of nr. of repeats, then hexadecimal numbers.
//        e.g. "R1,0000,0067,0000,0015,0060,0018,0018,0018,0030,0018,0030,0018,
//              0030,0018,0018,0018,0030,0018,0018,0018,0018,0018,0030,0018,
//              0018,0018,0030,0018,0030,0018,0030,0018,0018,0018,0018,0018,
//              0030,0018,0018,0018,0018,0018,0030,0018,0018,03f6"
//              or
//              "0000,0067,0000,0015,0060,0018". i.e. without the Repeat value
//        Requires at least kProntoMinLength comma-separated values.
//        sendPronto() only supports raw pronto code types, thus so does this.
//   repeats:  Nr. of times the message is to be repeated.
//             This value is ignored if an embeddd repeat is found in str.
// Returns:
//   bool: Successfully sent or not.
bool parseStringAndSendPronto(IRsend *irsend, const String str,
                              uint16_t repeats) {
  uint16_t count;
  uint16_t *code_array;
  int16_t index = -1;
  uint16_t start_from = 0;

  // Find out how many items there are in the string.
  count = countValuesInStr(str, ',');

  // Check if we have the optional embedded repeats value in the code string.
  if (str.startsWith("R") || str.startsWith("r")) {
    // Grab the first value from the string, as it is the nr. of repeats.
    index = str.indexOf(',', start_from);
    repeats = str.substring(start_from + 1, index).toInt();  // Skip the 'R'.
    start_from = index + 1;
    count--;  // We don't count the repeats value as part of the code array.
  }

  // We need at least kProntoMinLength values for the code part.
  if (count < kProntoMinLength) return false;

  // Now we know how many there are, allocate the memory to store them all.
  code_array = newCodeArray(count);

  // Rest of the string are values for the code array.
  // Now convert the hex strings to integers and place them in code_array.
  count = 0;
  do {
    index = str.indexOf(',', start_from);
    // Convert the hexadecimal value string to an unsigned integer.
    code_array[count] = strtoul(str.substring(start_from, index).c_str(),
                                NULL, 16);
    start_from = index + 1;
    count++;
  } while (index != -1);

  irsend->sendPronto(code_array, count, repeats);  // All done. Send it.
  free(code_array);  // Free up the memory allocated.
  if (count > 0)
    return true;  // We sent something.
  return false;  // We probably didn't.
}
#endif  // SEND_PRONTO

#if SEND_RAW
// Parse an IRremote Raw String/code and send it.
// Args:
//   irsend: A ptr to the IRsend object to transmit via.
//   str: A comma-separated String containing the freq and raw IR data.
//        e.g. "38000,9000,4500,600,1450,600,900,650,1500,..."
//        Requires at least two comma-separated values.
//        First value is the transmission frequency in Hz or kHz.
// Returns:
//   bool: Successfully sent or not.
bool parseStringAndSendRaw(IRsend *irsend, const String str) {
  uint16_t count;
  uint16_t freq = 38000;  // Default to 38kHz.
  uint16_t *raw_array;

  // Find out how many items there are in the string.
  count = countValuesInStr(str, ',');

  // We expect the frequency as the first comma separated value, so we need at
  // least two values. If not, bail out.
  if (count < 2)  return false;
  count--;  // We don't count the frequency value as part of the raw array.

  // Now we know how many there are, allocate the memory to store them all.
  raw_array = newCodeArray(count);

  // Grab the first value from the string, as it is the frequency.
  int16_t index = str.indexOf(',', 0);
  freq = str.substring(0, index).toInt();
  uint16_t start_from = index + 1;
  // Rest of the string are values for the raw array.
  // Now convert the strings to integers and place them in raw_array.
  count = 0;
  do {
    index = str.indexOf(',', start_from);
    raw_array[count] = str.substring(start_from, index).toInt();
    start_from = index + 1;
    count++;
  } while (index != -1);

  irsend->sendRaw(raw_array, count, freq);  // All done. Send it.
  free(raw_array);  // Free up the memory allocated.
  if (count > 0)
    return true;  // We sent something.
  return false;  // We probably didn't.
}
#endif  // SEND_RAW


// Transmit the given IR message.
//
// Args:
//   irsend:   A pointer to a IRsend object to transmit via.
//   ir_type:  enum of the protocol to be sent.
//   code:     Numeric payload of the IR message. Most protocols use this.
//   code_str: The unparsed code to be sent. Used by complex protocol encodings.
//   bits:     Nr. of bits in the protocol. 0 means use the protocol's default.
//   repeat:   Nr. of times the message is to be repeated. (Not all protocols.)
// Returns:
//   bool: Successfully sent or not.
bool sendIRCode(IRsend *irsend, decode_type_t const ir_type,
                uint64_t const code, char const * code_str, uint16_t bits,
                uint16_t repeat) {
  if (irsend == NULL) return false;
  bool success = true;  // Assume success.
  // Ensure we have enough repeats.
  repeat = std::max(IRsend::minRepeats(ir_type), repeat);
  if (bits == 0) bits = IRsend::defaultBits(ir_type);
  // Create a pseudo-lock so we don't try to send two codes at the same time.
  while (lockIr)
    delay(20);
  lockIr = true;


  // Turn off IR capture if we need to.
#if IR_RX && DISABLE_CAPTURE_WHILE_TRANSMITTING
  if (irrecv != NULL) irrecv->disableIRIn();  // Stop the IR receiver
#endif  // IR_RX && DISABLE_CAPTURE_WHILE_TRANSMITTING
  // send the IR message.
  switch (ir_type) {
#if SEND_PRONTO
    case decode_type_t::PRONTO:  // 25
      success = parseStringAndSendPronto(irsend, code_str, repeat);
      break;
#endif  // SEND_PRONTO
    case decode_type_t::RAW:  // 30
#if SEND_RAW
      success = parseStringAndSendRaw(irsend, code_str);
      break;
#endif
#if SEND_GLOBALCACHE
    case decode_type_t::GLOBALCACHE:  // 31
      success = parseStringAndSendGC(irsend, code_str);
      break;
#endif
    default:  // Everything else.
      if (hasACState(ir_type))  // protocols with > 64 bits
        success = parseStringAndSendAirCon(irsend, ir_type, code_str);
      else  // protocols with <= 64 bits
        success = irsend->send(ir_type, code, bits, repeat);
  }
#if IR_RX && DISABLE_CAPTURE_WHILE_TRANSMITTING
  // Turn IR capture back on if we need to.
  if (irrecv != NULL) irrecv->enableIRIn();  // Restart the receiver
#endif  // IR_RX && DISABLE_CAPTURE_WHILE_TRANSMITTING
  lastSendTime = millis();
  // Release the lock.
  lockIr = false;

  // Indicate that we sent the message or not.
  if (success) {
    sendReqCounter++;
    debug("Sent the IR message:");
  } else {
    debug("Failed to send IR Message:");
  }
  debug(D_STR_PROTOCOL ": ");
  debug(String(ir_type).c_str());
  // For "long" codes we basically repeat what we got.
  if (hasACState(ir_type) || ir_type == PRONTO || ir_type == RAW ||
      ir_type == GLOBALCACHE) {
    debug(D_STR_CODE ": ");
    debug(code_str);
    // Confirm what we were asked to send was sent.
#if MQTT_ENABLE
//    if (success) {
//      if (ir_type == PRONTO && repeat > 0)
//        mqtt_client.publish(MqttAck.c_str(), (String(ir_type) +
//                                              kCommandDelimiter[0] + 'R' +
//                                              String(repeat) +
//                                              kCommandDelimiter[0] +
//                                              String(code_str)).c_str());
//      else
//        mqtt_client.publish(MqttAck.c_str(), (String(ir_type) +
//                                              kCommandDelimiter[0] +
//                                              String(code_str)).c_str());
//      mqttSentCounter++;
//    }
#endif  // MQTT_ENABLE
  } else {  // For "short" codes, we break it down a bit more before we report.
    debug((D_STR_CODE ": 0x" + uint64ToString(code, 16)).c_str());
    debug((D_STR_BITS ": " + String(bits)).c_str());
    debug((D_STR_REPEAT ": " + String(repeat)).c_str());
#if MQTT_ENABLE
//    if (success) {
//      mqtt_client.publish(MqttAck.c_str(), (String(ir_type) +
//                                            kCommandDelimiter[0] +
//                                            uint64ToString(code, 16) +
//                                            kCommandDelimiter[0] +
//                                            String(bits) +
//                                            kCommandDelimiter[0] +
//                                            String(repeat)).c_str());
//      mqttSentCounter++;
//    }
#endif  // MQTT_ENABLE
  }
  return success;
}
