"""Pruebas unitarias de hash de contraseñas y JWT."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.security import TokenService, hash_password, verify_password


class TestPasswordHashing:
    def test_hash_is_not_plain_text_and_uses_argon2id(self) -> None:
        hashed = hash_password("S3cret!")
        assert hashed != "S3cret!"
        assert hashed.startswith("$argon2id$")

    def test_same_password_generates_different_hashes_due_to_salt(self) -> None:
        assert hash_password("S3cret!") != hash_password("S3cret!")

    def test_verify_accepts_correct_password(self) -> None:
        assert verify_password("S3cret!", hash_password("S3cret!")) is True

    def test_verify_rejects_wrong_password(self) -> None:
        assert verify_password("wrong", hash_password("S3cret!")) is False

    def test_verify_returns_false_when_hash_is_missing(self) -> None:
        assert verify_password("anything", None) is False

    def test_verify_returns_false_with_malformed_hash(self) -> None:
        assert verify_password("anything", "not-a-valid-hash") is False


class TestTokenService:
    @pytest.fixture
    def service(self, settings: Settings) -> TokenService:
        return TokenService(settings)

    def test_create_and_decode_roundtrip(self, service: TokenService) -> None:
        token = service.create_access_token("user-1")
        payload = service.decode_access_token(token)
        assert payload.subject == "user-1"
        assert len(payload.jti) == 32
        assert payload.expires_at > datetime.now(UTC)

    def test_each_token_has_unique_jti(self, service: TokenService) -> None:
        a = service.decode_access_token(service.create_access_token("u"))
        b = service.decode_access_token(service.create_access_token("u"))
        assert a.jti != b.jti

    def test_rejects_tampered_token(self, service: TokenService) -> None:
        token = service.create_access_token("user-1")
        with pytest.raises(AuthenticationError):
            service.decode_access_token(token[:-2] + "xx")

    def test_rejects_token_signed_with_other_key(
        self, service: TokenService, settings: Settings
    ) -> None:
        forged = jwt.encode(
            {"sub": "x", "jti": "j", "iat": 1, "exp": 9999999999, "iss": settings.jwt_issuer},
            "another-secret-key-also-long-enough-123456",
            algorithm="HS256",
        )
        with pytest.raises(AuthenticationError):
            service.decode_access_token(forged)

    def test_rejects_expired_token(self, service: TokenService, settings: Settings) -> None:
        past = datetime.now(UTC) - timedelta(hours=2)
        expired = jwt.encode(
            {
                "sub": "u",
                "jti": "j",
                "iat": past,
                "exp": past + timedelta(minutes=1),
                "iss": settings.jwt_issuer,
            },
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(AuthenticationError, match="expiró"):
            service.decode_access_token(expired)

    def test_rejects_unsigned_alg_none_token(self, service: TokenService) -> None:
        unsigned = jwt.encode({"sub": "u"}, key=None, algorithm="none")
        with pytest.raises(AuthenticationError):
            service.decode_access_token(unsigned)


class TestSettings:
    def test_rejects_short_secret(self) -> None:
        with pytest.raises(ValueError):
            Settings(jwt_secret_key="short")

    def test_rejects_non_hmac_algorithm(self) -> None:
        with pytest.raises(ValueError):
            Settings(jwt_secret_key="x" * 40, jwt_algorithm="none")
