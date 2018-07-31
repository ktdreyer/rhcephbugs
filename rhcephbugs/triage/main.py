import argparse
import rhcephbugs.triage.update
import rhcephbugs.triage.report


def main():
    parser = argparse.ArgumentParser()

    # top-level subcommands:
    subparsers = parser.add_subparsers()

    # add arguments for each subcommand:
    rhcephbugs.triage.update.add_parser(subparsers)
    rhcephbugs.triage.report.add_parser(subparsers)

    # TODO:
    # triage set-action <bznumber>
    #   Rewrite action description for this single bz.

    args = parser.parse_args()

    args.func(args)
