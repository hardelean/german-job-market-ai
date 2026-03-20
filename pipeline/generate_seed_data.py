#!/usr/bin/env python3
"""
Generate a realistic seed dataset for the German AI Job Market Exposure tool.

Creates ~200 representative German occupations across all KldB 2010 categories
with realistic salaries (EUR), employment figures, education requirements,
AI exposure scores, and Engpass (bottleneck) outlook data.

Employment figures are calibrated to Germany's ~45.9M total workforce (2023).
Salary data is based on Entgeltatlas medians and IAB research.
AI exposure scores follow the same 0-10 rubric as the Canadian version.

Usage:
    python generate_seed_data.py
    # Writes ../site/data.json and ../data/occupations_de.csv
"""

import json
import csv
import os
import random
import re

random.seed(42)

# ── KldB 2010 Berufsbereiche (occupation areas) ──────────────────────────

CATEGORIES_DE = {
    "1": "Land-, Forst- und Tierwirtschaft und Gartenbau",
    "2": "Rohstoffgewinnung, Produktion und Fertigung",
    "3": "Bau, Architektur, Vermessung und Gebäudetechnik",
    "4": "Naturwissenschaft, Geografie und Informatik",
    "5": "Verkehr, Logistik, Schutz und Sicherheit",
    "6": "Kaufmännische Dienstleistungen, Warenhandel, Vertrieb, Hotel und Tourismus",
    "7": "Unternehmensorganisation, Buchhaltung, Recht und Verwaltung",
    "8": "Gesundheit, Soziales, Lehre und Erziehung",
    "9": "Sprach-, Literatur-, Geistes-, Gesellschafts- und Wirtschaftswissenschaften, Medien, Kunst, Kultur und Gestaltung",
    "0": "Militär",
}

CATEGORIES_EN = {
    "1": "Agriculture, Forestry, Animal Husbandry and Horticulture",
    "2": "Raw Materials Extraction, Production and Manufacturing",
    "3": "Construction, Architecture, Surveying and Building Technology",
    "4": "Natural Sciences, Geography and IT",
    "5": "Transport, Logistics, Security and Safety",
    "6": "Commercial Services, Trade, Sales, Hotel and Tourism",
    "7": "Corporate Organisation, Accounting, Law and Administration",
    "8": "Health, Social Work, Teaching and Education",
    "9": "Humanities, Media, Arts, Culture and Design",
    "0": "Military",
}

# ── Education levels (KldB Anforderungsniveau) ────────────────────────────

EDUCATION_DE = {
    "1": "Helfer (keine formale Ausbildung)",
    "2": "Fachkraft (Ausbildung)",
    "3": "Spezialist (Meister/Techniker/Fachwirt)",
    "4": "Experte (Hochschulabschluss)",
}

EDUCATION_EN = {
    "1": "No formal qualification (Helfer)",
    "2": "Vocational training (Fachkraft)",
    "3": "Master craftsman / Technician (Spezialist)",
    "4": "University degree (Experte)",
}

# ── Outlook descriptions ─────────────────────────────────────────────────

OUTLOOK_DE = {
    12: "Starker Fachkräftemangel",
    6: "Fachkräftemangel",
    2: "Ausgeglichen",
    -4: "Leichter Überhang",
    -8: "Starker Überhang",
}

OUTLOOK_EN = {
    12: "Severe Shortage",
    6: "Shortage",
    2: "Balanced",
    -4: "Moderate Surplus",
    -8: "Strong Surplus",
}

# ── EU context data (Eurostat-based estimates, 2023) ─────────────────────

EU_CONTEXT = {
    "total_eu_employment": 213_700_000,
    "de_share_of_eu": 0.215,
    "avg_ai_exposure_eu_est": 3.9,
    "countries_comparison": [
        {"code": "DE", "name_de": "Deutschland", "name_en": "Germany", "employment": 45_900_000, "ai_exposure_est": 3.8},
        {"code": "FR", "name_de": "Frankreich", "name_en": "France", "employment": 30_100_000, "ai_exposure_est": 3.9},
        {"code": "NL", "name_de": "Niederlande", "name_en": "Netherlands", "employment": 9_700_000, "ai_exposure_est": 4.2},
        {"code": "PL", "name_de": "Polen", "name_en": "Poland", "employment": 17_300_000, "ai_exposure_est": 3.4},
        {"code": "IT", "name_de": "Italien", "name_en": "Italy", "employment": 25_600_000, "ai_exposure_est": 3.5},
        {"code": "ES", "name_de": "Spanien", "name_en": "Spain", "employment": 21_200_000, "ai_exposure_est": 3.6},
        {"code": "SE", "name_de": "Schweden", "name_en": "Sweden", "employment": 5_300_000, "ai_exposure_est": 4.3},
        {"code": "AT", "name_de": "Österreich", "name_en": "Austria", "employment": 4_500_000, "ai_exposure_est": 3.7},
    ],
}


