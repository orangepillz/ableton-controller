import unittest

from copilot_improvement.memory import default_memory, upsert_signal
from copilot_improvement.personalization import derive_intent_mappings, render_profile, sync_intent_mappings


class PersonalizationTests(unittest.TestCase):
    def test_derive_intent_mappings_from_project_and_chat_signals(self):
        memory = default_memory()
        upsert_signal(memory, category="project.name", label="SC Trigger", evidence="Appeared in set.", source="set.als")
        upsert_signal(memory, category="project.name", label="BD", evidence="Appeared in set.", source="set.als")
        upsert_signal(memory, category="project.name", label="Drums", evidence="Appeared in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-phase", label="main-section-phase-bass-drums", evidence="Clip roles in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-marker", label="locator-marker-2-at-64-beats", evidence="Locator in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-shape", label="arrangement-start-grid-16-beats", evidence="Clip timing in set.", source="set.als")
        upsert_signal(memory, category="chat.intent", label="bass", evidence="Appeared in chat.", source="chat.md")
        upsert_signal(memory, category="chat.intent", label="movement", evidence="Appeared in chat.", source="chat.md")
        upsert_signal(memory, category="chat.intent", label="glitchy", evidence="Appeared in chat.", source="chat.md")
        upsert_signal(memory, category="chat.intent", label="zap", evidence="Appeared in chat.", source="chat.md")
        upsert_signal(memory, category="chat.intent", label="cut out", evidence="Appeared in chat.", source="chat.md")
        upsert_signal(memory, category="chat.intent", label="riser", evidence="Appeared in chat.", source="chat.md")
        upsert_signal(memory, category="chat.intent", label="swell", evidence="Appeared in chat.", source="chat.md")
        upsert_signal(memory, category="chat.workflow", label="glitch-drum-transition", evidence="Workflow in chat.", source="chat.md")

        mappings = derive_intent_mappings(memory)
        ids = {mapping["id"] for mapping in mappings}

        self.assertIn("kick-sub-sidechain", ids)
        self.assertIn("arrangement-flow", ids)
        self.assertIn("bass-movement", ids)
        self.assertIn("glitch-drum-transition", ids)
        self.assertIn("riser-transition", ids)
        sidechain = next(mapping for mapping in mappings if mapping["id"] == "kick-sub-sidechain")
        drums = next(mapping for mapping in mappings if mapping["id"] == "drum-kit-building")
        bass = next(mapping for mapping in mappings if mapping["id"] == "bass-movement")
        riser = next(mapping for mapping in mappings if mapping["id"] == "riser-transition")
        self.assertIn("workflow-macro render kick-sub-separation", sidechain["recommended_commands"])
        self.assertIn("workflow-macro render drum-punch-bus", drums["recommended_commands"])
        self.assertIn("workflow-macro render call-response-bass", bass["recommended_commands"])
        self.assertEqual(riser["recommended_commands"], ["workflow-macro render riser-transition"])
        self.assertIn("sidechain", sidechain["query_terms"])
        self.assertGreaterEqual(sidechain["confidence"], 0.2)

    def test_sync_intent_mappings_persists_active_mappings(self):
        memory = default_memory()
        upsert_signal(memory, category="project.device", label="Reverb", evidence="Used in set.", source="set.als")
        upsert_signal(memory, category="project.device", label="Delay", evidence="Used in set.", source="set.als")

        updates = sync_intent_mappings(memory)

        self.assertTrue(any(update["id"] == "space-delay-rides" and update["changed"] for update in updates))
        self.assertTrue(any(mapping["id"] == "space-delay-rides" for mapping in memory["intent_mappings"]))

    def test_render_profile_includes_mappings_and_evidence_gaps(self):
        memory = default_memory()
        upsert_signal(memory, category="project.device", label="Reverb", evidence="Used in set.", source="set.als")
        upsert_signal(memory, category="project.device", label="Delay", evidence="Used in set.", source="set.als")
        upsert_signal(memory, category="project.name", label="BD", evidence="Named track in set.", source="set.als")
        upsert_signal(memory, category="project.name", label="SC Trigger", evidence="Named track in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement", label="Drop", evidence="Locator in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-label-proposal", label="beat 64: 02 Main Drop - Drum FX Kick Impact", evidence="Derived section.", source="derived")
        upsert_signal(memory, category="project.arrangement-marker", label="locator-marker-2-at-64-beats", evidence="Locator in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-phase", label="main-section-phase-bass-drums", evidence="Clip roles in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-role", label="clip-role-bass", evidence="Clip name in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-shape", label="common-clip-length-16-beats", evidence="Clip timing in set.", source="set.als")
        upsert_signal(memory, category="project.device-chain", label="Midi track: Operator > AutoFilter > Saturator", evidence="Chain in set.", source="set.als")
        upsert_signal(memory, category="project.routing", label="A-Reverb", evidence="Routing in set.", source="set.als")
        upsert_signal(memory, category="project.automation", label="AutomationEnvelope", evidence="Automation in set.", source="set.als")
        upsert_signal(memory, category="project.workflow", label="bass-movement-project-workflow", evidence="Workflow in set.", source="set.als")
        upsert_signal(memory, category="chat.workflow", label="bass-movement-workflow", evidence="Workflow in chat.", source="chat.md")
        upsert_signal(memory, category="chat.refinement", label="correction-instead-of", evidence="Correction in chat.", source="chat.md")
        sync_intent_mappings(memory)

        profile = render_profile(memory, {"run_id": "run-1"})

        self.assertIn("Derived Intent Mappings", profile)
        self.assertIn("space-delay-rides", profile)
        self.assertIn("Recognition terms", profile)
        self.assertIn("Personal Target Aliases", profile)
        self.assertIn("sidechain", profile)
        self.assertIn("SC Trigger", profile)
        self.assertIn("Project Workflow Evidence", profile)
        self.assertIn("Personalized Workflow Playbooks", profile)
        self.assertIn("Bass movement and resampling", profile)
        self.assertIn("Verify movement automation", profile)
        self.assertIn("chat.workflow", profile)
        self.assertIn("project.arrangement", profile)
        self.assertIn("project.arrangement-label-proposal", profile)
        self.assertIn("project.arrangement-marker", profile)
        self.assertIn("project.arrangement-phase", profile)
        self.assertIn("project.arrangement-role", profile)
        self.assertIn("project.arrangement-shape", profile)
        self.assertIn("project.device-chain", profile)
        self.assertIn("project.workflow", profile)
        self.assertIn("Operator > AutoFilter > Saturator", profile)
        self.assertIn("A-Reverb", profile)
        self.assertIn("set-send", profile)
        self.assertIn("workflow-macro render personalized-space-chain", profile)
        self.assertNotIn("No chat evidence has been scanned yet", profile)
        self.assertIn("Derived Section Label Proposals", profile)
        self.assertIn("Iterative Refinement Patterns", profile)
        self.assertIn("correction-instead-of", profile)

    def test_render_profile_does_not_report_missing_arrangement_when_locator_markers_exist(self):
        memory = default_memory()
        upsert_signal(memory, category="project.name", label="BD", evidence="Appeared in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-marker", label="locator-marker-2-at-64-beats", evidence="Locator in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-phase", label="main-section-phase-drums-kick", evidence="Clip roles in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-role", label="main-section-role-kick", evidence="Clip name in set.", source="set.als")
        upsert_signal(memory, category="project.arrangement-shape", label="locator-count-8", evidence="Timing in set.", source="set.als")

        profile = render_profile(memory, {"run_id": "run-1"})

        self.assertIn("project.arrangement-marker", profile)
        self.assertIn("Derived Section Label Proposals", profile)
        self.assertIn("02 Main Drop - Drum Kick Impact", profile)
        self.assertNotIn("No project arrangement marker or scene evidence has been learned yet", profile)
        self.assertNotIn("No project locator timing marker evidence has been learned yet", profile)
        self.assertIn("No project musical scene or locator label evidence has been learned yet", profile)


if __name__ == "__main__":
    unittest.main()
