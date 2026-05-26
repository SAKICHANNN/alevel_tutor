"""
Comprehensive Resource Index for Cambridge A-Level subjects.
Contains all free resources found through deep web research.
"""
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
RESOURCES_DIR = DATA_DIR / "study_guides"

@dataclass
class Resource:
    title: str
    url: str
    res_type: str  # revision_notes, past_papers, topical_qs, video, flashcards, syllabus, formula_sheet, learner_guide, community, essay_guide, worked_solutions, interactive, planner, textbook
    is_pdf: bool = False
    is_free: bool = True
    description: str = ""
    priority: str = "medium"  # essential, high, medium, low


# ============ CHEMISTRY 9701 ============
CHEMISTRY_RESOURCES = [
    # --- Official Cambridge ---
    Resource("Cambridge Official Syllabus 2025-2027 (9701)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-chemistry-9701/", "syllabus", True, True, "Official syllabus, past papers, mark schemes, examiner reports, grade thresholds, specimen papers, learner guide", "essential"),
    Resource("Data Booklet for Chemistry 9701", "https://www.cambridgeinternational.org/Images/164870-data-booklet.pdf", "formula_sheet", True, True, "Official periodic table, electrode potentials, qualitative analysis notes — provided in exam", "essential"),
    Resource("Learner Guide Chemistry 9701", "https://www.cambridgeinternational.org/Images/697484-learners-guide-for-cambridge-international-as-and-a-level-chemistry-9701.pdf", "learner_guide", True, True, "Explains paper structure, command words, revision checklist, sample answers", "essential"),
    Resource("Cambridge Past Papers Portal (Chemistry)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-chemistry-9701/past-papers/", "past_papers", True, True, "Official past papers, mark schemes, examiner reports — free PDF downloads", "essential"),

    # --- Revision Notes ---
    Resource("Chemguide for CIE (Jim Clark)", "https://www.chemguideforcie.co.uk/index.html", "revision_notes", False, True, "37 topic sections mapped exactly to CAIE 9701 syllabus. Most detailed free notes available.", "essential"),
    Resource("ZNotes — Chemistry 9701", "https://znotes.org", "revision_notes", True, True, "Student-written concise revision notes, quizzes, Discord community. Free PDF download.", "essential"),
    Resource("Chemguide (main site)", "https://www.chemguide.co.uk", "revision_notes", False, True, "In-depth AS/A2 chemistry theory, widely recommended by Cambridge teachers", "high"),
    Resource("SaveMyExams — CIE Chemistry", "https://www.savemyexams.com/a-level/chemistry/cie/22/revision-notes/", "revision_notes", False, False, "Professionally written notes by topic. Free tier gives limited access.", "high"),
    Resource("Physics & Maths Tutor — Chemistry", "https://www.physicsandmathstutor.com/chemistry-revision/", "revision_notes", True, True, "Revision notes, flashcards, past papers (UK spec, overlaps heavily with 9701)", "high"),
    Resource("A-Level Chemistry", "https://www.a-levelchemistry.co.uk", "revision_notes", False, True, "AS/A2 notes, practical guides, exam tips", "medium"),
    Resource("Senpai Corner — CIE Chemistry Notes", "https://www.senpai-corner.com/", "revision_notes", False, True, "Free CIE A Level Chemistry summarized notes", "medium"),

    # --- Past Papers ---
    Resource("PapaCambridge — Chemistry 9701", "https://pastpapers.papacambridge.com/cambridge-international-as-and-a-level-chemistry-9701", "past_papers", True, True, "Past papers, mark schemes, examiner reports, grade thresholds organized by session", "essential"),
    Resource("PastPapers.co — Chemistry 9701", "https://pastpapers.co/cie/A-Level/Chemistry-9701/", "past_papers", True, True, "Full past papers organized by year (2001-2024)", "high"),
    Resource("GCE Guide — Chemistry 9701", "https://papers.gceguide.com/A%20Levels/Chemistry%20(9701)/", "past_papers", True, True, "Comprehensive archive of past papers and mark schemes", "high"),
    Resource("Best Exam Help — Chemistry 9701", "https://www.bestexamhelp.com/cambridge-international-a-level/chemistry-9701", "past_papers", True, True, "Past papers 2010-2025 with mark schemes", "high"),
    Resource("Dynamic Papers — Chemistry 9701", "https://dynamicpapers.com/past-papers/cambridge/?dir=A-Level/Chemistry-9701", "past_papers", True, True, "Past papers browser with quick PDF access", "medium"),

    # --- Topical Questions ---
    Resource("SaveMyExams — Chemistry Topic Questions", "https://www.savemyexams.com/a-level/chemistry/cie/22/topic-questions/", "topical_qs", False, False, "Topic-wise practice questions with model answers", "high"),
    Resource("Exam-Mate — Chemistry Topical", "https://www.exam-mate.com/topicalpastpapers/cambridge/alevel/chemistry-9701/", "topical_qs", False, True, "Past paper questions sorted by syllabus topic", "high"),

    # --- Flashcards ---
    Resource("Quizlet — Cambridge 9701 Chemistry", "https://quizlet.com/en-gb/content/cambridge-as-a-level-chemistry-exam-prep", "flashcards", False, True, "User-generated flashcard decks for definitions, agents, tests, mechanisms", "high"),
    Resource("SaveMyExams — Chemistry Flashcards", "https://www.savemyexams.com/a-level/chemistry/cie/22/flashcards/", "flashcards", False, False, "Flashcards by topic from SaveMyExams", "medium"),
    Resource("Brainscape — A-Level Chemistry", "https://www.brainscape.com/subjects/a-level-chemistry", "flashcards", False, True, "Spaced repetition flashcards", "medium"),

    # --- Video Channels ---
    Resource("Eliot Rintoul — A-Level Chemistry", "https://www.youtube.com/@EliotRintoul", "video", False, True, "Full topic walk-through tutorials covering all major 9701 topics", "essential"),
    Resource("Allery Chemistry", "https://www.youtube.com/@AlleryChemistry", "video", False, True, "Topic-by-topic video lessons for A-Level Chemistry", "high"),
    Resource("ZNotes YouTube", "https://www.youtube.com/c/ZNotes", "video", False, True, "Live revision classes and recorded sessions for CAIE Chemistry", "high"),
    Resource("Science with Hazel", "https://www.youtube.com/@ScienceWithHazel", "video", False, True, "Video lessons and exam walk-throughs", "medium"),

    # --- Community ---
    Resource("ZNotes Discord Community", "https://discord.gg/znotes", "community", False, True, "50K+ students for peer support, live study sessions", "high"),
    Resource("r/alevel Reddit", "https://www.reddit.com/r/alevel/", "community", False, True, "A-Level student community discussions, resource sharing", "medium"),
    Resource("The Student Room — Chemistry", "https://www.thestudentroom.co.uk", "community", False, True, "UK A-Level forum with 9701 threads", "medium"),

    # --- Study Guides ---
    Resource("Grade Threshold Tables (Chemistry)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-chemistry-9701/grade-threshold-tables/", "syllabus", True, True, "Official raw mark → grade boundaries for every exam session", "high"),
    Resource("Examiner Tips for Chemistry 9701 (PDF)", "https://www.learnedguys.com/uploads/files/288/Examiner%20tips.pdf", "essay_guide", True, True, "Cambridge official examiner tips booklet for AS and A Level Chemistry", "essential"),
    Resource("Example Candidate Responses (Chemistry)", "https://nvdiaries.weebly.com/uploads/7/9/6/5/79657776/9701_chemistry_example_candidate_responses_2013.pdf", "essay_guide", True, True, "High/mid/low grade answers with examiner commentary", "essential"),
]


