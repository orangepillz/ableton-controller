#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$1"
PYTHON="$2"
shift 2

name=""
controls=""
output=""
template="$HOME/Music/Ableton/User Library/Serum.vstpreset"

usage() {
  printf '%s\n' "usage: abletonctl serum-build-preset --name NAME --controls JSON [--output FILE] [--template FILE]" >&2
  exit 2
}

sanitize_name() {
  printf '%s' "$1" | sed -E 's/[^A-Za-z0-9._-]+/-/g; s/^-+//; s/-+$//'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --name)
      [ "$#" -ge 2 ] || usage
      name="$2"
      shift 2
      ;;
    --controls)
      [ "$#" -ge 2 ] || usage
      controls="$2"
      shift 2
      ;;
    --output)
      [ "$#" -ge 2 ] || usage
      output="$2"
      shift 2
      ;;
    --template)
      [ "$#" -ge 2 ] || usage
      template="$2"
      shift 2
      ;;
    *)
      printf 'unknown serum-build-preset argument: %s\n' "$1" >&2
      usage
      ;;
  esac
done

[ -n "$name" ] || usage
[ -n "$controls" ] || usage
[ -f "$template" ] || { printf 'Serum VST3 template preset does not exist: %s\n' "$template" >&2; exit 1; }
if [ -z "$output" ]; then
  safe_name="$(sanitize_name "$name")"
  [ -n "$safe_name" ] || safe_name="Serum-Preset"
  output="/private/tmp/${safe_name}.vstpreset"
fi

controls_file="$(mktemp /private/tmp/serum-build-controls.XXXXXX)"
fxp_file="$(mktemp /private/tmp/serum-build-state.XXXXXX)"
result_file="$(mktemp /private/tmp/serum-build-result.XXXXXX)"
trap 'rm -f "$controls_file" "$fxp_file" "$result_file"' EXIT
printf '%s' "$controls" > "$controls_file"

/usr/bin/env CLANG_MODULE_CACHE_PATH=/private/tmp/codex-module-cache /usr/bin/swift - "$controls_file" "$fxp_file" "$result_file" <<'SWIFT'
import AudioToolbox
import Foundation

func die(_ message: String) -> Never {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
    exit(1)
}

func fourCC(_ text: String) -> OSType {
    var value: UInt32 = 0
    for byte in text.utf8 { value = (value << 8) | UInt32(byte) }
    return value
}

func norm(_ name: String) -> String { name.lowercased().filter { !$0.isWhitespace } }

func number(_ value: Any?) -> Double? {
    if let n = value as? NSNumber { return n.doubleValue }
    if let s = value as? String { return Double(s) }
    return nil
}

var desc = AudioComponentDescription(componentType: 0, componentSubType: 0, componentManufacturer: 0, componentFlags: 0, componentFlagsMask: 0)
var current: AudioComponent? = nil
var found: AudioComponent? = nil
while true {
    current = AudioComponentFindNext(current, &desc)
    guard let component = current else { break }
    var cd = AudioComponentDescription()
    AudioComponentGetDescription(component, &cd)
    var nameRef: Unmanaged<CFString>?
    AudioComponentCopyName(component, &nameRef)
    let componentName = nameRef?.takeRetainedValue() as String? ?? ""
    let exact = cd.componentType == fourCC("aumu") && cd.componentSubType == fourCC("XfsX") && cd.componentManufacturer == fourCC("XFER")
    if exact || componentName == "Xfer Records: Serum" {
        found = component
        break
    }
}
guard let component = found else { die("Serum Audio Unit component was not found") }

var instance: AudioComponentInstance?
guard AudioComponentInstanceNew(component, &instance) == noErr, let au = instance else { die("create Serum Audio Unit failed") }
defer {
    AudioUnitUninitialize(au)
    AudioComponentInstanceDispose(au)
}
guard AudioUnitInitialize(au) == noErr else { die("initialize Serum Audio Unit failed") }

var listSize: UInt32 = 0
var writable = DarwinBoolean(false)
guard AudioUnitGetPropertyInfo(au, kAudioUnitProperty_ParameterList, kAudioUnitScope_Global, 0, &listSize, &writable) == noErr else {
    die("read Serum parameter list size failed")
}
let count = Int(listSize) / MemoryLayout<AudioUnitParameterID>.size
var ids = [AudioUnitParameterID](repeating: 0, count: count)
guard AudioUnitGetProperty(au, kAudioUnitProperty_ParameterList, kAudioUnitScope_Global, 0, &ids, &listSize) == noErr else {
    die("read Serum parameter list failed")
}

