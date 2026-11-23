"""Offline restored-directory comparison. No cloud calls and no restore operation."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(directory):
    base = Path(directory)
    if base.is_symlink() or not base.is_dir():
        raise ValueError('Input must be an existing non-symlink directory')
    result = {}
    # Reject links and special files rather than silently skipping them.
    for path in sorted(base.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlinks are unsupported')
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError('Special files are unsupported')
        result[path.relative_to(base).as_posix()] = {
            'sha256': digest(path), 'size': path.stat().st_size}
    return result


def validate_manifest(data):
    if not isinstance(data, dict) or data.get('schema') != 1:
        raise ValueError('Unsupported manifest schema')
    files = data.get('files')
    if not isinstance(files, dict):
        raise ValueError('Manifest files must be an object')
    for name, meta in files.items():
        p = PurePosixPath(name)
        if (not name or name == '.' or p.is_absolute() or '..' in p.parts
                or '\\' in name or p.as_posix() != name):
            raise ValueError('Unsafe or noncanonical manifest path')
        if not isinstance(meta, dict):
            raise ValueError('Invalid manifest entry')
        sha = meta.get('sha256')
        size = meta.get('size')
        if (not isinstance(sha, str) or len(sha) != 64
                or any(c not in '0123456789abcdef' for c in sha)
                or type(size) is not int or size < 0):
            raise ValueError('Invalid manifest hash or size')
    return files


def compare(expected, actual):
    return {
        'missing': sorted(expected.keys() - actual.keys()),
        'unexpected': sorted(actual.keys() - expected.keys()),
        'changed': sorted(k for k in expected.keys() & actual.keys()
                          if expected[k] != actual[k])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    capture = sub.add_parser('capture')
    capture.add_argument('directory')
    capture.add_argument('manifest')
    verify = sub.add_parser('verify')
    verify.add_argument('directory')
    verify.add_argument('manifest')
    args = parser.parse_args(argv)
    try:
        base = Path(args.directory).resolve()
        target = Path(args.manifest).resolve()
        if target == base or base in target.parents:
            raise ValueError('Manifest must be outside the data directory')
        if args.command == 'capture':
            data = {'schema': 1, 'files': inventory(args.directory)}
            # Do not overwrite a trusted baseline by accident.
            with target.open('x', encoding='utf-8') as out:
                json.dump(data, out, indent=2, sort_keys=True)
                out.write('\n')
            return 0
        with target.open(encoding='utf-8') as stream:
            expected = validate_manifest(json.load(stream))
        result = compare(expected, inventory(args.directory))
        print(json.dumps(result, indent=2))
        return 1 if any(result.values()) else 0
    except (OSError, ValueError) as error:
        parser.exit(2, f'Input error: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
