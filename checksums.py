#!/usr/bin/env python3
"""Verify the distributed file inventory, or refresh it with --write."""
from pathlib import Path
import argparse
import hashlib


def distributed(root):
    return sorted(p for p in root.rglob('*') if p.is_file()
                  and p.name != 'SHA256SUMS'
                  and not any(part in ('bin','runs','__pycache__')
                              for part in p.relative_to(root).parts))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    inventory={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in distributed(root)}
    manifest=root/'SHA256SUMS'
    if args.write:
        manifest.write_text(''.join(f'{digest}  {name}\n' for name,digest in inventory.items()))
        print(f'Wrote hashes for {len(inventory)} files.')
    else:
        expected={}
        for line in manifest.read_text().splitlines():
            digest,name=line.split('  ',1)
            assert name not in expected,name
            expected[name]=digest
        assert expected==inventory,'Package inventory or content differs from SHA256SUMS'
        print(f'PASS: all {len(inventory)} distributed files match SHA256SUMS.')
