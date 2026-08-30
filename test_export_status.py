from pathlib import Path
import importlib.util

P=Path(__file__).resolve().parent/'export_status.py'
s=importlib.util.spec_from_file_location('dashboard_export',P)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def test_every_stage_has_explicit_percent():
    x=m.stage('x','working','d',12,.375)
    assert x['percent']==37.5

def test_mining_stage_reports_live_day_progress_and_subchecklist():
    progress={'days_complete':31,'days_total':183,'percent':16.94,'checklist':{'authority_and_join':100.0,'discovery_day_mining':16.94}}
    state,fraction,detail,sub=m.mining_stage_state(progress,{},'MT5_TICK_BACKWARD_WINNER_MINING_V1',True)
    assert state=='working' and abs(fraction-.1694)<1e-9
    assert '31/183' in detail and sub['authority_and_join']==100.0

def test_mining_stage_complete_is_100_percent():
    state,fraction,detail,sub=m.mining_stage_state({'percent':100},{'complete':True},'MT5_TICK_BACKWARD_WINNER_MINING_V1',False)
    assert state=='complete' and fraction==1.0 and 'complete' in detail.lower()

def test_load_json_accepts_windows_utf8_bom():
    import tempfile, json
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'x.json'; p.write_text(json.dumps({'phase':'x'}),encoding='utf-8-sig')
        assert m.load_json(p)['phase']=='x'

if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    for fn in tests: fn()
    print(f'PASS {len(tests)} tests')
