import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

DATA_DIR = Path(__file__).parent.parent / "data"
REPO_DIR = DATA_DIR / "repo"
PAPERS_DIR = DATA_DIR / "past_papers"
SYLLABUS_DIR = DATA_DIR / "syllabus"

GITHUB_REPO_URL = "https://github.com/caie-exams/pastpapers.git"
GITHUB_BRANCH = "A-Levels"

SESSION_CODES = {
    "m": "March",
    "s": "Summer (May/June)",
    "w": "Winter (Oct/Nov)",
}

FILE_TYPES = {
    "qp": "Question Paper",
    "ms": "Mark Scheme",
    "er": "Examiner Report",
    "gt": "Grade Threshold",
    "in": "Insert",
    "ci": "Confidential Instructions",
    "sf": "Support Files",
    "ir": "Instructions",
    "tn": "Teacher Notes",
    "sp": "Specimen Paper",
}


@dataclass
class Subject:
    code: str
    name: str
    directory_name: str
    syllabus_url: str = ""
    textbooks: List[dict] = field(default_factory=list)


SUBJECTS = [
    Subject(
        code="9701",
        name="Chemistry",
        directory_name="Chemistry-(9701)",
        syllabus_url="https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-chemistry-9701/",
        textbooks=[
            {
                "title": "Cambridge International AS & A Level Chemistry Student's Book",
                "publisher": "Collins",
                "isbn": "9780008322588",
                "year": 2020,
            },
            {
                "title": "Cambridge International AS & A Level Chemistry Student's Book (2nd Edition)",
                "publisher": "Hodder Education",
                "isbn": "9781510480230",
                "year": 2020,
            },
            {
                "title": "Cambridge International AS & A Level Chemistry Coursebook with Digital Access",
                "publisher": "Cambridge University Press",
                "isbn": "9781108863193",
                "year": 2020,
            },
        ],
    ),
    Subject(
        code="9702",
        name="Physics",
        directory_name="Physics-(9702)",
        syllabus_url="https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-physics-9702/",
        textbooks=[
            {
                "title": "Cambridge International AS & A Level Physics Student's Book",
                "publisher": "Collins",
                "isbn": "9780008322595",
                "year": 2020,
            },
            {
                "title": "Cambridge International AS & A Level Physics Coursebook with Digital Access",
                "publisher": "Cambridge University Press",
                "isbn": "9781108859035",
                "year": 2020,
            },
            {
                "title": "Cambridge International AS & A Level Complete Physics (3rd Edition)",
                "publisher": "Oxford University Press",
                "isbn": "9781382005395",
                "year": 2020,
            },
        ],
    ),
    Subject(
        code="9708",
        name="Economics",
        directory_name="Economics-(9708)",
        syllabus_url="https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-economics-9708/",
        textbooks=[
            {
                "title": "Cambridge International AS and A Level Economics (2nd Edition)",
                "publisher": "Hodder Education",
                "isbn": "9781398308275",
                "year": 2021,
            },
            {
                "title": "Cambridge International AS & A Level Economics Coursebook with Digital Access (4th Edition)",
                "publisher": "Cambridge University Press",
                "isbn": "9781108903417",
                "year": 2021,
            },
        ],
    ),
    Subject(
        code="9709",
        name="Mathematics",
        directory_name="Mathematics-(9709)",
        syllabus_url="https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-mathematics-9709/",
        textbooks=[
            {
                "title": "Cambridge International AS & A Level Mathematics Pure Mathematics 1 Student's Book",
                "publisher": "Collins",
                "isbn": "9780008257736",
                "year": 2018,
            },
            {
                "title": "Cambridge International AS & A Level Mathematics Pure Mathematics 2 & 3 Student's Book",
                "publisher": "Collins",
                "isbn": "9780008257743",
                "year": 2018,
            },
            {
                "title": "Cambridge International AS & A Level Mathematics Mechanics Student's Book",
                "publisher": "Collins",
                "isbn": "9780008257750",
                "year": 2018,
            },
            {
                "title": "Cambridge International AS & A Level Mathematics Probability & Statistics 1 Student's Book",
                "publisher": "Collins",
                "isbn": "9780008257767",
                "year": 2018,
            },
            {
                "title": "Cambridge International AS & A Level Mathematics Probability & Statistics 2 Student's Book",
                "publisher": "Collins",
                "isbn": "9780008271879",
                "year": 2018,
            },
            {
                "title": "Cambridge International AS & A Level Mathematics Pure Mathematics 1 Coursebook",
                "publisher": "Cambridge University Press",
                "isbn": "9781108562898",
                "year": 2018,
            },
            {
                "title": "Cambridge International AS & A Level Mathematics Mechanics Coursebook",
                "publisher": "Cambridge University Press",
                "isbn": "9781108562942",
                "year": 2018,
            },
        ],
    ),
]

FILE_PATTERN = re.compile(
    r"^(?P<code>\d{4})_"
    r"(?P<session>[msw])"
    r"(?P<year>\d{2})_"
    r"(?P<type>qp|ms|er|gt|in|ci|sf|ir|tn|sp)"
    r"(?:_(?P<paper>\d+))?"
    r"(?P<extra>.*?)"
    r"\.(?P<ext>pdf|doc|docx|xls|xlsx|zip|mp4|mp3)$"
)


def classify_file(filename: str):
    match = FILE_PATTERN.match(filename)
    if not match:
        return None
    info = match.groupdict()
    info["full_year"] = f"20{info['year']}" if len(info["year"]) == 2 else info["year"]
    info["type_name"] = FILE_TYPES.get(info["type"], info["type"])
    return info