var params: [[String: Any]] = []
for id in ids {
    var info = AudioUnitParameterInfo()
    var infoSize = UInt32(MemoryLayout<AudioUnitParameterInfo>.size)
    guard AudioUnitGetProperty(au, kAudioUnitProperty_ParameterInfo, kAudioUnitScope_Global, id, &info, &infoSize) == noErr else {
        die("read Serum parameter info failed")
    }
    params.append([
        "id": Int(id),
        "name": info.cfNameString?.takeUnretainedValue() as String? ?? String(id),
        "minimum": Double(info.minValue),
        "maximum": Double(info.maxValue)
    ])
}

let controlsData = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))
guard let controls = try JSONSerialization.jsonObject(with: controlsData) as? [[String: Any]] else {
    die("controls JSON must be a list of objects")
}

var applied: [[String: Any]] = []
for (index, control) in controls.enumerated() {
    let param: [String: Any]
    if let idNumber = number(control["id"]) {
        let id = Int(idNumber)
        guard let match = params.first(where: { ($0["id"] as? Int) == id }) else { die("Unknown Serum parameter id \(id)") }
        param = match
    } else if let name = control["param"] as? String {
        let matches = params.filter { norm(($0["name"] as? String) ?? "") == norm(name) }
        guard matches.count == 1 else { die(matches.isEmpty ? "Unknown Serum parameter '\(name)'" : "Ambiguous Serum parameter '\(name)'") }
        param = matches[0]
    } else {
        die("Serum control \(index) needs param or id")
    }

    let hasValue = control["value"] != nil
    let hasNormalized = control["normalized"] != nil
    guard hasValue != hasNormalized else { die("Serum control \(index) needs exactly one of value or normalized") }
    let minimum = param["minimum"] as! Double
    let maximum = param["maximum"] as! Double
    let raw: Double
    if hasNormalized {
        guard let normalized = number(control["normalized"]) else { die("Serum control \(index) has non-numeric normalized value") }
        raw = minimum + (maximum - minimum) * min(1.0, max(0.0, normalized))
    } else {
        guard let value = number(control["value"]) else { die("Serum control \(index) has non-numeric value") }
        raw = value
    }
    let id = AudioUnitParameterID(param["id"] as! Int)
    let clamped = min(maximum, max(minimum, raw))
    guard AudioUnitSetParameter(au, id, kAudioUnitScope_Global, 0, AudioUnitParameterValue(clamped), 0) == noErr else {
        die("set Serum parameter failed")
    }
    var readback = AudioUnitParameterValue(0)
    AudioUnitGetParameter(au, id, kAudioUnitScope_Global, 0, &readback)
    applied.append(["id": Int(id), "param": param["name"] as! String, "minimum": minimum, "maximum": maximum, "value": Double(readback)])
}

var unmanaged: Unmanaged<CFPropertyList>?
var stateSize: UInt32 = 8
guard AudioUnitGetProperty(au, kAudioUnitProperty_ClassInfo, kAudioUnitScope_Global, 0, &unmanaged, &stateSize) == noErr,
      let classInfo = unmanaged?.takeRetainedValue() as? [AnyHashable: Any],
      let fxp = classInfo["vstdata"] as? Data else {
    die("Serum class info did not contain vstdata")
}
try fxp.write(to: URL(fileURLWithPath: CommandLine.arguments[2]))
let result = ["parameter_count": params.count, "controls": applied] as [String: Any]
let resultData = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
try resultData.write(to: URL(fileURLWithPath: CommandLine.arguments[3]))
SWIFT

PYTHONPATH="$PROJECT_ROOT" "$PYTHON" - "$fxp_file" "$template" "$output" "$name" "$result_file" <<'PY'
import json
import sys
from pathlib import Path

from ableton_controller.serum_preset import build_vstpreset_from_fxp

fxp_arg, template_arg, output_arg, name, result_arg = sys.argv[1:]
fxp_path = Path(fxp_arg)
template_path = Path(template_arg)
output_path = Path(output_arg)
result_path = Path(result_arg)
preset = build_vstpreset_from_fxp(fxp_path.read_bytes(), template_path.read_bytes(), name)
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_bytes(preset)
result = json.loads(result_path.read_text())
result.update({
    "command": "serum-build-preset",
    "control_count": len(result.get("controls", [])),
    "done": True,
    "name": str(name),
    "output": str(output_path),
    "template": str(template_path),
})
print(json.dumps(result, indent=2, sort_keys=True))
PY
