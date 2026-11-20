"""Safe job staging for user-supplied, explicitly authorized mouth-sprite rigs."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import atexit
import json
import shutil
import stat
import tempfile
import zipfile

from .proof_render import ProofError, load_rig, sha256

_OWNED_JOBS: set[Path] = set()

def _clean_own_jobs():
    for job in list(_OWNED_JOBS):
        if job.name.startswith('job_') and job.is_dir() and not job.is_symlink():
            shutil.rmtree(job, ignore_errors=True)

atexit.register(_clean_own_jobs)

MAX_SOURCE_BYTES = 40 * 1024 * 1024
MAX_AUDIO_BYTES = 40 * 1024 * 1024
MAX_RIG_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGES = {'.png', '.jpg', '.jpeg', '.webp'}
ALLOWED_MEDIA = ALLOWED_IMAGES | {'.mp4', '.mov', '.webm', '.mkv'}
ALLOWED_AUDIO = {'.wav', '.mp3', '.m4a', '.ogg', '.flac'}
SHAPES = 'ABCDEFGHX'


def check_upload(source: Path, allowed: set[str], limit: int) -> None:
    if not source.is_file() or source.is_symlink():
        raise ProofError('Input file missing or is a symlink')
    if source.suffix.lower() not in allowed:
        raise ProofError('Input file type is not supported')
    if not 1 <= source.stat().st_size <= limit:
        raise ProofError(f'Input must be 1..{limit // (1024*1024)} MiB')


def stage_upload(source: Path, work: Path, stem: str, allowed: set[str], limit: int) -> Path:
    source = Path(source)
    check_upload(source, allowed, limit)
    dest = work / f'{stem}{source.suffix.lower()}'
    if dest.exists():
        raise ProofError('Job staging conflict')
    shutil.copyfile(source, dest)
    if sha256(dest) != sha256(source):
        raise ProofError('Input integrity check failed')
    return dest


def unpack_user_rig(zip_path: Path, source: Path, work: Path, anchor: dict, *, user_approved: bool) -> Path:
    if not user_approved:
        raise ProofError('Explicit confirmation of authorized mouth artwork is required')
    zip_path = Path(zip_path)
    check_upload(zip_path, {'.zip'}, MAX_RIG_BYTES)
    rig_dir = work / 'rig'
    if rig_dir.exists():
        raise ProofError('Rig already staged')
    rig_dir.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as archive:
        files = [v for v in archive.infolist() if not v.is_dir()]
        if not files or len(files) > 24 or sum(v.file_size for v in files) > MAX_RIG_BYTES:
            raise ProofError('Rig archive exceeds file count or size limits')
        for entry in files:
            name = PurePosixPath(entry.filename)
            if (name.is_absolute() or '..' in name.parts or '\\' in entry.filename
                    or len(name.parts) > 2 or not entry.filename.isascii()
                    or (entry.external_attr >> 16) & stat.S_IFMT(0o170000) == stat.S_IFLNK):
                raise ProofError('Rig archive has unsafe file paths')
            if entry.file_size > 3 * 1024 * 1024 or entry.compress_size == 0 and entry.file_size:
                raise ProofError('Rig archive contains an oversized or invalid file')
            if entry.compress_size and entry.file_size / entry.compress_size > 250:
                raise ProofError('Suspiciously compressed rig entry')
            if name.suffix.lower() != '.png' and str(name) != 'rig.json':
                raise ProofError('Rig archive can only contain PNG sprites and optional rig.json')
            dest = (rig_dir / str(name)).resolve()
            if rig_dir.resolve() not in dest.parents:
                raise ProofError('Rig archive path escapes staging directory')
            dest.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as reader, dest.open('xb') as writer:
                shutil.copyfileobj(reader, writer)
    config_path = rig_dir / 'rig.json'
    if config_path.is_file():
        rig = json.loads(config_path.read_text(encoding='utf-8'))
        if rig.get('source_sha256') and rig['source_sha256'] != sha256(source):
            raise ProofError('Rig belongs to a different source image/video')
        shapes = rig.get('shapes', {})
        if not isinstance(shapes, dict):
            raise ProofError('Rig shapes must be an object')
    else:
        shapes = {letter: f'{letter}.png' for letter in SHAPES if (rig_dir / f'{letter}.png').is_file()}
    if 'X' not in shapes or len(shapes) < 2:
        raise ProofError('Rig requires closed X and at least one speaking mouth shape')
    for shape, sprite in shapes.items():
        if shape not in SHAPES or not isinstance(sprite, str) or not sprite.lower().endswith('.png'):
            raise ProofError('Unrecognized or non-PNG mouth sprite')
    if not 0 <= anchor['x'] <= 1 or not 0 <= anchor['y'] <= 1:
        raise ProofError('Mouth anchor is outside source frame')
    if not 0.05 <= anchor['scale'] <= 10:
        raise ProofError('Invalid mouth scale')
    if not -360 <= anchor['rotation_deg'] <= 360:
        raise ProofError('Invalid mouth rotation')
    rig = {'schema_version': 1, 'character_id': 'user-supplied-noncanonical',
           'source_path': source.name, 'source_sha256': sha256(source),
           'authority': 'approved_user_rig', 'approved': True,
           'mouth_anchor': anchor, 'shapes': shapes,
           'notes': 'User-confirmed mouth artwork; not canon approval or identity certification.'}
    config_path.write_text(json.dumps(rig, indent=2), encoding='utf-8')
    load_rig(config_path, source)  # Final sprite and protected-source validation.
    return config_path


def atomic_job_directory(root: Path | None = None) -> Path:
    parent = root or Path(tempfile.gettempdir()) / 'dex_lips_jobs'
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    job = Path(tempfile.mkdtemp(prefix='job_', dir=parent))
    job.chmod(0o700)
    _OWNED_JOBS.add(job)
    return job


def prune_expired(root: Path | None = None, older_than_seconds: int = 3600) -> int:
    """Remove only Dex_Lips-owned job directories after their retention period."""
    import time
    parent = root or Path(tempfile.gettempdir()) / 'dex_lips_jobs'
    if not parent.is_dir() or parent.is_symlink():
        return 0
    count = 0
    for d in parent.iterdir():
        if not d.name.startswith('job_') or d.is_symlink() or not d.is_dir():
            continue
        if time.time() - d.stat().st_mtime > older_than_seconds:
            shutil.rmtree(d)
            _OWNED_JOBS.discard(d)
            count += 1
    return count
