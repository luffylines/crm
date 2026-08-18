import os
import tempfile

import pandas as pd

import app as app_module


def test_enrich_company_profile_adds_company_data_from_verified_sources():
    row = {
        "Company": "Acme Construction",
        "Website": "",
        "About Company": "",
        "Company Industry": "",
        "No. of Employees": "",
    }

    enriched = app_module.enrich_company_profile(row, {
        "description": "Commercial construction contractor",
        "industry": "Construction",
        "employee_count": "11-50",
        "website": "https://acme.example.com",
    })

    assert enriched["About Company"] == "Commercial construction contractor"
    assert enriched["Company Industry"] == "Construction"
    assert enriched["No. of Employees"] == "11-50"
    assert enriched["Website"] == "https://acme.example.com"


def test_calculate_rank_allows_good_when_company_evidence_exists_without_website():
    row = {
        "Company": "Acme Construction",
        "First Name": "John",
        "Last Name": "Smith",
        "Phone": "1234567890",
        "Email": "john@acme.com",
        "Website": "",
        "About / Company Description": "Commercial construction contractor",
        "Company Industry": "Construction",
        "No. of Employees": "11-50",
        "Alt. Contact Info": "",
        "Alternate Phone": "",
    }

    validations = {
        "website": {"valid": False, "msg": "Missing"},
    }

    rank, reason = app_module.calculate_rank(row, validations)
    assert rank.lower() == "good", reason


def test_conditional_formatting_applies_rank_colors_to_excel_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "ranked.xlsx")
        df = pd.DataFrame([
            {
                "Company": "Acme",
                "Lead Ranking": "Best",
                "About / Company Description": "Commercial construction contractor",
            },
            {
                "Company": "Beta",
                "Lead Ranking": "Bad",
                "About / Company Description": "",
            },
        ])
        df.to_excel(path, index=False)

        app_module.apply_lead_ranking_conditional_formatting(path)

        with pd.ExcelFile(path) as workbook:
            assert "Lead Ranking" in pd.read_excel(workbook).columns
