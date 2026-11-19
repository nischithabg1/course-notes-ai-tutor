import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBJECTS_FILE = PROJECT_ROOT / "data" / "subjects.json"


class SubjectManager:

    def __init__(self):
        SUBJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)

        if not SUBJECTS_FILE.exists():
            self._save_subjects([
                {
                    "name": "Software Engineering",
                    "slug": "software_engineering",
                    "status": "ready"
                },
                {
                    "name": "DBMS",
                    "slug": "dbms",
                    "status": "ready"
                }
            ])

    def get_subjects(self):
        with open(SUBJECTS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    def _save_subjects(self, subjects):
        with open(SUBJECTS_FILE, "w", encoding="utf-8") as file:
            json.dump(subjects, file, indent=4)

    def generate_slug(self, name):
        slug = name.strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "_", slug)
        return slug.strip("_")

    def get_subject(self, identifier):
        identifier = identifier.strip().casefold()

        for subject in self.get_subjects():
            if (
                subject["name"].casefold() == identifier
                or subject["slug"].casefold() == identifier
            ):
                return subject

        return None

    def add_subject(self, name):
        name = name.strip()

        if not name:
            raise ValueError("Subject name cannot be empty.")

        slug = self.generate_slug(name)

        if not slug:
            raise ValueError("Please enter a valid subject name.")

        subjects = self.get_subjects()

        for subject in subjects:
            if (
                subject["name"].casefold() == name.casefold()
                or subject["slug"] == slug
            ):
                raise ValueError("This subject already exists.")

        new_subject = {
            "name": name,
            "slug": slug,
            "status": "pending"
        }

        subjects.append(new_subject)
        self._save_subjects(subjects)

        return new_subject

    def update_status(self, slug, status):
        allowed_statuses = {"pending", "processing", "ready"}

        if status not in allowed_statuses:
            raise ValueError(f"Invalid subject status: {status}")

        subjects = self.get_subjects()

        for subject in subjects:
            if subject["slug"] == slug:
                subject["status"] = status
                self._save_subjects(subjects)
                return subject

        raise ValueError(f"Subject not found: {slug}")