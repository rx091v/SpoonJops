from enum import StrEnum


class ApplicationStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"


class JobSource(StrEnum):
    LINKEDIN = "linkedin"
    INSTAHYRE = "instahyre"
    NAUKRI = "naukri"
    INDEED = "indeed"
    WELLFOUND = "wellfound"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    COMPANY = "company"