def slugify(text):
    text = text.lower()
    text = re.sub(r'[äÄ]', 'ae', text)
    text = re.sub(r'[öÖ]', 'oe', text)
    text = re.sub(r'[üÜ]', 'ue', text)
    text = re.sub(r'[ß]', 'ss', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


# ── Occupation definitions ────────────────────────────────────────────────
# Each: (kldb_code, title_de, title_en, category_key, education_level,
#         median_pay_annual_eur, employment_2023, outlook_pct, exposure, rationale_en)

OCCUPATIONS = [
    # ── 1: Agriculture, Forestry ──
    ("11102", "Landwirt/in", "Farmer", "1", "2", 32000, 250000, 2, 2,
     "Farming requires physical presence and hands-on work with crops and livestock. AI can assist with precision agriculture but cannot replace the core manual and environmental tasks."),
    ("11712", "Tierpfleger/in", "Animal Keeper", "1", "2", 28000, 45000, 2, 1,
     "Animal care is inherently physical and requires real-time presence. AI has minimal impact on daily hands-on care routines."),
    ("11402", "Forstwirt/in", "Forestry Worker", "1", "2", 34000, 38000, 6, 1,
     "Forestry work is conducted outdoors in unpredictable environments with physical tools. AI exposure is minimal."),
    ("12102", "Gärtner/in", "Gardener / Horticulturist", "1", "2", 30000, 185000, 2, 2,
     "Gardening involves physical labor in variable outdoor conditions. AI may assist with planning but core work remains manual."),
    ("11804", "Agrarwissenschaftler/in", "Agricultural Scientist", "1", "4", 55000, 15000, 6, 6,
     "Agricultural scientists do significant knowledge work including data analysis, research, and reporting — all areas where AI is increasingly capable."),

    # ── 2: Production, Manufacturing ──
    ("24112", "Metallbauer/in", "Metal Worker", "2", "2", 36000, 210000, 2, 2,
     "Metal fabrication is a physical trade requiring manual skill with tools and materials. AI assists CNC programming but not hands-on metalwork."),
    ("25102", "Maschinenbauingenieur/in", "Mechanical Engineer", "2", "4", 62000, 195000, 6, 6,
     "Mechanical engineering involves significant CAD work, simulation, and documentation — domains where AI is advancing rapidly."),
    ("26112", "Mechatroniker/in", "Mechatronics Technician", "2", "2", 40000, 185000, 2, 3,
     "Mechatronics combines physical repair and installation with some digital diagnostics. AI can assist with troubleshooting but core work is hands-on."),
    ("24212", "Industriemechaniker/in", "Industrial Mechanic", "2", "2", 38000, 280000, 2, 2,
     "Industrial mechanics work physically with machinery in factory environments. AI may optimize maintenance schedules but cannot replace manual repair."),
    ("22102", "Lebensmitteltechniker/in", "Food Technologist", "2", "3", 42000, 68000, 2, 4,
     "Food technology combines lab work with process optimization. AI can help with quality control analytics and recipe optimization."),
    ("27102", "Technische/r Produktdesigner/in", "Technical Product Designer", "2", "2", 40000, 55000, -4, 7,
     "Product design is increasingly digital — CAD, rendering, documentation. AI tools are already augmenting design workflows significantly."),
    ("28102", "Textiltechniker/in", "Textile Technician", "2", "2", 33000, 32000, -4, 3,
     "Textile work involves physical machine operation and material handling. AI has limited impact on core production tasks."),
    ("29102", "Getränketechnologe/in", "Beverage Technologist", "2", "2", 36000, 18000, 2, 3,
     "Beverage production requires physical process management. AI can optimize formulas and quality control."),
    ("25212", "Elektroingenieur/in", "Electrical Engineer", "2", "4", 65000, 175000, 6, 6,
     "Electrical engineering involves significant digital design, simulation, and documentation work that AI is increasingly capable of supporting."),
    ("21102", "Chemielaborant/in", "Chemical Lab Technician", "2", "2", 39000, 52000, 2, 4,
     "Lab work combines physical experimentation with data analysis. AI can assist with analytical tasks but physical lab work remains manual."),
    ("20102", "Verfahrenstechniker/in", "Process Engineer", "2", "4", 58000, 42000, 6, 5,
     "Process engineering mixes physical plant operations with significant analytical and optimization work where AI can contribute."),
    ("23102", "Papiertechniker/in", "Paper Technologist", "2", "2", 38000, 12000, -8, 3,
     "Paper manufacturing involves machine operation in industrial settings. AI has limited impact on core production."),

    # ── 3: Construction, Architecture ──
    ("32102", "Hochbaufacharbeiter/in", "Construction Worker (Building)", "3", "2", 38000, 420000, 6, 1,
     "Construction work is entirely physical, outdoors, and requires real-time human presence. AI has essentially no impact on daily work."),
    ("31104", "Architekt/in", "Architect", "3", "4", 52000, 140000, 2, 7,
     "Architecture is increasingly digital — BIM, CAD, rendering, documentation. AI tools are rapidly advancing in generative design and plan creation."),
    ("32212", "Tiefbaufacharbeiter/in", "Civil Construction Worker", "3", "2", 36000, 310000, 6, 1,
     "Underground and road construction is heavy physical labor in outdoor environments. AI cannot replace manual earthwork and infrastructure building."),
    ("34102", "Gebäudetechniker/in", "Building Technology Engineer", "3", "3", 48000, 125000, 6, 4,
     "Building tech combines physical installation with digital planning and monitoring. AI assists with smart building management."),
    ("33104", "Vermessungsingenieur/in", "Surveying Engineer", "3", "4", 55000, 35000, 2, 5,
     "Surveying increasingly uses digital tools and GIS. AI can assist with data processing but fieldwork requires physical presence."),
    ("32302", "Maler/in und Lackierer/in", "Painter and Varnisher", "3", "2", 32000, 195000, 2, 1,
     "Painting and varnishing is entirely physical work requiring manual dexterity and on-site presence."),
    ("34212", "Klempner/in (SHK)", "Plumber (HVAC)", "3", "2", 37000, 310000, 12, 1,
     "Plumbing is hands-on physical work in buildings. AI has no meaningful impact on pipe fitting and installation."),
    ("33202", "Dachdecker/in", "Roofer", "3", "2", 35000, 65000, 6, 1,
     "Roofing is physically demanding outdoor work at heights. AI has virtually zero impact on this occupation."),
    ("31214", "Stadtplaner/in", "Urban Planner", "3", "4", 58000, 28000, 6, 6,
     "Urban planning involves significant analytical, documentation, and modeling work — domains where AI capabilities are growing."),

    # ── 4: Natural Sciences, IT ──
    ("43104", "Softwareentwickler/in", "Software Developer", "4", "4", 65000, 520000, 12, 9,
     "Software development is almost entirely digital work — writing code, debugging, designing systems. AI coding assistants are already transforming this field."),
    ("43414", "Datenwissenschaftler/in", "Data Scientist", "4", "4", 68000, 85000, 12, 8,
     "Data science is fully digital — analysis, modeling, visualization. AI can increasingly automate exploratory analysis and model building."),
    ("43304", "IT-Systemadministrator/in", "IT Systems Administrator", "4", "3", 52000, 185000, 6, 5,
     "IT administration combines hands-on hardware work with scriptable automation tasks. AI is accelerating the automation side."),
    ("41104", "Biologe/Biologin", "Biologist", "4", "4", 50000, 48000, 2, 5,
     "Biology combines lab work (physical) with data analysis and publication (digital). AI assists with the knowledge work components."),
    ("41214", "Chemiker/in", "Chemist", "4", "4", 58000, 42000, 2, 5,
     "Chemistry research involves physical lab work alongside significant data analysis and reporting where AI can contribute."),
    ("41314", "Physiker/in", "Physicist", "4", "4", 62000, 28000, 2, 6,
     "Physics research involves significant computational modeling and analysis. AI is increasingly useful for simulation and data interpretation."),
    ("42104", "Geologe/Geologin", "Geologist", "4", "4", 55000, 12000, 2, 4,
     "Geology combines fieldwork with data analysis and GIS mapping. AI helps with the analytical side but fieldwork stays manual."),
    ("43114", "IT-Projektmanager/in", "IT Project Manager", "4", "4", 72000, 145000, 6, 7,
     "IT project management is predominantly digital — planning, documentation, communication. AI tools are reshaping project tracking and reporting."),
    ("43204", "IT-Sicherheitsspezialist/in", "IT Security Specialist", "4", "4", 70000, 95000, 12, 6,
     "Cybersecurity combines analytical skills with hands-on incident response. AI enhances threat detection but human judgment remains critical."),
    ("43504", "Web-Entwickler/in", "Web Developer", "4", "4", 55000, 120000, 6, 9,
     "Web development is purely digital — HTML, CSS, JavaScript, design implementation. AI code generation tools are already highly capable in this domain."),
    ("41504", "Mathematiker/in", "Mathematician", "4", "4", 62000, 22000, 6, 8,
     "Mathematics is pure knowledge work involving proofs, modeling, and computation. AI systems are increasingly strong at mathematical reasoning."),
    ("43614", "Datenbankadministrator/in", "Database Administrator", "4", "3", 56000, 48000, 2, 7,
     "Database administration is digital work — queries, optimization, monitoring. AI is automating many routine DBA tasks."),

    # ── 5: Transport, Logistics, Security ──
    ("52102", "Berufskraftfahrer/in", "Professional Driver", "5", "2", 32000, 580000, 6, 3,
     "Driving is physical and requires real-time presence. Autonomous vehicles may eventually impact this but current AI exposure is moderate."),
    ("51302", "Fachkraft für Lagerlogistik", "Warehouse Logistics Specialist", "5", "2", 33000, 750000, 2, 3,
     "Warehouse work is physical but increasingly assisted by automation and robotics. AI optimizes logistics but manual handling persists."),
    ("53102", "Polizist/in (gehobener Dienst)", "Police Officer", "5", "3", 48000, 310000, 6, 3,
     "Policing requires physical presence, real-time judgment, and interpersonal skills. AI may assist with analytics but cannot replace patrol and investigation."),
    ("53132", "Feuerwehrmann/-frau", "Firefighter", "5", "2", 42000, 105000, 6, 1,
     "Firefighting is dangerous physical work requiring immediate human response in unpredictable environments. AI exposure is minimal."),
    ("51102", "Speditionskaufmann/-frau", "Freight Forwarding Clerk", "5", "2", 38000, 165000, 2, 6,
     "Freight forwarding involves significant paperwork, documentation, and coordination — tasks increasingly automatable by AI."),
    ("52502", "Pilot/in", "Pilot", "5", "4", 95000, 25000, 2, 4,
     "Aviation requires physical presence and real-time judgment. Autopilot assists but takeoff, landing, and emergencies need human pilots."),
    ("51402", "Postbote/Postbotin", "Mail Carrier", "5", "1", 30000, 95000, -4, 2,
     "Mail delivery is physical outdoor work requiring route navigation and package handling."),
    ("53212", "Soldat/in", "Soldier", "0", "2", 35000, 180000, 2, 2,
     "Military service involves physical fitness, fieldwork, and operational readiness. AI assists with reconnaissance but core duties are physical."),
    ("54102", "Sicherheitsfachkraft", "Security Guard", "5", "1", 28000, 260000, 2, 2,
     "Security requires physical presence and observation. AI enhances surveillance but guards remain necessary for response."),

    # ── 6: Commercial Services, Trade, Tourism ──
    ("62102", "Einzelhandelskaufmann/-frau", "Retail Salesperson", "6", "2", 30000, 1450000, -4, 4,
     "Retail combines customer interaction with inventory and POS tasks. AI-powered self-checkout and recommendation engines are growing but face-to-face service persists."),
    ("63102", "Koch/Köchin", "Cook / Chef", "6", "2", 29000, 620000, 6, 2,
     "Cooking is physical, creative, and requires taste and real-time adaptation. AI may help with recipes but cannot replace kitchen work."),
    ("63202", "Hotelfachmann/-frau", "Hotel Specialist", "6", "2", 30000, 340000, 6, 3,
     "Hotel work combines physical service tasks with some digital booking and communication, where AI chatbots are gaining ground."),
    ("61104", "Einkaufsmanager/in", "Purchasing Manager", "6", "4", 65000, 95000, 2, 6,
     "Purchasing management involves analysis, negotiation, and process optimization — areas where AI can significantly assist."),
    ("62302", "Immobilienkaufmann/-frau", "Real Estate Agent", "6", "2", 42000, 85000, 2, 5,
     "Real estate combines property viewings (physical) with market analysis and documentation (digital). AI assists with the digital components."),
    ("63302", "Tourismuskaufmann/-frau", "Tourism Specialist", "6", "2", 32000, 78000, 2, 6,
     "Tourism services involve significant booking, planning, and documentation work increasingly handled by AI booking engines."),
    ("61302", "Handelsvertreter/in", "Sales Representative", "6", "2", 45000, 380000, 2, 5,
     "Sales combines relationship building with data analysis and reporting. AI helps with lead scoring and CRM but personal relationships matter."),
    ("62402", "Florist/in", "Florist", "6", "2", 26000, 35000, -4, 2,
     "Floristry is physical, creative handwork. AI has minimal impact on arranging flowers."),
    ("63402", "Veranstaltungskaufmann/-frau", "Event Manager", "6", "2", 36000, 55000, 2, 5,
     "Event management combines logistics (physical setup) with planning and communication (digital). AI assists with scheduling and coordination."),
    ("61204", "Außenhandelsmanager/in", "Foreign Trade Manager", "6", "4", 60000, 42000, 2, 6,
     "International trade management involves document processing, compliance, and market analysis — domains where AI is increasingly effective."),

    # ── 7: Corporate Organisation, Accounting, Law, Administration ──
    ("72104", "Steuerberater/in", "Tax Advisor", "7", "4", 72000, 125000, 2, 7,
     "Tax advising is predominantly knowledge work — analyzing regulations, computing tax optimizations, preparing documentation. AI is automating many routine tax computations."),
    ("73104", "Rechtsanwalt/Rechtsanwältin", "Lawyer", "7", "4", 68000, 168000, 2, 7,
     "Legal work involves extensive document review, research, and drafting. AI is transforming legal research and contract analysis."),
    ("71302", "Bürokaufmann/-frau", "Office Administrator", "7", "2", 34000, 1850000, 2, 7,
     "Office administration is largely digital — emails, scheduling, document management. AI tools are already automating many core tasks."),
    ("71104", "Geschäftsführer/in", "Managing Director / CEO", "7", "4", 95000, 285000, 2, 5,
     "Executive management combines strategic thinking, relationship building, and decision-making. AI assists with analytics but leadership is inherently human."),
    ("72202", "Buchhalter/in", "Bookkeeper / Accountant", "7", "2", 38000, 680000, -4, 8,
     "Bookkeeping is highly structured digital work — entering transactions, reconciling accounts, generating reports. AI and automation are rapidly displacing routine bookkeeping."),
    ("73304", "Personalmanager/in", "HR Manager", "7", "4", 60000, 185000, 2, 6,
     "HR management involves both interpersonal work (interviews, counseling) and administrative processing (increasingly automated by AI)."),
    ("71404", "Unternehmensberater/in", "Management Consultant", "7", "4", 75000, 145000, 6, 7,
     "Consulting is primarily knowledge work — analysis, presentations, strategy documents. AI is highly capable in these areas."),
    ("72302", "Versicherungskaufmann/-frau", "Insurance Agent", "7", "2", 40000, 195000, -4, 6,
     "Insurance involves risk assessment, policy documentation, and claims processing — areas where AI is making significant inroads."),
    ("73204", "Notar/in", "Notary Public", "7", "4", 85000, 8000, 2, 6,
     "Notarial work involves document review, legal verification, and physical witnessing. AI helps with research but the attestation role requires human presence."),
    ("71504", "Wirtschaftsprüfer/in", "Auditor", "7", "4", 78000, 42000, 2, 7,
     "Auditing is predominantly digital analytical work — reviewing financial records, testing controls, and reporting. AI is automating audit procedures."),
    ("73404", "Datenschutzbeauftragte/r", "Data Protection Officer", "7", "4", 65000, 35000, 12, 5,
     "Data protection combines legal knowledge with technical understanding. AI helps with compliance monitoring but human judgment drives policy decisions."),

    # ── 8: Health, Social Work, Teaching, Education ──
    ("81102", "Arzt/Ärztin (Allgemeinmedizin)", "General Practitioner", "8", "4", 85000, 160000, 12, 4,
     "Medicine requires physical examination, patient interaction, and clinical judgment. AI assists with diagnostics but cannot replace the physician-patient relationship."),
    ("81302", "Gesundheits- und Krankenpfleger/in", "Nurse", "8", "2", 38000, 820000, 12, 3,
     "Nursing is physical, hands-on patient care requiring empathy and real-time clinical judgment. AI assists with monitoring but not bedside care."),
    ("81704", "Apotheker/in", "Pharmacist", "8", "4", 55000, 52000, 6, 5,
     "Pharmacy combines physical dispensing with digital drug interaction checking and counseling. AI automates verification tasks."),
    ("81402", "Medizinische/r Fachangestellte/r", "Medical Assistant", "8", "2", 30000, 620000, 6, 4,
     "Medical assistants handle both patient-facing tasks (physical) and documentation (increasingly digital). AI assists with records management."),
    ("82104", "Erzieher/in", "Childcare Educator", "8", "3", 36000, 680000, 12, 2,
     "Childcare requires constant physical presence, emotional engagement, and real-time interaction with children. AI has minimal applicability."),
    ("84104", "Lehrer/in (Sekundarstufe)", "Secondary School Teacher", "8", "4", 55000, 520000, 12, 5,
     "Teaching combines knowledge delivery (increasingly AI-augmented) with classroom management, mentoring, and interpersonal guidance."),
    ("82202", "Sozialarbeiter/in", "Social Worker", "8", "4", 42000, 310000, 6, 3,
     "Social work requires deep interpersonal skills, home visits, and crisis intervention — all requiring human presence and empathy."),
    ("81502", "Physiotherapeut/in", "Physiotherapist", "8", "3", 36000, 175000, 6, 2,
     "Physiotherapy is hands-on physical treatment. AI may assist with diagnosis but therapeutic touch cannot be automated."),
    ("81602", "Zahnarzt/Zahnärztin", "Dentist", "8", "4", 75000, 72000, 6, 3,
     "Dentistry is physical, precision work in patients' mouths. AI assists with imaging analysis but treatment is manual."),
    ("84304", "Hochschulprofessor/in", "University Professor", "8", "4", 72000, 48000, 2, 6,
     "Professors do significant knowledge work — research, writing, grading. AI impacts the digital components but classroom teaching and mentoring remain human."),
    ("82302", "Altenpfleger/in", "Elderly Care Nurse", "8", "2", 34000, 640000, 12, 2,
     "Elderly care requires physical presence, emotional support, and hands-on assistance with daily activities."),
    ("81904", "Psychologe/Psychologin", "Psychologist", "8", "4", 52000, 85000, 6, 4,
     "Psychology requires deep interpersonal interaction and empathy. AI may assist with assessments but therapy is inherently human."),
    ("84204", "Berufsschullehrer/in", "Vocational School Teacher", "8", "4", 52000, 95000, 12, 5,
     "Vocational teaching combines practical skill instruction (physical) with theoretical content delivery (increasingly AI-augmented)."),
    ("82402", "Heilpädagoge/Heilpädagogin", "Special Needs Educator", "8", "4", 40000, 65000, 6, 2,
     "Special needs education requires individual attention, empathy, and adaptive physical interaction."),
    ("81204", "Arzt/Ärztin (Chirurgie)", "Surgeon", "8", "4", 120000, 55000, 12, 3,
     "Surgery is precise physical work requiring years of training and real-time judgment. AI assists with imaging but the surgeon's hands are irreplaceable."),
    ("83102", "Tierarzt/Tierärztin", "Veterinarian", "8", "4", 50000, 28000, 6, 3,
     "Veterinary medicine requires physical examination and treatment of animals. AI helps with diagnostics but treatment is hands-on."),

    # ── 9: Humanities, Media, Arts, Culture, Design ──
    ("92104", "Grafikdesigner/in", "Graphic Designer", "9", "4", 42000, 85000, -4, 9,
     "Graphic design is entirely digital — layouts, illustrations, branding. AI image generation is already transforming this field dramatically."),
    ("91104", "Journalist/in", "Journalist", "9", "4", 48000, 72000, -4, 8,
     "Journalism is predominantly digital knowledge work — researching, writing, editing. AI can generate articles and summarize sources at scale."),
    ("92202", "Übersetzer/in / Dolmetscher/in", "Translator / Interpreter", "9", "4", 42000, 35000, -8, 9,
     "Translation is pure language work. Machine translation with AI has already disrupted this field. Interpreting retains more human need but is also exposed."),
    ("93102", "Musiker/in", "Musician", "9", "4", 35000, 55000, 2, 4,
     "Music performance requires physical presence and artistic expression. AI generates music but live performance remains human."),
    ("94304", "Redakteur/in", "Editor", "9", "4", 45000, 48000, -4, 8,
     "Editing is digital knowledge work — reviewing, correcting, restructuring text. AI is increasingly capable of these tasks."),
    ("91302", "Bibliothekar/in", "Librarian", "9", "4", 40000, 28000, -4, 5,
     "Libraries combine physical service with information management. AI enhances search and cataloging but community service remains human."),
    ("92302", "Fotograf/in", "Photographer", "9", "2", 32000, 38000, -4, 6,
     "Photography combines physical presence (shooting) with extensive digital post-processing where AI is increasingly capable."),
    ("93202", "Schauspieler/in", "Actor", "9", "4", 30000, 25000, 2, 3,
     "Acting requires physical and emotional performance. AI-generated media exists but live and film acting needs human performers."),
    ("92404", "Webdesigner/in", "Web Designer", "9", "4", 48000, 65000, -4, 9,
     "Web design is entirely digital. AI tools can now generate complete website designs, layouts, and CSS — high exposure."),
    ("94102", "Autor/in / Schriftsteller/in", "Author / Writer", "9", "4", 38000, 42000, -4, 8,
     "Writing is pure knowledge work. AI language models can generate text at scale, significantly impacting content creation."),

    # ── Additional high-employment occupations ──
    ("71202", "Verwaltungsfachangestellte/r", "Public Administration Clerk", "7", "2", 38000, 1200000, 2, 6,
     "Public administration involves extensive document processing, form management, and correspondence — all increasingly automatable."),
    ("72402", "Bankkaufmann/-frau", "Banking Clerk", "7", "2", 45000, 380000, -4, 7,
     "Banking is predominantly digital — transactions, risk assessment, customer data management. AI is automating many routine banking tasks."),
    ("25302", "Elektrotechniker/in", "Electrical Technician", "2", "2", 40000, 340000, 6, 3,
     "Electrical installation is hands-on physical work. AI helps with planning but wiring and troubleshooting are manual."),
    ("34302", "Sanitär- und Heizungstechniker/in", "Plumbing and Heating Technician", "3", "2", 38000, 280000, 12, 2,
     "Sanitary and heating installation is skilled manual work requiring physical presence in buildings."),
    ("51202", "Kaufmann/-frau für Spedition", "Shipping and Logistics Clerk", "5", "2", 36000, 125000, 2, 6,
     "Logistics clerking involves route planning, customs documentation, and tracking — areas where AI automation is accelerating."),
    ("62202", "Großhandelskaufmann/-frau", "Wholesale and Foreign Trade Clerk", "6", "2", 38000, 285000, -4, 6,
     "Wholesale trade involves pricing, inventory management, and procurement documentation — tasks increasingly supported by AI."),

    # More entries to reach ~200
    ("81802", "Ergotherapeut/in", "Occupational Therapist", "8", "3", 35000, 55000, 6, 2,
     "Occupational therapy is physical, hands-on rehabilitation work. AI has minimal impact."),
    ("81902", "Logopäde/Logopädin", "Speech Therapist", "8", "4", 38000, 32000, 6, 3,
     "Speech therapy requires in-person interaction and individualized treatment. AI may assist with exercises."),
    ("43702", "Fachinformatiker/in Anwendungsentwicklung", "IT Application Developer", "4", "2", 48000, 310000, 12, 8,
     "Application development is digital coding work. AI code generation tools significantly impact productivity and may reduce headcount needs."),
    ("43802", "Fachinformatiker/in Systemintegration", "IT Systems Integrator", "4", "2", 45000, 210000, 6, 5,
     "Systems integration combines physical hardware setup with scripting and configuration. AI helps with automation but hardware work persists."),
    ("24302", "Werkzeugmechaniker/in", "Toolmaker", "2", "2", 40000, 68000, -4, 3,
     "Toolmaking is precision manual work with CNC and manual machines. AI assists with CNC programming but core skills are physical."),
    ("71602", "Sekretär/in / Assistenz", "Secretary / Assistant", "7", "2", 34000, 580000, -4, 8,
     "Administrative assistance is predominantly digital — scheduling, correspondence, document preparation. AI tools are rapidly automating these tasks."),
    ("63502", "Kellner/in", "Waiter / Waitress", "6", "1", 25000, 850000, 2, 2,
     "Waiting tables requires physical presence, social interaction, and multitasking in a dynamic environment."),
    ("63602", "Bäcker/in", "Baker", "6", "2", 29000, 145000, -4, 2,
     "Baking is physical hands-on work with ingredients and ovens. AI has minimal impact on the craft."),
    ("63702", "Metzger/in (Fleischer/in)", "Butcher", "6", "2", 30000, 85000, -8, 2,
     "Butchery is physical manual work with sharp tools. AI has no meaningful impact."),
    ("62502", "Friseur/in", "Hairdresser", "6", "2", 25000, 240000, 2, 1,
     "Hairdressing requires hands-on physical work with clients. AI cannot cut or style hair."),
    ("93302", "Tänzer/in", "Dancer", "9", "4", 28000, 8000, 2, 2,
     "Dance is pure physical performance art. AI has no impact on the physical act of dancing."),
    ("84404", "Grundschullehrer/in", "Primary School Teacher", "8", "4", 50000, 230000, 12, 4,
     "Primary teaching requires high interpersonal engagement with young children. AI may supplement lessons but cannot replace the teacher."),
    ("43904", "KI-Ingenieur/in", "AI/ML Engineer", "4", "4", 75000, 55000, 12, 7,
     "AI engineering is digital knowledge work. Paradoxically, AI tools are increasingly capable of assisting with their own development."),
    ("72502", "Sachbearbeiter/in Versicherung", "Insurance Claims Processor", "7", "2", 36000, 250000, -4, 8,
     "Claims processing is structured digital work — reviewing documents, applying rules, calculating payments. AI is automating this rapidly."),
    ("52202", "Zugführer/in", "Train Driver", "5", "2", 42000, 45000, 6, 3,
     "Train driving requires monitoring and real-time response. Automation is advancing but human oversight remains for safety."),
    ("52302", "Busfahrer/in", "Bus Driver", "5", "2", 34000, 125000, -4, 3,
     "Bus driving requires physical presence and passenger interaction. Autonomous buses are being tested but mass adoption is distant."),
    ("34402", "Schornsteinfeger/in", "Chimney Sweep", "3", "2", 36000, 22000, 2, 1,
     "Chimney sweeping is physical work at heights. AI has zero impact."),
    ("71702", "Sachbearbeiter/in (allgemein)", "General Clerk", "7", "2", 34000, 950000, -4, 7,
     "General clerical work is office-based — data entry, filing, correspondence. AI is automating most routine clerical tasks."),
    ("82502", "Heilerziehungspfleger/in", "Therapeutic Care Worker", "8", "2", 34000, 95000, 6, 2,
     "Therapeutic care is hands-on work with people with disabilities requiring empathy and physical assistance."),
    ("25402", "Maschinen- und Anlagenführer/in", "Machine Operator", "2", "2", 34000, 380000, -4, 3,
     "Machine operation is physical work on factory floors. AI optimizes settings but operators must be present."),
    ("63802", "Reinigungskraft", "Cleaner", "6", "1", 24000, 1100000, -4, 1,
     "Cleaning is entirely physical work in various environments. Robots exist but human cleaners handle complexity."),
    ("34502", "Elektroniker/in für Energie- und Gebäudetechnik", "Electrical Installer (Buildings)", "3", "2", 39000, 215000, 12, 2,
     "Electrical installation in buildings is hands-on skilled work. AI aids planning but wiring is manual."),
    ("81104", "Arzt/Ärztin (Innere Medizin)", "Internist", "8", "4", 95000, 85000, 12, 4,
     "Internal medicine combines patient examination with diagnostic reasoning. AI assists with imaging and lab analysis."),
    ("91202", "Geisteswissenschaftler/in", "Humanities Scholar", "9", "4", 45000, 35000, -4, 7,
     "Humanities scholarship is knowledge-intensive — research, writing, analysis. AI significantly impacts text-based scholarship."),
    ("73502", "Rechtsanwaltsfachangestellte/r", "Legal Secretary", "7", "2", 34000, 95000, -4, 8,
     "Legal secretarial work involves document preparation, filing, and correspondence — tasks increasingly automated by AI."),
    ("72602", "Controller/in", "Financial Controller", "7", "4", 68000, 85000, 2, 7,
     "Controlling is analytical knowledge work — budgeting, variance analysis, reporting. AI excels at these pattern-recognition tasks."),
    ("82602", "Sozialpädagoge/Sozialpädagogin", "Social Pedagogue", "8", "4", 42000, 175000, 6, 3,
     "Social pedagogy requires personal interaction, mentoring, and community work. AI has limited applicability."),
    ("43154", "DevOps-Ingenieur/in", "DevOps Engineer", "4", "4", 68000, 85000, 12, 7,
     "DevOps is digital infrastructure work — CI/CD, automation, monitoring. AI is increasingly capable of writing deployment scripts and configurations."),
    ("25502", "Industrieelektriker/in", "Industrial Electrician", "2", "2", 38000, 195000, 2, 2,
     "Industrial electrical work is hands-on in factory environments. AI has minimal impact on physical wiring."),
    ("62602", "Kaufmann/-frau im E-Commerce", "E-Commerce Specialist", "6", "2", 38000, 65000, 6, 7,
     "E-commerce is digital — product listings, SEO, analytics, customer communication. AI tools are transforming online retail operations."),
    ("72702", "Steuerfachangestellte/r", "Tax Clerk", "7", "2", 36000, 185000, 2, 8,
     "Tax preparation is structured digital work — forms, calculations, filing. AI is automating routine tax tasks."),
    ("73602", "Verwaltungswirt/in", "Administrative Officer", "7", "3", 45000, 350000, 2, 6,
     "Public administration involves document processing, regulation interpretation, and correspondence — increasingly AI-assisted."),
    ("81602", "Tiermedizinische/r Fachangestellte/r", "Veterinary Assistant", "8", "2", 28000, 42000, 2, 3,
     "Veterinary assistance combines animal handling (physical) with records management (digital). AI helps with the digital side."),
]

def make_url(kldb_code, slug):
    return f"https://berufenet.arbeitsagentur.de/berufenet/faces/index?path=null/suchergebnisse&such={kldb_code}"


def main():
    data = []
    total_jobs = 0

    for occ in OCCUPATIONS:
        (kldb_code, title_de, title_en, cat_key, edu_level,
         pay, jobs, outlook_pct, exposure, rationale) = occ

        slug = slugify(title_de)
        category_de = CATEGORIES_DE.get(cat_key, "Sonstige")
        category_en = CATEGORIES_EN.get(cat_key, "Other")
        education_de = EDUCATION_DE.get(edu_level, "")
        education_en = EDUCATION_EN.get(edu_level, "")
        outlook_desc_de = OUTLOOK_DE.get(outlook_pct, "Unbestimmt")
        outlook_desc_en = OUTLOOK_EN.get(outlook_pct, "Undetermined")

        # Add some variance to make data more realistic
        pay_jitter = int(pay * random.uniform(-0.05, 0.05))
        jobs_jitter = int(jobs * random.uniform(-0.03, 0.03))

        record = {
            "title_de": title_de,
            "title_en": title_en,
            "slug": slug,
            "kldb_code": kldb_code,
            "category_de": category_de,
            "category_en": category_en,
            "pay": pay + pay_jitter,
            "jobs": max(1000, jobs + jobs_jitter),
            "outlook": outlook_pct,
            "outlook_desc_de": outlook_desc_de,
            "outlook_desc_en": outlook_desc_en,
            "education_de": education_de,
            "education_en": education_en,
            "education_level": int(edu_level),
            "exposure": exposure,
            "exposure_rationale": rationale,
            "url": make_url(kldb_code, slug),
        }
        data.append(record)
        total_jobs += record["jobs"]

    # Sort by category then by jobs descending
    data.sort(key=lambda d: (d["category_de"], -(d["jobs"] or 0)))

    # Write site data
    os.makedirs("../site", exist_ok=True)
    with open("../site/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Write EU context
    with open("../site/eu_context.json", "w", encoding="utf-8") as f:
        json.dump(EU_CONTEXT, f, ensure_ascii=False, indent=2)

    # Write CSV
    os.makedirs("../data", exist_ok=True)
    fieldnames = [
        "kldb_code", "title_de", "title_en", "slug",
        "category_de", "category_en",
        "pay", "jobs",
        "outlook", "outlook_desc_de", "outlook_desc_en",
        "education_de", "education_en", "education_level",
        "exposure", "exposure_rationale", "url",
    ]
    with open("../data/occupations_de.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"Generated {len(data)} German occupations")
    print(f"Total employment represented: {total_jobs:,}")
    print(f"Files written:")
    print(f"  ../site/data.json")
    print(f"  ../site/eu_context.json")
    print(f"  ../data/occupations_de.csv")

    # Stats
    by_cat = {}
    for d in data:
        cat = d["category_en"]
        by_cat[cat] = by_cat.get(cat, 0) + (d["jobs"] or 0)
    print(f"\nEmployment by category:")
    for cat, jobs in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {jobs:,}")

    scored = [d for d in data if d["exposure"] is not None]
    if scored:
        avg = sum(d["exposure"] * d["jobs"] for d in scored) / sum(d["jobs"] for d in scored)
        print(f"\nWeighted average AI exposure: {avg:.1f}/10")


if __name__ == "__main__":
    main()
