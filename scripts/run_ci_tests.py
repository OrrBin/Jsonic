"""Supply reproducible local/CI artifact inputs to the existing test harness."""
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

root = Path(__file__).resolve().parents[1]
folder = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / 'dist'
wheel, = folder.glob('*.whl')
with tempfile.TemporaryDirectory() as temporary:
    legacy = Path(temporary)
    archive = legacy / 'source.tar'
    subprocess.run(['git', 'archive', '--format=tar', '--output', str(archive),
                    '6138b60a992d14cf18ad9f35c2b58ad2ee20b244', 'jsonic'], check=True, cwd=str(root))
    with tarfile.open(str(archive)) as source:
        source.extractall(str(legacy))  # Pinned, trusted repository source.
    subprocess.run([sys.executable, '-m', 'pytest', '-q', '-o', 'addopts=',
                    '--wheel-path=' + str(wheel), '--legacy-jsonic-root=' + str(legacy),
                    '--cov=jsonic', '--cov-branch', '--cov-report=json',
                    '--junitxml=junit.xml'], check=True, cwd=str(root))
