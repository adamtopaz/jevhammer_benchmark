"""Publish only complete, independently replayed graph-screen evidence.

Requests are processed mechanically. No goal text, proof text, declaration
names from selector choices, or individual failed goals are inspected.
"""
import copy
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'runs/cpu-selector-graph-preview-v1'
DEPLOYMENT = ROOT / 'runs/cpu-selector-graph-preview-v1-deployment'
PREFIX = 'JevHammerBenchmark.GraphPreviewStudy.'
METHODS = [PREFIX + x for x in ('cpuControl', 'original', 'preview', 'neuralNative', 'neuralReranked')]

def read(path):
    return json.loads(path.read_text())

def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def graph_decisions(decisions):
    result = {'requests': 0, 'validResponses': 0, 'fallbackResponses': 0,
              'frontierNodes': 0, 'directions': Counter(), 'cappedForwardNodes': 0,
              'truncatedTypes': 0, 'emptySelectedNeighborhoods': 0,
              'nonemptyExpansions': 0, 'requestsWithExpansion': 0,
              'requestsWithNonemptyExpansion': 0}
    for row in decisions:
        if row['request']['state']['task'] != 'selector':
            continue
        result['requests'] += 1
        questions = row['request']['questions']
        choices = [questions[str(i)]['instructions']['candidate'] for i in range(len(questions))]
        assert choices and len(choices) % 3 == 0
        assert all(c['direction'] == ('none', 'backward', 'forward')[i % 3]
                   for i, c in enumerate(choices))
        answers = row['response'].get('answers', {})
        try:
            scores = [answers[str(i)]['noul'] for i in range(len(choices))]
            assert all(isinstance(s, (int, float)) and math.isfinite(s) for s in scores)
            order = sorted(range(len(choices)), key=lambda i: (-scores[i], i))
        except (KeyError, TypeError, AssertionError):
            result['fallbackResponses'] += 1
            order = list(range(len(choices)))
        else:
            result['validResponses'] += 1
        chosen = {}
        for i in order:
            chosen.setdefault(i // 3, choices[i])
        expanded = nonempty = False
        for choice in chosen.values():
            direction = choice['direction']
            result['frontierNodes'] += 1
            result['directions'][direction] += 1
            result['cappedForwardNodes'] += choice['forward_count_capped']
            result['truncatedTypes'] += choice['type_truncated']
            if direction != 'none':
                expanded = True
                if choice[direction + '_count']:
                    nonempty = True
                    result['nonemptyExpansions'] += 1
                else:
                    result['emptySelectedNeighborhoods'] += 1
        result['requestsWithExpansion'] += expanded
        result['requestsWithNonemptyExpansion'] += nonempty
    return result

def main():
    manifest = read(RUN / 'run.json')
    assert manifest['status'] == 'complete', 'Run must finish before export.'
    summary, verification = (read(RUN / p) for p in ('summary.json', 'verification.json'))
    assert summary['status'] == verification['status'] == 'complete'
    assert manifest['methods'] == METHODS and manifest['guidance'] == 'jev'
    trials, decisions, warmups = (rows(RUN / p) for p in ('trials.jsonl', 'decisions.jsonl', 'warmup.jsonl'))
    dataset = read(RUN / 'dataset.json')
    expected = {(r['site'], m) for r in dataset['sites'] for m in METHODS}
    assert len(dataset['sites']) == 34 and len(expected) == len(trials) == 170
    assert {(r['site'], r['method']) for r in trials} == expected
    checks = rows(RUN / verification['directory'] / 'replay.jsonl')
    assert all(r['verified'] for r in checks)
    verified = {(r['site'], r['method']) for r in checks}
    assert len(verified) == len(checks)
    assert verified == {(r['site'], r['method']) for r in trials if r['solved']}
    public = []
    metrics = {}
    configs = []
    for method in METHODS:
        group = [r for r in trials if r['method'] == method]
        ds = [r for r in decisions if r['method'] == method]
        config = group[0]['config']
        assert all(r['config'] == config for r in group)
        assert config['guidePremises'] == (method == PREFIX + 'neuralReranked')
        configs.append({k: v for k, v in config.items() if k != 'guidePremises'})
        counters = {key: sum(r['stats'][key] for r in group) for key in
                    ('retrievalMs', 'selectorRankCalls', 'premiseRankCalls', 'stateRankCalls',
                     'rankCalls', 'rankFailures', 'refreshes', 'nodes', 'trials')}
        assert counters['rankCalls'] == counters['premiseRankCalls'] + counters['stateRankCalls']
        assert counters['stateRankCalls'] > 0
        assert (counters['selectorRankCalls'] > 0) == (method in {PREFIX + 'original', PREFIX + 'preview'})
        assert all(r['stats']['rankCalls'] <= config['maxCalls'] for r in group)
        task_counts = Counter(d['request']['state']['task'] for d in ds)
        assert task_counts['selector'] == counters['selectorRankCalls']
        assert task_counts['continuations'] == counters['stateRankCalls']
        metrics[method] = {'config': config, **counters,
            'goalMedianMs': statistics.median(r['elapsedMs'] for r in group),
            'requestElapsedMs': sum(r['elapsedMs'] for r in ds),
            'selectorRequestElapsedMs': sum(r['elapsedMs'] for r in ds if r['request']['state']['task'] == 'selector'),
            'requestTaskCounts': task_counts, 'requests': len(ds),
            'warmupMs': [r['elapsedMs'] for r in warmups if r['name'] == method],
            'reportedInputTokens': sum((r.get('usage') or {}).get('input_tokens', 0) for r in ds),
            'reportedOutputTokens': sum((r.get('usage') or {}).get('output_tokens', 0) for r in ds),
            'errors': dict(Counter(r['response']['error'] for r in ds if 'error' in r.get('response', {})))}
        for r in group:
            row = {k: r[k] for k in ('site', 'module', 'declaration', 'method', 'elapsedMs', 'stats', 'budgetBlocked')}
            row.update(rawSolved=r['solved'], independentlyReplayed=(r['site'], method) in verified,
                       onTimeVerified=r['onTime'] and (r['site'], method) in verified)
            public.append(row)
    assert all(c == configs[0] for c in configs)
    assert len(decisions) == summary['usage']['attempts']
    resources = copy.deepcopy(manifest['resources'])
    for snapshot in resources.values():
        snapshot.pop('cgroup', None)
        assert snapshot['memoryMax'] <= 16000000000 and snapshot['swapMax'] == '0'
    coverage = {m: summary['methods'][m]['onTimeVerified'] for m in METHODS}
    promote = coverage[PREFIX + 'preview'] > max(coverage[m] for m in METHODS if m != PREFIX + 'preview')
    publicpath = ROOT / 'docs/cpu-selector-graph-preview-v1-trials.jsonl'
    evidence = ['run.json', 'summary.json', 'trials.jsonl', 'decisions.jsonl', 'warmup.jsonl',
                'verification.json', verification['directory'] + '/replay.jsonl']
    report = {'schema': 1, 'kind': 'live-development-candidate-screen',
        **read(DEPLOYMENT / 'research.json'),
        'dataset': 'datasets/sparse-jev-v1/research-graph-preview-v1.json',
        'datasetSha256': manifest['datasetSha256'], 'summary': summary,
        'resources': resources, 'metrics': metrics, 'graphDecisions': {m: graph_decisions([d for d in decisions if d['method'] == m]) for m in (PREFIX + 'original', PREFIX + 'preview')},
        'successfulTrialsIndependentlyReplayed': len(verified), 'reservedEvaluationTrials': 0,
        'promotionRule': 'Preview must exceed CPU control, original graph, and both neural arms on on-time verified pilot coverage.',
        'promoteToDevelopment134': promote,
        'limitations': [
            '34 repeatedly exposed development locations; pilot screening cannot establish final superiority.',
            'Every arm uses Jev proof-state guidance; selectors are compared inside JevHammer, not full LeanHammer.',
            'Graph selector requests share the existing three-call and six-second search allowance.',
            'Preview CPU p95 exceeds the provisional 200 ms target; optional Jev latency remains included in trial retrieval. Signature graph fits no proof statistics. The CPU base excludes all 188 cohort owners before fitting.',
            'Fixed synthetic structural warmup and imported/current-file neural embeddings are outside goal timing.',
            'Per-arm initialization cost attribution depends on shared immutable caches and method order.',
            'Model/API failures remain included; third-party neural training overlap is unknown.'
        ],
        'evidenceSha256': {p: sha(RUN / p) for p in evidence},
        'neuralProvenance': read(DEPLOYMENT / 'provenance.json')}
    # Write only after all completeness, matching and replay assertions pass.
    publicpath.write_text(''.join(json.dumps(r, sort_keys=True) + '\n' for r in public))
    report['publicTrials'] = {'path': publicpath.name, 'sha256': sha(publicpath)}
    (ROOT / 'docs/cpu-selector-graph-preview-v1.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'summary': summary, 'graphDecisions': report['graphDecisions'],
                      'metrics': metrics, 'resources': resources, 'promote': promote}, indent=2))

if __name__ == '__main__':
    main()
