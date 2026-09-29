import argparse
import json
import os
from pathlib import Path
import random
import shutil
from fetch_kobo import fetch
from process_data import aggregate

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--xlsx', help='Local export only; requires openpyxl')
    parser.add_argument('--output', default='dist')
    args = parser.parse_args()
    if args.demo and args.xlsx:
        parser.error('Choose demo or xlsx, not both')
    if args.demo:
        rng = random.Random(42)
        records = []
        for day in ['2026-07-09', '2026-07-23', '2026-08-06', '2026-08-20', '2026-09-10', '2026-09-24']:
            for _ in range(rng.randint(12, 20)):
                row = {'viaje': day}
                for k in ['hr', 'education', 'logistics', 'im', 'sm', 'acompa', 'estadia', 'comidas', 'vuelos']:
                    row[k] = rng.choices([1, 2, 3, 4, 5], [1, 2, 8, 35, 54] if k != 'vuelos' else [5, 12, 25, 35, 23])[0]
                records.append(row)
    elif args.xlsx:
        import openpyxl
        workbook = openpyxl.load_workbook(args.xlsx, read_only=True, data_only=True)
        rows = iter(workbook.active.values)
        headers = next(rows)
        records = [dict(zip(headers, row)) for row in rows]
        workbook.close()
    else:
        records = fetch(os.environ['KOBO_SERVER'], os.environ['KOBO_ASSET_UID'], os.environ['KOBO_TOKEN'])
    data = aggregate(records, int(os.environ.get('MIN_RESPONSES', '2')), args.demo)
    output = Path(args.output)
    source = Path(__file__).resolve().parents[1] / 'site'
    if output.resolve() == source.resolve() or source.resolve() in output.resolve().parents:
        raise ValueError('Output must be separate from source')
    shutil.copytree(source, output, dirs_exist_ok=True)
    (output / 'data').mkdir(exist_ok=True)
    (output / 'data/dashboard.json').write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    print('Dashboard built successfully. No raw submissions written.')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Avoid dumping responses, request objects or tokens into CI logs.
        print('Build failed:', str(exc) if isinstance(exc, (ValueError, RuntimeError, KeyError)) else type(exc).__name__)
        raise SystemExit(1)
