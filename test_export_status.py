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

def test_frontier_stage_reports_live_pair_progress():
    progress={'days_complete':6,'days_total':183,'percent':3.28,'pair_candidates':572000,
              'checklist':{'authority_and_pair_catalog':100.0,'discovery_pair_shards':3.28}}
    state,fraction,detail,sub=m.frontier_stage_state(progress,{},'MT5_TICK_PRECURSOR_FRONTIER_V1',True)
    assert state=='working' and abs(fraction-.0328)<1e-9
    assert '6/183' in detail and '572,000' in detail
    assert sub['authority_and_pair_catalog']==100.0

def test_precursor_stage_combines_pair_completion_with_live_temporal_progress():
    frontier={'complete':True,'pair_candidates':572000,'stable_enriched_pairs':540687}
    progress={'days_complete':2,'days_total':183,'percent':1.09,'transition_candidates':3492438,
              'checklist':{'authority_and_temporal_catalog':100.0,'discovery_temporal_shards':1.09}}
    state,fraction,detail,sub=m.precursor_stage_state(frontier,progress,{},'MT5_TICK_SEQUENCE_PERSISTENCE_FRONTIER_V1',True)
    assert state=='working' and abs(fraction-.50545)<1e-9
    assert '3,492,438' in detail and sub['concurrent_pair_frontier']==100.0
    assert sub['discovery_temporal_shards']==1.09

def test_broker_stage_reports_live_real_progress_and_survivors():
    progress={'state':'RUNNING','active_stage':'raw_screen','percent':52.5,'days_complete':66,'days_total':183,'conditions_total':733848,'geometry_total':1638,'anchor_total':126,'anchor_B1_survivors':21,'raw95_survivors':7,'exact98_finalists':0}
    state,fraction,detail,sub=m.broker_stage_state(progress,{},'MT5_PRECURSOR_BROKER_SCREEN_V1',True,0)
    assert state=='working' and abs(fraction-.525)<1e-9
    assert 'raw screen' in detail.lower() and '733,848' in detail
    assert sub['conditions']==733848 and sub['raw_95_survivors']==7

def test_broker_stage_complete_reports_exact_finalists():
    final={'complete':True,'raw95_survivors':12,'exact98_finalists':3,'conditions_total':733848,'geometry_total':1638}
    state,fraction,detail,sub=m.broker_stage_state({},final,'',False,0)
    assert state=='complete' and fraction==1.0 and '3' in detail and sub['exact_98_finalists']==3

def test_structure_stage_reports_lossless_live_progress():
    progress={'state':'RUNNING','active_stage':'structure_days','percent':25.5,'days_complete':62,'days_total':183,'ticks':11000000,'success_rows_mapped':12000000,'events_confirmed':8000000,'success_population_target':35975633,'all_successes_preserved':True}
    state,fraction,detail,sub=m.structure_stage_state(progress,{},'MT5_CAUSAL_STRUCTURE_MAP_V1',True,0)
    assert state=='working' and abs(fraction-.255)<1e-9
    assert '62/183' in detail and sub['success_target']==35975633
    assert sub['success_rows_mapped']==12000000 and sub['stderr_bytes']==0

def test_structure_stage_complete_reports_group_counts():
    final={'complete':True,'corrected_discovery_ticks':33488805,'success_source_direction_rows':35975633,'structural_events':123456,'fine_groups':100,'topology_groups':70,'macro_groups':40}
    state,fraction,detail,sub=m.structure_stage_state({},final,'',False,0)
    assert state=='complete' and fraction==1.0
    assert sub['success_rows_mapped']==35975633 and sub['fine_groups']==100

if __name__=='__main__':
    tests=[v for k,v in list(globals().items()) if k.startswith('test_')]
    for fn in tests: fn()
    print(f'PASS {len(tests)} tests')
