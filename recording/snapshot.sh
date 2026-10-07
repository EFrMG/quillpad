#!/usr/bin/env sh
# Save or restore the install's local records, so a retake starts from the same state.
#
#   recording/snapshot.sh save seeded
#   recording/snapshot.sh restore seeded
#
# Restore replaces triage-o-mator/config, data and reports with the saved copy. It does not undo anything published to GitHub.
set -e

cd "$(dirname "$0")/.."
mkdir -p recording/.snapshots
archive="recording/.snapshots/${2:?name the snapshot}.tgz"

case "$1" in
save)
	tar czf "$archive" -C triage-o-mator config data reports
	echo "saved $archive"
	;;
restore)
	test -f "$archive" || { echo "no snapshot at $archive" >&2; exit 1; }
	rm -rf triage-o-mator/config triage-o-mator/data triage-o-mator/reports
	tar xzf "$archive" -C triage-o-mator
	echo "restored $archive"
	;;
*)
	echo "usage: recording/snapshot.sh save|restore NAME" >&2
	exit 2
	;;
esac
