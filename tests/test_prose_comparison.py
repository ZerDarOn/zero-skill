"""Protect experimental inputs from rubric leakage and invalid-run acceptance."""
from pathlib import Path
import runpy
import unittest

RUNNER = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                           'evaluations/comparisons/prose-three-arm-01/run_comparison.py'))


class ProseComparisonTests(unittest.TestCase):
    def test_prompt_keeps_complete_input_and_excludes_rubric(self):
        case = {'prompt': '请求\n\n---\n原始材料\n', 'hard_criteria': ['SECRET_RUBRIC']}
        for files in [None, {'SKILL.md': '技能正文', 'references/example.md': '引用示例'}]:
            prompt = RUNNER['build_prompt']('共同约定', case, files)
            self.assertTrue(prompt.endswith(case['prompt']))
            self.assertNotIn('SECRET_RUBRIC', prompt)
            if files:
                for body in files.values():
                    self.assertIn(body, prompt)

    def test_invalid_attempts_are_not_accepted_as_behavior_passes(self):
        good = {'exit_code': 0, 'raw_output': '回答', 'turn_completed': True,
                'tool_items': [], 'error': None}
        self.assertTrue(RUNNER['valid_record'](good))
        for patch in [{'exit_code': 1}, {'raw_output': ' '}, {'turn_completed': False},
                      {'tool_items': [{'type': 'command_execution'}]}, {'error': 'timeout'}]:
            self.assertFalse(RUNNER['valid_record']({**good, **patch}))


if __name__ == '__main__':
    unittest.main()
