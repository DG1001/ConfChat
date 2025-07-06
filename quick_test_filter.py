#!/usr/bin/env python3
from app import clean_markdown_response

test_input = '```markdown\n# Test Title\nContent here\n```'
expected = '# Test Title\nContent here'
result = clean_markdown_response(test_input)
print(f"Input: {repr(test_input)}")
print(f"Output: {repr(result)}")
print(f"Expected: {repr(expected)}")
print(f"Success: {'✓' if result == expected else '✗'}")