from pathlib import Path

from ai_xp.database import FileDatabase


def main():
    inputs_lookup_dir_path = Path("inputs").resolve()
    outputs_lookup_dir_path = Path("generated").resolve()
    do_fetch_transcripts = False
    do_fetch_metadata = True
    do_fetch_llm_outputs = False

    db = FileDatabase.from_paths(inputs_lookup_dir_path, outputs_lookup_dir_path)

    if do_fetch_transcripts:
        db = db.refresh()
        db.fetch_missing_transcripts()

    if do_fetch_metadata:
        db = db.refresh()
        db.fetch_missing_metadata()

    if do_fetch_llm_outputs:
        db = db.refresh()
        db.fetch_missing_llm_outputs()


if __name__ == "__main__":
    main()
