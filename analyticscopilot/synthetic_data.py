"""Seeded synthetic identity-verification data: fictional users and
verification events, in the same shape an identity-verification platform's
raw event stream would land in a warehouse.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np

METHODS = ["document_scan", "selfie_match", "sms_otp", "knowledge_based"]
STATUSES = ["verified", "failed", "pending"]
STATUS_WEIGHTS = [0.78, 0.17, 0.05]
EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "proton.me"]
ORGANIZATIONS = [
    "Acme Health Plan", "Statewide Benefits Office", "Riverside Credit Union",
    "Northbridge Retailers", "Veridian Insurance", "Lakeside University",
]


@dataclass
class SyntheticUser:
    user_id: int
    email_domain: str
    organization: str
    signup_date: dt.date


@dataclass
class SyntheticVerification:
    verification_id: int
    user_id: int
    method: str
    status: str
    created_at: dt.date


def generate_users(n: int = 300, seed: int | None = None) -> list[SyntheticUser]:
    rng = np.random.default_rng(seed)
    start = dt.date(2025, 1, 1)
    users = []
    for i in range(n):
        signup_offset = int(rng.integers(0, 600))
        users.append(SyntheticUser(
            user_id=i,
            email_domain=str(rng.choice(EMAIL_DOMAINS)),
            organization=str(rng.choice(ORGANIZATIONS)),
            signup_date=start + dt.timedelta(days=signup_offset),
        ))
    return users


def generate_verifications(
    users: list[SyntheticUser], avg_per_user: float = 2.5, seed: int | None = None
) -> list[SyntheticVerification]:
    rng = np.random.default_rng(seed)
    verifications = []
    verification_id = 0
    for user in users:
        n_events = int(rng.poisson(avg_per_user))
        for _ in range(n_events):
            days_after_signup = int(rng.integers(0, 365))
            created_at = user.signup_date + dt.timedelta(days=days_after_signup)
            verifications.append(SyntheticVerification(
                verification_id=verification_id,
                user_id=user.user_id,
                method=str(rng.choice(METHODS)),
                status=str(rng.choice(STATUSES, p=STATUS_WEIGHTS)),
                created_at=created_at,
            ))
            verification_id += 1
    return verifications
