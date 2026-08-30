from pathlib import Path

ROOT=Path(__file__).resolve().parent
JS=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')
EXPORT=(ROOT/'export_status.py').read_text(encoding='utf-8')

def test_stage_cards_render_explicit_percent():
    assert 'stage-percent' in JS and 's.percent' in JS

def test_stage_cards_render_subchecklist_percentages():
    assert 'subchecklist' in JS and 'subcheck-row' in JS and 'subcheck-row' in CSS

def test_dashboard_has_live_structure_mapping_panel():
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    for token in ('structureStage','structureProgress','structureDays','structureTicks','structureEvents','structureSuccess','structureCoverage','structureHealth','structureError'):
        assert f'id="{token}"' in html
    for token in ('structure_stage','structure_progress','structure_days','structure_ticks','structure_events','structure_success_rows','structure_coverage'):
        assert token in JS

def test_full_structure_mapping_precedes_broker_and_microstructure():
    assert EXPORT.index('MT5 full causal structure mapping') < EXPORT.index('MT5 structural family broker replay')
    assert EXPORT.index('MT5 structural family broker replay') < EXPORT.index('Microstructure entry timing')
    assert EXPORT.index('Microstructure entry timing') < EXPORT.index('Binance strength cross-reference')

def test_dashboard_has_live_structural_broker_panel():
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    for token in ('structBrokerStage','structBrokerProgress','structBrokerCandidates','structBrokerGeometries','structBrokerRaw95','structBrokerExact95','structBrokerPre98','structBrokerHealth','structBrokerError'):
        assert f'id="{token}"' in html
    for token in ('raw_dollar95_candidates','primary_geometries','raw_broker95_combos','exact95_structural_valid','exact98_pretiming'):
        assert token in JS

if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    for fn in tests: fn()
    print(f'PASS {len(tests)} tests')
