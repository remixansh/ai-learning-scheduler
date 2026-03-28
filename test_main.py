import json
import unittest

import main


class _Chunk:
    def __init__(self, text):
        self.text = text


class _ModelWithChunks:
    def __init__(self, chunks):
        self._chunks = chunks

    def generate_content(self, prompt, stream=True):
        return [_Chunk(text) for text in self._chunks]


class _ModelFactory:
    def __init__(self, chunks):
        self._chunks = chunks

    def __call__(self, *_args, **_kwargs):
        return _ModelWithChunks(self._chunks)


class StreamJsonObjectsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.original_model = main.genai.GenerativeModel

    async def asyncTearDown(self):
        main.genai.GenerativeModel = self.original_model

    async def test_stream_json_objects_emits_valid_json_lines(self):
        main.genai.GenerativeModel = _ModelFactory(
            ['{"day":1}\n{"day":2}\n']
        )
        request = main.ScheduleRequest(
            topic="Python",
            total_duration="2 days",
            daily_commitment="1 hour",
        )

        lines = [line async for line in main.stream_json_objects(request)]

        self.assertEqual(lines, ['{"day":1}\n', '{"day":2}\n'])

    async def test_stream_json_objects_yields_error_for_invalid_json_buffer(self):
        main.genai.GenerativeModel = _ModelFactory(
            ['{"day":1}\n', '{"day":2']
        )
        request = main.ScheduleRequest(
            topic="Python",
            total_duration="2 days",
            daily_commitment="1 hour",
        )

        lines = [line async for line in main.stream_json_objects(request)]

        self.assertEqual(lines[0], '{"day":1}\n')
        error_payload = json.loads(lines[1])
        self.assertIn("error", error_payload)


if __name__ == "__main__":
    unittest.main()
