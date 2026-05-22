import CoreMIDI
import Foundation

let sourceName = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "V61 (Out)"
let destinationName = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "V61 (In)"

func check(_ status: OSStatus, _ message: String) {
    if status != noErr {
        fputs("\(message): OSStatus \(status)\n", stderr)
        exit(1)
    }
}

var client = MIDIClientRef()
check(MIDIClientCreate("Codex Ableton MIDI Ports" as CFString, nil, nil, &client), "MIDIClientCreate failed")

var source = MIDIEndpointRef()
check(MIDISourceCreate(client, sourceName as CFString, &source), "MIDISourceCreate failed")

var destination = MIDIEndpointRef()
check(
    MIDIDestinationCreateWithBlock(client, destinationName as CFString, &destination) { _packetList, _srcConnRefCon in
    },
    "MIDIDestinationCreateWithBlock failed"
)

print("Codex MIDI ports ready: input='\(sourceName)' output='\(destinationName)'")
fflush(stdout)
RunLoop.current.run()

