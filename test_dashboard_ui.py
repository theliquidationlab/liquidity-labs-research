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

def test_dashboard_has_live_broker_certification_panel():
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    for token in ('brokerStage','brokerProgress','brokerConditions','brokerAnchors','brokerRaw95','brokerFinal98','brokerHealth','brokerError'):
        assert f'id="{token}"' in html
    for token in ('broker_stage','broker_progress','broker_conditions','broker_anchor_survivors','broker_raw95_survivors','broker_exact98_finalists'):
        assert token in JS

if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    for fn in tests: fn()
    print(f'PASS {len(tests)} tests')
