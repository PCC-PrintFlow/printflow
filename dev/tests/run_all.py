"""Runs every PrintFlow browser test and reports page errors.

Usage (from anywhere):  python3 dev/tests/run_all.py            # all tests
                        python3 dev/tests/run_all.py test_n test_pwa
Needs: pip install playwright && playwright install chromium
       (or set CHROME=/path/to/chrome to use an installed Chrome).
Each test drives dev/printflow.html with made-up sample data and prints what it sees,
ending with "ERRORS: [...]" (page errors / console errors). test_pwa.py tests the built
app at the repo root (run dev/build.py first) with a fake GitHub API; its three expected
console errors are the fake 401/404 responses it sends on purpose.
Screenshots and files the tests save land in dev/tests/ and are ignored by git.
"""
import os, sys, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
DEV = os.path.dirname(HERE); ROOT = os.path.dirname(DEV)
env = dict(os.environ, PRINTFLOW_HTML=os.path.join(DEV, "printflow.html"), PRINTFLOW_SITE=ROOT)
EXPECTED = {"test_pwa.py": 3}
names = [a if a.endswith(".py") else a + ".py" for a in sys.argv[1:]] or sorted(os.path.basename(p) for p in glob.glob(os.path.join(HERE, "test_*.py")))
failed = []
for n in names:
    # run inside dev/tests: tests share fixtures by relative path; screenshots land here too (git-ignored)
    r = subprocess.run([sys.executable, n], cwd=HERE, env=env, capture_output=True, text=True, timeout=300)
    text = r.stdout + r.stderr
    line = next((l for l in text.splitlines() if l.startswith("ERRORS:")), None)
    ok = r.returncode == 0 and line is not None
    if ok:
        try: count = len(eval(line[len("ERRORS:"):]))
        except Exception: count = 99
        ok = count <= EXPECTED.get(n, 0)
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else "\n" + text[-1500:]))
    if not ok: failed.append(n)
print(f"\n{len(names) - len(failed)}/{len(names)} passed")
sys.exit(1 if failed else 0)
