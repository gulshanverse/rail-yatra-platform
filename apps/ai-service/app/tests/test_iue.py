import unittest
import asyncio

from app.orchestrator.normalizer import input_normalizer
from app.orchestrator.slot_extractor import slot_extractor
from app.orchestrator.evaluator import confidence_evaluator
from app.orchestrator.classifier import intent_classifier
from app.orchestrator.types import IntentCandidate, Slot


class TestIntentUnderstandingEngine(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_input_normalizer_sanitization(self):
        # Test basic cleaning and whitespace normalization
        raw_text = "  Hello \n \t World!  "
        normalized = input_normalizer.normalize(raw_text)
        self.assertEqual(normalized, "Hello World!")

        # Test non-printable character stripping and space collapsing
        raw_non_printable = "Hello \x00 World"
        normalized = input_normalizer.normalize(raw_non_printable)
        self.assertEqual(normalized, "Hello World")

    def test_input_normalizer_pii_redaction(self):
        # Test phone number redaction
        text_with_phone = "My phone number is 9876543210 and (+91) 8765432109"
        redacted = input_normalizer.redact_pii(text_with_phone)
        self.assertIn("[REDACTED_PHONE]", redacted)
        self.assertNotIn("9876543210", redacted)

        # Test email redaction
        text_with_email = "Email me at test.user@railyatra.com or contact@yatra.in"
        redacted = input_normalizer.redact_pii(text_with_email)
        self.assertIn("[REDACTED_EMAIL]", redacted)
        self.assertNotIn("test.user@railyatra.com", redacted)

        # Test PNR redaction
        text_with_pnr = "My PNR is 4321098765"
        redacted = input_normalizer.redact_pii(text_with_pnr)
        self.assertIn("[REDACTED_PNR]", redacted)
        self.assertNotIn("4321098765", redacted)

        # Test credit card redaction
        text_with_cc = "Pay using card 1234-5678-9012-3456"
        redacted = input_normalizer.redact_pii(text_with_cc)
        self.assertIn("[REDACTED_CC]", redacted)

    def test_slot_extractor(self):
        # Test station code extraction
        query = "Book travel from NDLS to HWH on 2026-10-15"
        slots = slot_extractor.extract_slots(query)
        
        self.assertIn("origin", slots)
        self.assertEqual(slots["origin"].value, "NDLS")
        self.assertIn("destination", slots)
        self.assertEqual(slots["destination"].value, "HWH")
        self.assertIn("date", slots)
        self.assertEqual(slots["date"].value, "2026-10-15")

        # Test relative date parsing
        query_today = "Show schedules for today"
        slots_today = slot_extractor.extract_slots(query_today)
        self.assertIn("date", slots_today)
        self.assertEqual(slots_today["date"].value, "today")

        # Test train number and passenger counts
        query_train = "Schedules for train 12002 for 3 passengers"
        slots_train = slot_extractor.extract_slots(query_train)
        self.assertIn("train_number", slots_train)
        self.assertEqual(slots_train["train_number"].value, "12002")
        self.assertIn("passenger_count", slots_train)
        self.assertEqual(slots_train["passenger_count"].value, 3)

    def test_confidence_evaluator(self):
        # 1. Successful evaluation (high confidence, slots complete)
        candidate = IntentCandidate(name="plan_travel", confidence=0.95, reason="Matches model classification")
        slots = {
            "origin": Slot(name="origin", value="NDLS", type="StationCode", confidence=1.0),
            "destination": Slot(name="destination", value="SBC", type="StationCode", confidence=1.0),
        }
        descriptor = confidence_evaluator.evaluate(candidate, slots, {}, {})
        self.assertFalse(descriptor.needs_clarification)
        
        # 2. Low confidence intent triggers clarification
        candidate_low = IntentCandidate(name="plan_travel", confidence=0.55, reason="Unsure classification")
        descriptor_low = confidence_evaluator.evaluate(candidate_low, slots, {}, {})
        self.assertTrue(descriptor_low.needs_clarification)

        # 3. Missing slots triggers clarification
        slots_missing = {
            "origin": Slot(name="origin", value="NDLS", type="StationCode", confidence=1.0)
        }
        descriptor_missing = confidence_evaluator.evaluate(candidate, slots_missing, {}, {})
        self.assertTrue(descriptor_missing.needs_clarification)

    def test_classifier_pipeline_end_to_end(self):
        async def run_test():
            # Test fast-path heuristic routing bypasses LLM
            query = "My PNR status is 4321098765"
            descriptor = await intent_classifier.classify_and_parse(query)
            
            self.assertEqual(descriptor.intent.name, "check_pnr")
            self.assertEqual(descriptor.metadata["classifier_type"], "heuristic")
            self.assertIn("pnr", descriptor.slots)
            self.assertEqual(descriptor.slots["pnr"].value, "4321098765")
            self.assertFalse(descriptor.needs_clarification)

            # Test general query falling back
            query_general = "hello there"
            descriptor_general = await intent_classifier.classify_and_parse(query_general)
            self.assertEqual(descriptor_general.intent.name, "conversation")

        self.loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main()
