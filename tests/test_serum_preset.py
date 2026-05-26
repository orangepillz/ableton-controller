import struct
import unittest
import zlib
from pathlib import Path

from ableton_controller.parser import build_parser
from ableton_controller.serum_preset import (
    build_vstpreset_from_fxp,
    default_output_path,
    extract_fxp_component,
    patch_serum_state_name,
    serum_build_controls,
)


def fake_vstpreset(component: bytes = b"old") -> bytes:
    header = bytearray(b"VST3" + b"\x01\x00\x00\x00" + b"0" * 32 + b"\x00" * 8)
    info = b"<MetaInfo><Attribute id='PlugInName' value='Serum'/></MetaInfo>"
    info_offset = 48 + len(component)
    list_offset = info_offset + len(info)
    struct.pack_into("<Q", header, 40, list_offset)
    footer = bytearray()
    footer += b"List"
    footer += struct.pack("<I", 3)
    footer += b"Comp" + struct.pack("<Q", 48) + struct.pack("<Q", len(component))
    footer += b"Cont" + struct.pack("<Q", info_offset) + struct.pack("<Q", 0)
    footer += b"Info" + struct.pack("<Q", info_offset) + struct.pack("<Q", len(info))
    return bytes(header) + component + info + bytes(footer)


def fake_serum_fxp(state: bytes) -> bytes:
    component = zlib.compress(state, level=1)
    header = bytearray(60)
    header[:4] = b"CcnK"
    header[8:12] = b"FPCh"
    struct.pack_into(">I", header, 56, len(component))
    return bytes(header) + component


class SerumPresetTests(unittest.TestCase):
    def test_serum_build_preset_parser(self):
        args = build_parser().parse_args(
            [
                "serum-build-preset",
                "--name",
                "Codex Bass",
                "--controls",
                '[{"param":"A Vol","value":64}]',
                "--output",
                "/private/tmp/Codex Bass.vstpreset",
            ]
        )

        self.assertEqual(args.command, "serum-build-preset")
        self.assertEqual(args.name, "Codex Bass")
        self.assertEqual(args.output, Path("/private/tmp/Codex Bass.vstpreset"))

    def test_serum_build_controls_accepts_param_or_id(self):
        self.assertEqual(
            serum_build_controls([{"param": "A Vol", "normalized": 0.64}, {"id": 45, "value": 0.3}]),
            [{"param": "A Vol", "normalized": 0.64}, {"id": 45, "value": 0.3}],
        )
        with self.assertRaises(SystemExit):
            serum_build_controls([{"param": "A Vol", "id": 1, "value": 12}])
        with self.assertRaises(SystemExit):
            serum_build_controls([{"param": "A Vol", "value": 12, "normalized": 0.12}])

    def test_extract_fxp_component_validates_chunk(self):
        component = extract_fxp_component(fake_serum_fxp(b"state"))
        self.assertEqual(zlib.decompress(component), b"state")
        with self.assertRaises(ValueError):
            extract_fxp_component(b"nope")

    def test_patch_serum_state_name_replaces_init_name(self):
        state = b"abc - Init - \x00" + (b"\x00" * 200) + b"tail"

        patched = patch_serum_state_name(state, "Codex Hollow Bass")

        self.assertIn(b"Codex Hollow Bass\x00", patched)
        self.assertNotIn(b" - Init - ", patched)

    def test_build_vstpreset_from_fxp_replaces_component_and_preserves_info(self):
        state = b"abc - Init - \x00" + (b"\x00" * 200)
        template = fake_vstpreset(zlib.compress(b"old", level=1))

        preset = build_vstpreset_from_fxp(fake_serum_fxp(state), template, "Codex Bass")
        list_offset = struct.unpack_from("<Q", preset, 40)[0]
        self.assertEqual(preset[list_offset : list_offset + 4], b"List")
        count = struct.unpack_from("<I", preset, list_offset + 4)[0]
        self.assertEqual(count, 3)
        comp_offset = struct.unpack_from("<Q", preset, list_offset + 12)[0]
        comp_size = struct.unpack_from("<Q", preset, list_offset + 20)[0]
        component = preset[comp_offset : comp_offset + comp_size]

        self.assertIn(b" - Init - ", zlib.decompress(component))
        self.assertIn(b"PlugInName", preset)

    def test_default_output_path_is_sanitized(self):
        self.assertEqual(default_output_path(" Codex Hollow Bass! ").name, "Codex-Hollow-Bass.vstpreset")


if __name__ == "__main__":
    unittest.main()
