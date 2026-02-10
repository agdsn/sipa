from __future__ import annotations

import typing as t

from pydantic import BaseModel, Field, SecretStr, HttpUrl, PositiveFloat, PositiveInt, MySQLDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class ContactAddress(BaseModel):
    name: str
    city: str
    doorbell: str | None = None
    floor: int | None = None
    only_residents: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SIPA_",
        case_sensitive=False,
        extra="ignore",
    )

    # --- observability ---
    sentry_dsn: str | None = None

    # --- content / flatpages ---
    content_url: str | None = None

    flatpages_root: str | None = None
    flatpages_extension: str = ".md"

    # TODO perhaps turn into `extensions` and then mapping `name → config`
    flatpages_markdown_extensions: list[str] = Field(
        default_factory=lambda: [
            "sane_lists",
            "sipa.utils.bootstraped_tables",
            "sipa.utils.link_patch",
            "meta",
            "attr_list",
            "toc",
        ]
    )
    flatpages_markdown_extension_configs: dict[str, dict[str, t.Any]] = Field(
        default_factory=lambda: {
            "sane_lists": {},
            "sipa.utils.bootstraped_tables": {},
            "sipa.utils.link_patch": {},
            "meta": {},
            "attr_list": {},
            "toc": {
                "permalink": "#",
                "permalink_class": "headerlink ms-2 link-secondary link-opacity-75",
            },
        }
    )

    # --- locale / i18n ---
    locale_cookie_name: str = "locale"
    locale_cookie_max_age_seconds: PositiveInt = PositiveInt(86400 * 31)

    languages: dict[str, str] = Field(default_factory=lambda: {"de": "Deutsch", "en": "English"})

    # --- proxy / deployment ---
    num_proxies: int = 1  # TODO do we still need that?

    # --- backend selection ---
    # TODO backends-specific config?
    backend: str = "pycroft"
    backends_config: dict[str, dict[str, t.Any]] = Field(default_factory=dict)

    # --- mail ---
    mailserver_host: str = ""
    mailserver_port: PositiveInt = PositiveInt(25)

    mailserver_security: t.Literal["none", "starttls", "ssl"] = "none"
    mailserver_verify_tls: bool = False
    mailserver_ssl_ca_file: str | None = None
    mailserver_ssl_ca_data: str | None = None

    mailserver_user: str | None = None
    mailserver_password: SecretStr | None = None

    # TODO either set default,
    #  or make required and think about what to provide here for dev.
    contact_sender_mail: str = ""

    # --- database (helios) ---
    db_helios_uri: MySQLDsn = MySQLDsn("mysql+pymysql://verwaltung:secret@userdb.agdsn.network:3306/")
    db_helios_ip_mask: str | None = "10.0.7.%"

    sql_connect_timeout_seconds: int = 2
    sql_connection_recycle_seconds: int = 3600

    # --- pycroft ---
    pycroft_endpoint: HttpUrl = HttpUrl("http://localhost:5000/api/v0/")
    pycroft_api_key: SecretStr = SecretStr("secret")

    # --- integrations ---
    pbx_uri: HttpUrl = HttpUrl("http://voip.agdsn.de:8000")

    meetings_ical_url: HttpUrl = HttpUrl(
        "https://agdsn.de/cloud/remote.php/dav/public-calendars/bgiQmBstmfzRdMeH?export"
    )
    support_ical_url: HttpUrl = HttpUrl(
        "https://agdsn.de/cloud/remote.php/dav/public-calendars/rkocEZqKat8SybNx?export"
    )
    support_max_displayed: PositiveInt = PositiveInt(2)

    # --- status page ---
    status_page_api_subscribe_endpoint: HttpUrl = HttpUrl(
        "https://status.agdsn.net/api/subscribers/subscribers/"
    )
    status_page_api_token: SecretStr = SecretStr("")
    status_page_request_timeout_seconds: PositiveFloat = 1.0

    # --- git hooks ---
    git_update_hook_token: SecretStr | None = SecretStr("")

    # --- features ---
    busstops: list[str] = Field(
        default_factory=lambda: [
            "Zellescher Weg",
            "Strehlener Platz",
            "Weberplatz",
        ]
    )

    # --- usersuite / membership ---
    membership_contribution_cents: int = 500

    payment_recipient: str = "Donald"
    payment_bank: str = "Bank"
    payment_iban: str = "DE09123123123"
    payment_bic: str = "KA"

    # --- contact / misc ---
    contact_addresses: list[ContactAddress] = Field(
        default_factory=lambda: [
            ContactAddress(
                name="Wundtstraße 5",
                doorbell="0100",
                floor=0,
                city="01217 Dresden",
            ),
            ContactAddress(
                name="Hochschulstraße 50",
                doorbell="0103",
                floor=0,
                city="01069 Dresden",
            ),
            ContactAddress(
                name="Borsbergstraße 34",
                floor=7,
                city="01309 Dresden",
                only_residents=True,
            ),
        ]
    )
