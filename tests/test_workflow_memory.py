import unittest

from copilot_improvement.memory import default_memory
from copilot_improvement.personalization import sync_intent_mappings
from copilot_improvement.workflow_memory import derive_workflow_macros, sync_workflow_macros


class WorkflowMemoryTests(unittest.TestCase):
    def test_derive_workflow_macros_links_intent_evidence(self):
        memory = default_memory()
        memory["intent_mappings"] = [
            {
                "id": "mix-bus-control",
                "confidence": 0.37,
                "recommended_commands": ["workflow-macro render mix-bus-control"],
                "evidence_signal_ids": ["project.device.limiter", "project.name.master"],
                "status": "active",
            }
        ]

        macros = derive_workflow_macros(memory)
        mix = next(macro for macro in macros if macro["name"] == "mix-bus-control")

        self.assertGreater(mix["confidence"], 0.37)
        self.assertEqual(mix["linked_intent_ids"], ["mix-bus-control"])
        self.assertIn("project.device.limiter", mix["evidence_signal_ids"])
        self.assertIn("mixing", mix["tags"])

    def test_sync_workflow_macros_persists_catalog_without_duplicate_changes(self):
        memory = default_memory()
        memory["intent_mappings"] = [
            {
                "id": "bass-movement",
                "confidence": 0.5,
                "recommended_commands": ["workflow-macro render bass-movement"],
                "evidence_signal_ids": ["chat.intent.bass"],
                "status": "active",
            }
        ]

        first = sync_workflow_macros(memory)
        second = sync_workflow_macros(memory)

        self.assertTrue(any(update["name"] == "bass-movement" and update["changed"] for update in first))
        self.assertTrue(any(macro["name"] == "bass-movement" for macro in memory["workflow_macros"]))
        self.assertFalse(any(update["changed"] for update in second))

    def test_sync_links_followup_macros_from_derived_intents(self):
        memory = default_memory()
        memory["signals"] = [
            {"id": "project.name.bd", "category": "project.name", "label": "BD", "confidence": 0.4},
            {"id": "project.name.drums", "category": "project.name", "label": "Drums", "confidence": 0.4},
            {"id": "chat.intent.bass", "category": "chat.intent", "label": "bass", "confidence": 0.3},
            {"id": "chat.intent.movement", "category": "chat.intent", "label": "movement", "confidence": 0.3},
        ]

        sync_intent_mappings(memory)
        sync_workflow_macros(memory)
        macros = {macro["name"]: macro for macro in memory["workflow_macros"]}

        self.assertEqual(macros["drum-punch-bus"]["linked_intent_ids"], ["drum-kit-building"])
        self.assertEqual(macros["call-response-bass"]["linked_intent_ids"], ["bass-movement"])


if __name__ == "__main__":
    unittest.main()
