"""Sign in with Apple → our own session token. Apple's rules (developer.apple.com,
"Verifying a user"): verify the signature against Apple's public keys, the nonce, iss ==
https://appleid.apple.com, aud == the app's bundle id, and exp."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
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
            con.execute("INSERT OR IGNORE INTO words (user_id, word, pos, definition, status, added) "
                        "VALUES (?,?,?,?,?,?)", (row["id"], w["word"], w.get("pos"), w["definition"],
                                                 w.get("status", "learning"), w.get("added") or db.now()))
        con.commit()
    return row


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    if creds is None:
        raise HTTPException(401, "missing bearer token")
    con = db.connect()
    try:
        if DEV_TOKEN and creds.credentials == DEV_TOKEN:
            return dict(dev_user(con))
        try:
            claims = jwt.decode(creds.credentials, SESSION_SECRET, algorithms=["HS256"], issuer="retain")
        except jwt.PyJWTError as exc:
            raise HTTPException(401, f"invalid session: {exc}")
        row = con.execute("SELECT * FROM users WHERE id=?", (claims["sub"],)).fetchone()
        if row is None:
            raise HTTPException(401, "unknown user")
        return dict(row)
    finally:
        con.close()
