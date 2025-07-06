#!/usr/bin/env python3
"""
Test script for markdown code block filtering
"""

import sys
from app import clean_markdown_response, markdown_to_html

def test_markdown_filter():
    print("Testing markdown code block filter...")
    
    # Test cases für verschiedene Markdown-Code-Block-Varianten
    test_cases = [
        # Case 1: Standard ```markdown ... ```
        {
            'input': '```markdown\n# Titel\n\nDas ist ein Test.\n```',
            'expected': '# Titel\n\nDas ist ein Test.',
            'description': 'Standard markdown code block'
        },
        
        # Case 2: Nur ``` ohne "markdown"
        {
            'input': '```\n# Titel\n\nDas ist ein Test.\n```',
            'expected': '# Titel\n\nDas ist ein Test.',
            'description': 'Generic code block'
        },
        
        # Case 3: Case-insensitive MARKDOWN
        {
            'input': '```MARKDOWN\n# Titel\n\nDas ist ein Test.\n```',
            'expected': '# Titel\n\nDas ist ein Test.',
            'description': 'Uppercase MARKDOWN'
        },
        
        # Case 4: Gemischte Groß-/Kleinschreibung
        {
            'input': '```Markdown\n# Titel\n\nDas ist ein Test.\n```',
            'expected': '# Titel\n\nDas ist ein Test.',
            'description': 'Mixed case Markdown'
        },
        
        # Case 5: Nur am Anfang
        {
            'input': '```markdown\n# Titel\n\nDas ist ein Test.',
            'expected': '# Titel\n\nDas ist ein Test.',
            'description': 'Only start marker'
        },
        
        # Case 6: Nur am Ende
        {
            'input': '# Titel\n\nDas ist ein Test.\n```',
            'expected': '# Titel\n\nDas ist ein Test.',
            'description': 'Only end marker'
        },
        
        # Case 7: Kein Code-Block
        {
            'input': '# Titel\n\nDas ist ein Test.',
            'expected': '# Titel\n\nDas ist ein Test.',
            'description': 'No code block'
        },
        
        # Case 8: Mehrere Code-Blöcke (sollte nur äußere entfernen)
        {
            'input': '```markdown\n# Titel\n\n```python\nprint("hello")\n```\n\nDas ist ein Test.\n```',
            'expected': '# Titel\n\n```python\nprint("hello")\n```\n\nDas ist ein Test.',
            'description': 'Nested code blocks'
        },
        
        # Case 9: Leer oder None
        {
            'input': '',
            'expected': '',
            'description': 'Empty string'
        },
        
        {
            'input': None,
            'expected': None,
            'description': 'None value'
        },
        
        # Case 10: Nur Whitespace
        {
            'input': '   ```markdown   \n\n   # Titel   \n\n   ```   ',
            'expected': '# Titel',
            'description': 'With whitespace'
        }
    ]
    
    print(f"\nTesting {len(test_cases)} cases:")
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        result = clean_markdown_response(case['input'])
        
        if result == case['expected']:
            print(f"✓ Test {i:2d}: {case['description']}")
            passed += 1
        else:
            print(f"✗ Test {i:2d}: {case['description']}")
            print(f"    Input:    {repr(case['input'])}")
            print(f"    Expected: {repr(case['expected'])}")
            print(f"    Got:      {repr(result)}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    # Test HTML-Konvertierung
    print(f"\nTesting HTML conversion with code blocks:")
    
    html_test_cases = [
        '```markdown\n# Test Titel\n\nDas ist **fett** und *kursiv*.\n```',
        '```\n## Überschrift\n\n- Liste Item 1\n- Liste Item 2\n```',
        '# Normaler Titel\n\nOhne Code-Block-Markierungen.'
    ]
    
    for i, test_input in enumerate(html_test_cases, 1):
        html_result = markdown_to_html(test_input)
        print(f"Test {i}:")
        print(f"  Input:  {repr(test_input[:50])}...")
        print(f"  HTML:   {str(html_result)[:100]}...")
        
        # Prüfe, ob Code-Block-Markierungen in HTML enthalten sind
        if '```' in str(html_result):
            print(f"  ✗ Warning: Code block markers still present in HTML")
            failed += 1
        else:
            print(f"  ✓ Code block markers successfully removed")
            passed += 1
    
    print(f"\nFinal Results: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = test_markdown_filter()
    sys.exit(0 if success else 1)