"""CLI principal del pipeline ETL RetailTech."""

import argparse
import time
import sys


def run_bronze():
    from pipeline.src.bronze import run_bronze as _run
    _run()


def run_silver():
    from pipeline.src.silver import run_silver as _run
    _run()


def run_gold():
    from pipeline.src.gold import run_gold as _run
    _run()


def run_queries():
    from pipeline.src.sql_runner import run_queries as _run
    _run()


STAGES = {
    "bronze": ("Capa Bronze", run_bronze),
    "silver": ("Capa Silver", run_silver),
    "gold": ("Capa Gold", run_gold),
    "queries": ("Queries SQL", run_queries),
}


def run_all():
    """Ejecuta todas las etapas del pipeline."""
    total_start = time.time()
    print("=" * 60)
    print("  RetailTech S.A.S — Pipeline ETL")
    print("=" * 60)

    for key, (label, func) in STAGES.items():
        print(f"\n{'─' * 40}")
        print(f"  {label}")
        print(f"{'─' * 40}")
        start = time.time()
        func()
        elapsed = time.time() - start
        print(f"  [{label}] Completado en {elapsed:.1f}s")

    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"  Pipeline completado en {total_elapsed:.1f}s")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Pipeline ETL RetailTech S.A.S")
    parser.add_argument(
        "command",
        choices=["run", "bronze", "silver", "gold", "queries"],
        help="Comando a ejecutar",
    )
    args = parser.parse_args()

    if args.command == "run":
        run_all()
    else:
        label, func = STAGES[args.command]
        print(f"\n  Ejecutando: {label}")
        start = time.time()
        func()
        elapsed = time.time() - start
        print(f"  [{label}] Completado en {elapsed:.1f}s")


if __name__ == "__main__":
    main()
