from pathlib import Path

ROOT=Path(__file__).resolve().parent
JS=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')

def test_stage_cards_render_explicit_percent():
    assert 'stage-percent' in JS
    assert 's.percent' in JS

def test_stage_cards_render_subchecklist_percentages():
    assert 'subchecklist' in JS
    assert 'subcheck-row' in JS
    assert 'subcheck-row' in CSS

if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    for fn in tests: fn()
    print(f'PASS {len(tests)} tests')