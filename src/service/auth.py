"""Sign in with Apple → our own session token. Apple's rules (developer.apple.com,
"Verifying a user"): verify the signature against Apple's public keys, the nonce, iss ==
https://appleid.apple.com, aud == the app's bundle id, and exp."""
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from . import db
from .config import (APPLE_BUNDLE_ID, APPLE_ISSUER, APPLE_JWKS_URL, DEV_TOKEN,
                     SESSION_DAYS, SESSION_SECRET)

_jwks = PyJWKClient(APPLE_JWKS_URL, cache_keys=True)
_bearer = HTTPBearer(auto_error=False)


def verify_apple_identity_token(identity_token: str, nonce: str | None) -> dict:
    key = _jwks.get_signing_key_from_jwt(identity_token)
    claims = jwt.decode(identity_token, key.key, algorithms=["RS256"],
                        audience=APPLE_BUNDLE_ID, issuer=APPLE_ISSUER)
    if nonce is not None and claims.get("nonce") != nonce:
        raise jwt.InvalidTokenError("nonce mismatch")
    return claims


def issue_session(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    return jwt.encode({"sub": user_id, "exp": exp, "iss": "retain"}, SESSION_SECRET, algorithm="HS256")


def dev_user(con):
    """Curl-testable identity when RETAIN_DEV_TOKEN is set; seeded from data/words.json."""
    row, created = db.upsert_user(con, "dev", "dev@local")
    if created:
        import json
        from .config import ROOT
        words = json.loads((ROOT / "data" / "words.json").read_text())["words"]
        for w in words:
            added = w.get("added") or db.now()
            con.execute("INSERT OR IGNORE INTO words (user_id, word, pos, definition, status, added, day) "
                        "VALUES (?,?,?,?,?,?,?)", (row["id"], w["word"], w.get("pos"), w["definition"],
                                                   w.get("status", "learning"), added, added[:10]))
        con.commit()
    return row


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
                 x_timezone: Annotated[str | None, Header()] = None):
    """The signed-in user's row + tz, day and next_day_at (D51: the app sends X-Timezone)."""
    if creds is None:
        raise HTTPException(401, "missing bearer token")
    con = db.connect()
    try:
        if DEV_TOKEN and creds.credentials == DEV_TOKEN:
            return db.resolve_day(con, dict(dev_user(con)), x_timezone)
        try:
            claims = jwt.decode(creds.credentials, SESSION_SECRET, algorithms=["HS256"], issuer="retain")
        except jwt.PyJWTError as exc:
            raise HTTPException(401, f"invalid session: {exc}")
        row = con.execute("SELECT * FROM users WHERE id=?", (claims["sub"],)).fetchone()
        if row is None:
            raise HTTPException(401, "unknown user")
        return db.resolve_day(con, dict(row), x_timezone)
    finally:
        con.close()