# ============ PHYSICS 9702 ============
PHYSICS_RESOURCES = [
    # --- Official Cambridge ---
    Resource("Cambridge Official Syllabus (9702)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-physics-9702/", "syllabus", True, True, "Official syllabus, past papers, mark schemes, examiner reports, specimen papers", "essential"),
    Resource("Cambridge Learner Guide Physics 9702", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-physics-9702/", "learner_guide", True, True, "Available from the official page — explains paper structure, command words", "essential"),
    Resource("Cambridge Past Papers Portal (Physics)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-physics-9702/past-papers/", "past_papers", True, True, "Official past papers, mark schemes, examiner reports", "essential"),

    # --- Revision Notes ---
    Resource("ZNotes — Physics 9702 AS", "https://znotes.org/caie/as/physics-9702/", "revision_notes", True, True, "Concise student-written revision notes for AS Physics. Free PDF.", "essential"),
    Resource("ZNotes — Physics 9702 A2", "https://znotes.org/caie/a2/physics-9702/", "revision_notes", True, True, "Concise student-written revision notes for A2 Physics. Free PDF.", "essential"),
    Resource("SaveMyExams — CIE Physics", "https://www.savemyexams.com/a-level/physics/cie/22/revision-notes/", "revision_notes", False, False, "Professionally written notes with diagrams. Free tier limited.", "high"),
    Resource("Physics & Maths Tutor — CIE Physics", "https://www.physicsandmathstutor.com/physics-revision/a-level-cie/", "revision_notes", False, True, "Revision notes and past papers for CAIE Physics", "high"),
    Resource("Mega Lecture — Physics Notes", "https://megalecture.com/cambridge-a2-physics-notes/", "revision_notes", True, True, "Free downloadable A2 Physics notes PDF", "high"),
    Resource("RocketRevise — CIE Physics", "https://www.rocketrevise.com/a-level-physics-cie/", "revision_notes", False, True, "Topic-wise revision notes and past papers by topic", "high"),
    Resource("CIE Notes — Physics 9702", "https://www.cienotes.com/cambridge-a-level-physics-9702/", "revision_notes", True, True, "Syllabus, guides, definitions, past papers aggregated", "high"),
    Resource("CramNow — A Level Physics", "https://cramnow.com/physics-a-level/", "revision_notes", False, True, "Free A-Level physics revision notes", "medium"),

    # --- Past Papers ---
    Resource("PapaCambridge — Physics 9702", "https://pastpapers.papacambridge.com/cambridge-international-as-and-a-level-physics-9702", "past_papers", True, True, "Past papers, mark schemes, examiner reports, grade thresholds", "essential"),
    Resource("Best Exam Help — Physics 9702", "https://www.bestexamhelp.com/cambridge-international-a-level/physics-9702", "past_papers", True, True, "Past papers 2010-2025 with mark schemes", "high"),
    Resource("Dynamic Papers — Physics 9702", "https://dynamicpapers.com/past-papers/cambridge/?dir=A-Level/Physics-9702", "past_papers", True, True, "Quick PDF access browser for past papers", "high"),
    Resource("GCE Guide — Physics 9702", "https://papers.gceguide.com/A%20Levels/Physics%20(9702)/", "past_papers", True, True, "Comprehensive archive of past papers and mark schemes", "high"),
    Resource("PastPapers.co — Physics 9702", "https://pastpapers.co/cie/A-Level/Physics-9702", "past_papers", True, True, "Past papers organized by year", "medium"),

    # --- Topical Questions ---
    Resource("Exam-Mate — Physics 9702 Topical", "https://www.exam-mate.com/topicalpastpapers/cambridge/alevel/physics-9702/", "topical_qs", False, True, "Past paper questions sorted by syllabus topic", "high"),
    Resource("RocketRevise — CIE Physics by Topic", "https://www.rocketrevise.com/a-level-physics-cie/", "topical_qs", False, True, "Past papers organized by topic with solutions", "high"),

    # --- YouTube Channels ---
    Resource("ETphysics — CIE Physics 9702", "https://www.youtube.com/@ETphysics", "video", False, True, "Most complete 9702 playlist. Covers all topics + Paper 5.", "essential"),
    Resource("Science Shorts — A Level Physics", "https://www.youtube.com/@ScienceShorts", "video", False, True, "Concise revision videos covering all A-Level physics topics", "high"),
    Resource("TL Physics — CIE 9702", "https://www.youtube.com/@TLPhysics", "video", False, True, "CIE-specific A-Level Physics tutorials and past paper walkthroughs", "high"),
    Resource("Physics Online", "https://www.youtube.com/@PhysicsOnline", "video", False, True, "Comprehensive A-Level physics video lessons", "high"),
    Resource("Centaurus Academy — 9702", "https://www.youtube.com/@CentaurusAcademy", "video", False, True, "CIE A Level Physics 9702 video lectures", "medium"),
    Resource("A Level Physics HQ", "https://www.youtube.com/@ALevelPhysicsHQ", "video", False, True, "CIE past paper walkthroughs", "medium"),

    # --- Paper 5 Resources ---
    Resource("ETphysics — Paper 5 Playlist", "https://www.youtube.com/playlist?list=PL1XxvR7y8P2qNfkNh1Pg4CQKEpKvJKMmB", "video", False, True, "Dedicated Paper 5 Planning/Analysis/Evaluation video walkthroughs", "essential"),
    Resource("Example Candidate Responses P5 (Physics)", "https://papers.xtremepape.rs/CAIE/AS%20and%20A%20Level/Physics%20(9702)/ECR_AS-AL_Physics_9702_P5_v1.pdf", "essay_guide", True, True, "High-level candidate responses with examiner commentary for Paper 5", "essential"),
    Resource("Example Candidate Responses P3 (Physics)", "https://www.learnedguys.com/uploads/files/350/9702_Example_Candidate_Responses_Paper_3_(for_examination_from_2016).pdf", "essay_guide", True, True, "Practical skills example responses with examiner feedback", "essential"),

    # --- Flashcards ---
    Resource("Quizlet — CIE A Level Physics 9702", "https://quizlet.com/subject/cie-a-level-physics-9702/", "flashcards", False, True, "User-generated flashcard sets for definitions and concepts", "high"),
    Resource("AnkiWeb — CIE Physics 9702", "https://ankiweb.net/shared/decks?search=cie+physics+9702", "flashcards", False, True, "Spaced repetition flashcard decks", "medium"),

    # --- Interactive/Full Courses ---
    Resource("Seneca Learning — CIE A Level Physics", "https://senecalearning.com/en-GB/blog/cie-a-level-physics/", "interactive", False, True, "Interactive revision with spaced repetition, gamified learning", "high"),
    Resource("Khan Academy — Physics Library", "https://www.khanacademy.org/science/physics", "interactive", False, True, "Free complete physics courses with video + exercises", "high"),
    Resource("Isaac Physics — Problem Solving", "https://isaacphysics.org/", "interactive", False, True, "Free A-Level physics problem-solving platform by Cambridge University", "high"),

    # --- Community ---
    Resource("ZNotes Discord Community", "https://discord.gg/znotes", "community", False, True, "50K+ students for peer support", "high"),
    Resource("Reddit — r/ALevelPhysics", "https://www.reddit.com/r/ALevelPhysics/", "community", False, True, "Physics-specific A-Level community", "medium"),

    # --- Formula & Definitions ---
    Resource("Cambridge Official Formula List", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-physics-9702/", "formula_sheet", True, True, "Formula list provided in exams — found in syllabus appendix", "essential"),
    Resource("Mega Lecture — Physics Formula Sheet", "https://megalecture.com/a-level-physics-formula-sheet/", "formula_sheet", True, True, "Downloadable formula sheet PDF", "medium"),
]


# ============ ECONOMICS 9708 ============
ECONOMICS_RESOURCES = [
    # --- Official Cambridge ---
    Resource("Cambridge Official Syllabus (9708)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-economics-9708/", "syllabus", True, True, "Official syllabus, past papers, examiner reports, grade thresholds, specimen papers", "essential"),
    Resource("Cambridge Learner Guide Economics 9708", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-economics-9708/", "learner_guide", True, True, "Exam guide with tips, command words, sample answers from Cambridge", "essential"),
    Resource("Cambridge Past Papers Portal (Economics)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-economics-9708/past-papers/", "past_papers", True, True, "Official past papers, mark schemes, examiner reports", "essential"),

    # --- Revision Notes ---
    Resource("SaveMyExams — CIE Economics", "https://www.savemyexams.com/a-level/economics/cie/", "revision_notes", False, False, "Professionally written revision notes, topic questions, flashcards, mock exams", "essential"),
    Resource("ZNotes — Economics 9708", "https://znotes.org", "revision_notes", True, True, "Student-written revision notes for Economics 9708. Free PDF.", "essential"),
    Resource("TutorChase — CAIE Economics Notes", "https://www.tutorchase.com/revision-notes/caie-a-level/economics", "revision_notes", False, True, "Syllabus-matched CAIE Economics revision notes", "high"),
    Resource("Tutor2u — Economics Reference Library", "https://www.tutor2u.net/economics/reference", "revision_notes", False, True, "3400+ study notes, articles, exam technique guides, model answers", "essential"),
    Resource("EduRev — A Level Economics", "https://edurev.in/explore/272/A-Level", "revision_notes", False, False, "Notes, video lectures, tests, flashcards for A Level Economics", "medium"),

    # --- Past Papers ---
    Resource("BestExamHelp — Economics 9708", "https://bestexamhelp.com/exam/cambridge-international-a-level/economics-9708/index.php", "past_papers", True, True, "Past papers 2010-2025 (all 3 sessions/year) with mark schemes", "essential"),
    Resource("PapaCambridge — Economics 9708", "https://papacambridge.com/caie/as-and-a-level/economics-9708/", "past_papers", True, True, "Past papers, examiner reports, grade thresholds", "essential"),
    Resource("GCE Guide — Economics 9708", "https://gceguide.com/past-papers/a-level/economics-9708/", "past_papers", True, True, "Past papers with mark schemes", "high"),

    # --- Essay & Exam Technique ---
    Resource("Specimen Paper Answers P4 (Economics 9708)", "https://www.learnedguys.com/uploads/files/2094/9708_Specimen_Paper_Answers_Paper_4_(for_examination_from_2023).pdf", "essay_guide", True, True, "Official specimen answers with examiner commentary for 20-mark essays", "essential"),
    Resource("A Level Economics 9708 20-Mark Essay Structure", "https://pdfcoffee.com/a-level-economics-9708-20-mark-essay-answer-structure-pdf-free.html", "essay_guide", True, True, "Detailed 5-part essay framework: Introduction → Analysis → Impacts → Evaluation → Conclusion", "essential"),
    Resource("Tutor2u — Economics Essay Technique", "https://www.tutor2u.net/economics/reference", "essay_guide", False, True, "Exam technique guides, essay writing tips, evaluation frameworks", "high"),
    Resource("Economics 9708 Command Words Guide", "https://www.tutopiya.com/blog/a-level/command-words-keywords/cambridge-a-level-economics-9708-command-words-keywords/", "essay_guide", False, True, "Complete command word definitions and what examiners expect for each", "high"),

    # --- YouTube Channels ---
    Resource("EconplusDal", "https://www.youtube.com/@EconPlusDal", "video", False, True, "Most popular A-Level Economics channel. All topics with diagrams + evaluation.", "essential"),
    Resource("Tutor2u Economics YouTube", "https://www.youtube.com/@tutor2u-economics", "video", False, True, "Topic videos, exam technique, case studies, livestreams", "high"),
    Resource("ZNotes YouTube — Economics", "https://www.youtube.com/c/ZNotes", "video", False, True, "CAIE Economics live revision classes", "high"),
    Resource("Khan Academy — Economics", "https://www.khanacademy.org/economics-finance-domain", "interactive", False, True, "Free complete microeconomics & macroeconomics courses", "high"),

    # --- Flashcards ---
    Resource("Quizlet — Cambridge 9708 Economics", "https://quizlet.com", "flashcards", False, True, "Search 'Cambridge 9708 Economics' for definitions, diagrams, theories", "high"),
    Resource("AnkiWeb — Economics 9708", "https://ankiweb.net/shared/decks?search=economics+9708", "flashcards", True, True, "Spaced repetition flashcards in Anki format", "medium"),

    # --- Case Studies & Data Response ---
    Resource("Tutor2u — Economics Case Studies", "https://www.tutor2u.net/economics/reference", "essay_guide", False, True, "Real-world economics case studies with analysis for data response practice", "high"),
    Resource("Economics Help", "https://www.economicshelp.org/", "revision_notes", False, True, "A-Level economics notes, diagrams, essay writing guide with real examples", "high"),

    # --- Community ---
    Resource("ZNotes Discord Community", "https://discord.gg/znotes", "community", False, True, "50K+ students for peer support, live study sessions", "high"),
    Resource("The Student Room — Economics", "https://www.thestudentroom.co.uk", "community", False, True, "Forum discussions, essay sharing, revision tips", "medium"),
    Resource("Reddit — r/alevel", "https://www.reddit.com/r/alevel/", "community", False, True, "Student community for A Level help and resources", "medium"),

    # --- Textbooks ---
    Resource("Cambridge University Press — Endorsed Economics", "https://www.cambridge.org/education", "textbook", False, False, "Official coursebook, workbook, revision guide (publisher samples free)", "medium"),
]


# ============ MATHEMATICS 9709 ============
MATHEMATICS_RESOURCES = [
    # --- Official Cambridge ---
    Resource("Cambridge Official Syllabus (9709)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-mathematics-9709/", "syllabus", True, True, "Official syllabus, past papers, specimen papers, formula booklet", "essential"),
    Resource("Cambridge Formula Booklet (MF19)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-mathematics-9709/", "formula_sheet", True, True, "Official formula booklet provided in exams for Mathematics 9709", "essential"),
    Resource("Cambridge Learner Guide Mathematics 9709", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-mathematics-9709/", "learner_guide", True, True, "Explains paper structure, calculator rules, command words", "essential"),
    Resource("Cambridge Past Papers Portal (Maths)", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-level-mathematics-9709/past-papers/", "past_papers", True, True, "Official past papers and mark schemes", "essential"),

    # --- Revision Notes ---
    Resource("ZNotes — Mathematics 9709", "https://znotes.org", "revision_notes", True, True, "Student-written concise revision notes covering all 9709 components. Free PDF.", "essential"),
    Resource("Physics & Maths Tutor — CIE Maths 9709", "https://www.physicsandmathstutor.com/maths-revision/a-level-cie/", "revision_notes", True, True, "Past paper questions sorted by topic for all components (Pure, Mechanics, Stats). Free PDFs.", "essential"),
    Resource("SaveMyExams — CIE A Level Maths", "https://www.savemyexams.com/a-level/maths/cie/", "revision_notes", False, False, "Professionally written notes with diagrams. Free tier limited.", "high"),

    # --- Worked Solutions ---
    Resource("OnlineMathLearning — 9709 Worked Solutions", "https://www.onlinemathlearning.com/a-level-maths.html", "worked_solutions", False, True, "Step-by-step solutions for EVERY 9709 paper 2020-2024 across all 6 components. FREE.", "essential"),
    Resource("ExamSolutions — CIE Maths", "https://www.examsolutions.net/international-exams/cie/", "worked_solutions", False, True, "Dedicated CIE 9709 section with P1,P2,P3,M1,M2,S1,S2 tutorials + past paper walkthroughs", "essential"),

    # --- Video Tutorials ---
    Resource("Intuitive (YouTube)", "https://www.youtube.com/@intuitive_edu", "video", False, True, "Dedicated 9709 past paper walkthroughs and topic tutorials", "essential"),
    Resource("TLMaths — A-Level Maths", "https://www.tlmaths.com/home/a-level-maths", "video", False, True, "Massive structured library of A-Level Maths videos organized by topic. All free.", "essential"),
    Resource("ZNotes YouTube — Maths 9709", "https://www.youtube.com/c/ZNotes", "video", False, True, "Free live revision classes and recorded sessions for 9709", "high"),
    Resource("ExamSolutions YouTube", "https://www.youtube.com/@ExamSolutions_", "video", False, True, "Past paper walkthroughs and topic tutorials", "high"),

    # --- Past Papers ---
    Resource("GCE Guide — Mathematics 9709", "https://papers.gceguide.com/A%20Levels/Mathematics%20(9709)/", "past_papers", True, True, "Comprehensive archive of past papers and mark schemes organized by year", "essential"),
    Resource("PapaCambridge — Mathematics 9709", "https://papacambridge.com/?s=mathematics+9709", "past_papers", True, True, "Past papers, mark schemes, examiner reports, specimen papers", "high"),
    Resource("PastPapers.co — Mathematics 9709", "https://pastpapers.co/cie/A-Level/Mathematics-9709", "past_papers", True, True, "Organized collection of 9709 past papers", "medium"),

    # --- Topical Questions ---
    Resource("Physics & Maths Tutor — 9709 by Topic", "https://www.physicsandmathstutor.com/maths-revision/a-level-cie/", "topical_qs", True, True, "Past paper questions sorted by topic with mark schemes. Pure, Mechanics, Stats.", "essential"),
    Resource("SaveMyExams — Maths Topic Questions", "https://www.savemyexams.com/a-level/maths/cie/", "topical_qs", False, False, "Exam-style questions organized by topic with model answers", "high"),

    # --- Flashcards ---
    Resource("Maths Genie — A-Level Revision", "https://www.mathsgenie.co.uk/alevel.php", "interactive", False, True, "Free topic-based revision with past papers and worked examples", "high"),
    Resource("Revisely — A-Level Maths", "https://www.revisely.com/alevel/maths", "revision_notes", True, True, "Topic-wise revision notes, flashcards, past papers", "high"),

    # --- Community ---
    Resource("The Student Room — Maths 9709", "https://www.thestudentroom.co.uk/search/?q=9709+mathematics", "community", False, True, "Active forum with 9709 discussion threads and homework help", "high"),
    Resource("ZNotes Discord Community", "https://discord.gg/znotes", "community", False, True, "Live Discord community for Mathematics support", "high"),
    Resource("Reddit — r/alevel", "https://www.reddit.com/r/alevel/", "community", False, True, "Reddit community with 9709 resources and peer help", "medium"),
]


# ============ CROSS-SUBJECT / GENERAL ============
GENERAL_RESOURCES = [
    # --- Official Cambridge ---
    Resource("Cambridge Official — All A-Level Subjects", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-levels/subjects/", "syllabus", False, True, "Full list of all CAIE AS & A Level subjects with syllabi", "essential"),
    Resource("Cambridge Grade Threshold Tables", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-advanced/cambridge-international-as-and-a-levels/grade-threshold-tables/", "syllabus", True, True, "Official raw mark → grade boundaries for every exam session", "essential"),
    Resource("Cambridge Results Statistics", "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-international-as-and-a-levels/results-statistics/", "syllabus", True, True, "Grade distribution percentages by subject and year", "high"),
    Resource("Cambridge Endorsed Resources", "https://www.cambridgeinternational.org/support-and-training-for-schools/endorsed-resources/", "textbook", False, True, "Officially endorsed textbooks and publishers list", "high"),

    # --- Revision Platforms ---
    Resource("ZNotes — All Subjects", "https://znotes.org", "revision_notes", True, True, "Student-written revision notes for all CAIE subjects. 3000+ quizzes, Discord 50K+.", "essential"),
    Resource("Save My Exams", "https://savemyexams.com/a-level/", "revision_notes", False, False, "Topic questions, revision notes, flashcards, mock exams for CIE + UK boards", "essential"),
    Resource("PapaCambridge", "https://papacambridge.com", "past_papers", True, True, "Past papers, notes, topical questions for all CAIE subjects", "essential"),
    Resource("PastPapers.co", "https://pastpapers.co/cie/A-Level", "past_papers", True, True, "Repository of past papers organized by year and subject", "high"),
    Resource("Physics & Maths Tutor", "https://physicsandmathstutor.com", "revision_notes", True, True, "Past papers, revision notes, topic questions for Maths and Sciences", "essential"),
    Resource("Khan Academy", "https://khanacademy.org", "interactive", False, True, "Free complete courses for Maths, Physics, Chemistry, Economics", "high"),
    Resource("Seneca Learning", "https://senecalearning.com", "interactive", False, True, "Interactive revision with spaced repetition, covers CAIE A-Level subjects", "high"),
    Resource("Exam-Mate", "https://exam-mate.com", "topical_qs", False, True, "Topical past paper questions organized by syllabus section", "high"),
    Resource("Dynamic Papers", "https://dynamicpapers.com", "past_papers", True, True, "Past papers browser for Cambridge and other boards", "medium"),
    Resource("Best Exam Help", "https://www.bestexamhelp.com", "past_papers", True, True, "Past papers for all Cambridge subjects with mark schemes", "high"),
    Resource("GCE Guide", "https://gceguide.com", "past_papers", True, True, "Past papers and resources for all Cambridge qualifications", "high"),

    # --- Mobile Apps ---
    Resource("ZNotes App (iOS + Android)", "https://znotes.org", "interactive", False, True, "Study notes, quizzes, AI assistant for CAIE subjects", "high"),
    Resource("Anki / AnkiApp", "https://apps.ankiweb.net/", "flashcards", False, True, "Spaced repetition flashcard system. Create custom decks or use shared A-Level decks.", "high"),
    Resource("Past Papers Pro", "https://apps.apple.com (search)", "past_papers", False, True, "Past paper browser app with mark schemes", "medium"),
    Resource("Seneca App", "https://senecalearning.com", "interactive", False, True, "Gamified revision with algorithmic scheduling on mobile", "medium"),

    # --- Revision Planners ---
    Resource("Get Revising — Timetable Generator", "https://getrevising.co.uk", "planner", False, True, "Create custom revision timetables with resource sharing", "high"),
    Resource("MyStudyLife — Study Planner", "https://mystudylife.com", "planner", False, True, "Cross-platform study planner with exam countdown", "medium"),
    Resource("Adapt App — AI Revision Planner", "https://getadapt.co.uk", "planner", False, False, "AI-based revision timetable generator aligned to exam dates", "medium"),

    # --- Community ---
    Resource("ZNotes Discord (50K+)", "https://discord.gg/znotes", "community", False, True, "Live study sessions, doubt clearing, peer support for all CAIE subjects", "essential"),
    Resource("Reddit — r/alevel", "https://www.reddit.com/r/alevel/", "community", False, True, "Active community for A-Level help, resources, and discussions", "high"),
    Resource("Reddit — r/6thForm", "https://www.reddit.com/r/6thForm/", "community", False, True, "UK A-Level community (also CAIE-relevant)", "medium"),
    Resource("The Student Room", "https://thestudentroom.co.uk", "community", False, True, "A-Level forums by subject with past paper discussions", "high"),

    # --- Study Techniques ---
    Resource("Active Recall Guide", "https://www.cambridgeinternational.org/why-choose-us/parents-and-students/learning-with-lasting-impact/study-resources/", "essay_guide", False, True, "Cambridge official study tips and learner attributes", "high"),
    Resource("Cambridge Revision Planner Template", "https://www.cambridgeinternational.org/", "planner", True, True, "Official Cambridge revision schedule template — search 'learner revision planner PDF'", "high"),
]


ALL_RESOURCES = {
    "9701_chemistry": CHEMISTRY_RESOURCES,
    "9702_physics": PHYSICS_RESOURCES,
    "9708_economics": ECONOMICS_RESOURCES,
    "9709_mathematics": MATHEMATICS_RESOURCES,
    "general": GENERAL_RESOURCES,
}


def get_resources_by_type(subject_code: str, res_type: str) -> list:
    resources = ALL_RESOURCES.get(subject_code, []) + ALL_RESOURCES.get("general", [])
    return [r for r in resources if r.res_type == res_type]


def get_essential_resources(subject_code: str) -> list:
    resources = ALL_RESOURCES.get(subject_code, [])
    return [r for r in resources if r.priority == "essential"]


def get_downloadable_pdfs(subject_code: str) -> list:
    resources = ALL_RESOURCES.get(subject_code, []) + ALL_RESOURCES.get("general", [])
    return [r for r in resources if r.is_pdf]


def count_by_type(subject_code: str):
    resources = ALL_RESOURCES.get(subject_code, [])
    counts = {}
    for r in resources:
        counts[r.res_type] = counts.get(r.res_type, 0) + 1
    return counts
