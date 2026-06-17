import json
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_APP = REPO_ROOT / "dashboard" / "app"
TSC = DASHBOARD_APP / "node_modules" / ".bin" / "tsc"


def run_foundation_script(tmp_path: Path, script: str):
    out_dir = tmp_path / "compiled"
    source_files = sorted((DASHBOARD_APP / "src" / "core" / "foundation").glob("*.ts"))
    subprocess.run(
        [
            str(TSC),
            "--target",
            "ES2022",
            "--module",
            "CommonJS",
            "--moduleResolution",
            "Node",
            "--rootDir",
            str(DASHBOARD_APP / "src"),
            "--outDir",
            str(out_dir),
            "--strict",
            "--skipLibCheck",
            *[str(path) for path in source_files],
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=out_dir,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_stable_stringify_and_hashing(tmp_path):
    result = run_foundation_script(
        tmp_path,
        textwrap.dedent(
            """
            const assert = require('node:assert/strict');
            const {
              stableStringify,
              stableHash,
              stableNonCryptoHash,
            } = require('./core/foundation');

            // 1. Object key ordering
            const obj1 = { b: 2, a: 1, c: { y: 2, x: 1 } };
            const obj2 = { a: 1, b: 2, c: { x: 1, y: 2 } };
            assert.equal(stableStringify(obj1), stableStringify(obj2));
            assert.equal(stableStringify(obj1), '{"a":1,"b":2,"c":{"x":1,"y":2}}');

            // 2. Array order preservation
            assert.equal(stableStringify([1, 2, 3]), '[1,2,3]');
            assert.notEqual(stableStringify([1, 2, 3]), stableStringify([3, 2, 1]));

            // 3. Undefined fields dropped in objects
            assert.equal(stableStringify({ a: 1, b: undefined }), '{"a":1}');
            assert.equal(stableStringify({ a: 1, b: () => {} }), '{"a":1}');
            assert.equal(stableStringify({ a: 1, b: Symbol('test') }), '{"a":1}');

            // 4. Undefined / Function / Symbol in arrays
            assert.equal(stableStringify([1, undefined, 2]), '[1,"[UNDEFINED]",2]');
            assert.equal(stableStringify([undefined]), '["[UNDEFINED]"]');
            assert.notEqual(stableStringify([undefined]), stableStringify([]));
            assert.equal(stableStringify([() => {}]), '["[NON_SERIALIZABLE_FUNCTION]"]');
            assert.equal(stableStringify([Symbol('test')]), '["[NON_SERIALIZABLE_SYMBOL]"]');

            // 5. NaN / Infinity
            assert.equal(stableStringify(NaN), '"[NON_FINITE_NUMBER_NAN]"');
            assert.equal(stableStringify(Infinity), '"[NON_FINITE_NUMBER_INFINITY]"');
            assert.equal(stableStringify(-Infinity), '"[NON_FINITE_NUMBER_NEGATIVE_INFINITY]"');

            // 6. maxDepth
            const deep = { a: { b: { c: { d: { e: { f: { g: { h: { i: 1 } } } } } } } } };
            assert.match(stableStringify(deep, { maxDepth: 4 }), /MAX_DEPTH_EXCEEDED/);
            assert.doesNotMatch(stableStringify(deep, { maxDepth: 10 }), /MAX_DEPTH_EXCEEDED/);

            // 7. maxStringLength
            const longStr = 'a'.repeat(20);
            const truncated = stableStringify(longStr, { maxStringLength: 10 });
            assert.match(truncated, /TRUNCATED_STRING_HASH_/);
            assert.match(truncated, /_LENGTH_20/);

            // 8. Different oversized strings
            const longStr2 = 'b'.repeat(20);
            assert.notEqual(stableStringify(longStr, { maxStringLength: 10 }), stableStringify(longStr2, { maxStringLength: 10 }));

            // 9. stableHash stability and differentiation
            assert.equal(stableHash(obj1), stableHash(obj2));
            assert.notEqual(stableHash(obj1), stableHash({ ...obj1, a: 2 }));
            assert.notEqual(stableHash([undefined]), stableHash([]));

            // 10. Synchronous check
            const start = Date.now();
            const h = stableHash({ large: 'a'.repeat(10000) });
            assert.equal(typeof h, 'string');
            assert.ok(!h.then); // Not a promise

            console.log(JSON.stringify({ success: true }));
            """
        ),
    )
    assert result["success"] is True
