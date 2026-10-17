# AI Code Sandbox

The runner executes pasted Python only inside the `ai-analysis-audit-sandbox:latest` Docker image. Runtime has `--network none`, a read-only container root, CPU/memory/process limits, dropped Linux capabilities, and only the raw-data directory mounted read-only. The attempt workspace is writable so model code can produce files; it is isolated from the project source and host credentials.

Build the image from the repository root after Docker Desktop is installed and running:

```powershell
docker build --tag ai-analysis-audit-sandbox:latest -f sandbox/Dockerfile .
```

The image build downloads the exact dependencies in `requirements.txt`. The later model-code run itself has no network. If Docker is unavailable or the image is absent, `src/run_ai_code.py` refuses to run the code.

After a response has been pasted and validated:

```powershell
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\run_ai_code.py --case 01_bank_marketing
```

If the first attempt crashes, inspect its `stderr.txt`. A single minimal repair can be supplied as a separate Python source file; the runner records a unified diff and makes at most one second attempt:

```powershell
C:\dev\venvs\ai-analysis-audit\Scripts\python.exe src\run_ai_code.py --case 01_bank_marketing --repair-source path\to\one-repair.py
```

Run artifacts are written under `reports/ai_code_runs/<case>/<run-id>/`; the exact original response and code are retained there. A code exception or timeout is recorded in `summary.json` as an execution finding. The runner does not alter `PASTE_HERE.md`.