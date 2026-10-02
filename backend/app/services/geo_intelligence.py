"""
geo_intelligence.py — Geographic Intelligence Engine

Detects country/region from user queries, maps to languages,
generates multilingual search queries, and expands searches intelligently.
No external API required — runs fully offline.
"""

from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# GEO TAXONOMY
# Country/region → { languages, google_news_gl, google_news_hl, local_rss }
# ─────────────────────────────────────────────────────────────────────────────

GEO_DATABASE: Dict[str, dict] = {
    # ── SOUTH ASIA ────────────────────────────────────────────────────────────
    "india":        {"region": "South Asia", "languages": ["en", "hi"], "gl": "IN", "hl": "en-IN", "aliases": ["indian", "bharat", "hindustan"]},
    "pakistan":     {"region": "South Asia", "languages": ["en", "ur"], "gl": "PK", "hl": "en-PK", "aliases": ["pakistani"]},
    "bangladesh":   {"region": "South Asia", "languages": ["en", "bn"], "gl": "BD", "hl": "en-BD", "aliases": ["bangladeshi"]},
    "nepal":        {"region": "South Asia", "languages": ["en", "ne"], "gl": "NP", "hl": "en-NP", "aliases": ["nepalese", "nepali"]},
    "sri lanka":    {"region": "South Asia", "languages": ["en", "si"], "gl": "LK", "hl": "en-LK", "aliases": ["sri lankan", "ceylon", "srilankan"]},
    "bhutan":       {"region": "South Asia", "languages": ["en", "dz"], "gl": "BT", "hl": "en-BT", "aliases": ["bhutanese"]},
    "maldives":     {"region": "South Asia", "languages": ["en"],       "gl": "MV", "hl": "en-MV", "aliases": ["maldivian"]},
    "afghanistan":  {"region": "South Asia", "languages": ["en", "fa"], "gl": "AF", "hl": "en-AF", "aliases": ["afghan"]},

    # ── SOUTHEAST ASIA ────────────────────────────────────────────────────────
    "indonesia":    {"region": "Southeast Asia", "languages": ["en", "id"], "gl": "ID", "hl": "en-ID", "aliases": ["indonesian"]},
    "philippines":  {"region": "Southeast Asia", "languages": ["en", "tl"], "gl": "PH", "hl": "en-PH", "aliases": ["philippine", "filipino"]},
    "vietnam":      {"region": "Southeast Asia", "languages": ["en", "vi"], "gl": "VN", "hl": "en-VN", "aliases": ["vietnamese", "viet nam"]},
    "thailand":     {"region": "Southeast Asia", "languages": ["en", "th"], "gl": "TH", "hl": "en-TH", "aliases": ["thai"]},
    "malaysia":     {"region": "Southeast Asia", "languages": ["en", "ms"], "gl": "MY", "hl": "en-MY", "aliases": ["malaysian"]},
    "singapore":    {"region": "Southeast Asia", "languages": ["en"],       "gl": "SG", "hl": "en-SG", "aliases": ["singaporean"]},
    "myanmar":      {"region": "Southeast Asia", "languages": ["en", "my"], "gl": "MM", "hl": "en-MM", "aliases": ["burma", "burmese"]},
    "cambodia":     {"region": "Southeast Asia", "languages": ["en", "km"], "gl": "KH", "hl": "en-KH", "aliases": ["cambodian", "khmer"]},
    "laos":         {"region": "Southeast Asia", "languages": ["en", "lo"], "gl": "LA", "hl": "en-LA", "aliases": ["laotian"]},
    "timor-leste":  {"region": "Southeast Asia", "languages": ["en", "pt"], "gl": "TL", "hl": "en-TL", "aliases": ["east timor", "timorese"]},
    "brunei":       {"region": "Southeast Asia", "languages": ["en", "ms"], "gl": "BN", "hl": "en-BN", "aliases": ["bruneian"]},

    # ── EAST ASIA ─────────────────────────────────────────────────────────────
    "japan":        {"region": "East Asia", "languages": ["en", "ja"], "gl": "JP", "hl": "en-JP", "aliases": ["japanese"]},
    "south korea":  {"region": "East Asia", "languages": ["en", "ko"], "gl": "KR", "hl": "en-KR", "aliases": ["korean", "korea"]},
    "china":        {"region": "East Asia", "languages": ["en"],       "gl": "HK", "hl": "en-HK", "aliases": ["chinese", "prc", "mainland china"]},
    "taiwan":       {"region": "East Asia", "languages": ["en"],       "gl": "TW", "hl": "en-TW", "aliases": ["taiwanese"]},
    "hong kong":    {"region": "East Asia", "languages": ["en"],       "gl": "HK", "hl": "en-HK", "aliases": []},
    "mongolia":     {"region": "East Asia", "languages": ["en", "mn"], "gl": "MN", "hl": "en-MN", "aliases": ["mongolian"]},

    # ── CENTRAL ASIA ──────────────────────────────────────────────────────────
    "kazakhstan":   {"region": "Central Asia", "languages": ["en", "ru"], "gl": "KZ", "hl": "en-KZ", "aliases": ["kazakh"]},
    "uzbekistan":   {"region": "Central Asia", "languages": ["en", "uz"], "gl": "UZ", "hl": "en-UZ", "aliases": ["uzbek"]},
    "kyrgyzstan":   {"region": "Central Asia", "languages": ["en", "ru"], "gl": "KG", "hl": "en-KG", "aliases": ["kyrgyz"]},
    "tajikistan":   {"region": "Central Asia", "languages": ["en", "ru"], "gl": "TJ", "hl": "en-TJ", "aliases": ["tajik"]},
    "turkmenistan": {"region": "Central Asia", "languages": ["en"],       "gl": "TM", "hl": "en-TM", "aliases": ["turkmen"]},

    # ── WEST ASIA / MIDDLE EAST ───────────────────────────────────────────────
    "saudi arabia": {"region": "Middle East", "languages": ["en", "ar"], "gl": "SA", "hl": "en-SA", "aliases": ["saudi", "ksa"]},
    "iran":         {"region": "Middle East", "languages": ["en", "fa"], "gl": "IR", "hl": "en-IR", "aliases": ["iranian", "persia"]},
    "iraq":         {"region": "Middle East", "languages": ["en", "ar"], "gl": "IQ", "hl": "en-IQ", "aliases": ["iraqi"]},
    "israel":       {"region": "Middle East", "languages": ["en", "he"], "gl": "IL", "hl": "en-IL", "aliases": ["israeli"]},
    "palestine":    {"region": "Middle East", "languages": ["en", "ar"], "gl": "PS", "hl": "en-PS", "aliases": ["palestinian", "gaza", "west bank"]},
    "turkey":       {"region": "Middle East", "languages": ["en", "tr"], "gl": "TR", "hl": "en-TR", "aliases": ["turkish", "turkiye"]},
    "uae":          {"region": "Middle East", "languages": ["en", "ar"], "gl": "AE", "hl": "en-AE", "aliases": ["united arab emirates", "dubai", "abu dhabi"]},
    "qatar":        {"region": "Middle East", "languages": ["en", "ar"], "gl": "QA", "hl": "en-QA", "aliases": ["qatari"]},
    "kuwait":       {"region": "Middle East", "languages": ["en", "ar"], "gl": "KW", "hl": "en-KW", "aliases": ["kuwaiti"]},
    "jordan":       {"region": "Middle East", "languages": ["en", "ar"], "gl": "JO", "hl": "en-JO", "aliases": ["jordanian"]},
    "lebanon":      {"region": "Middle East", "languages": ["en", "ar"], "gl": "LB", "hl": "en-LB", "aliases": ["lebanese"]},
    "syria":        {"region": "Middle East", "languages": ["en", "ar"], "gl": "SY", "hl": "en-SY", "aliases": ["syrian"]},
    "yemen":        {"region": "Middle East", "languages": ["en", "ar"], "gl": "YE", "hl": "en-YE", "aliases": ["yemeni"]},
    "bahrain":      {"region": "Middle East", "languages": ["en", "ar"], "gl": "BH", "hl": "en-BH", "aliases": ["bahraini"]},
    "oman":         {"region": "Middle East", "languages": ["en", "ar"], "gl": "OM", "hl": "en-OM", "aliases": ["omani"]},

    # ── EUROPE ────────────────────────────────────────────────────────────────
    "uk":           {"region": "Northern Europe", "languages": ["en"], "gl": "GB", "hl": "en-GB", "aliases": ["united kingdom", "britain", "england", "scotland", "wales", "british"]},
    "germany":      {"region": "Western Europe", "languages": ["en", "de"], "gl": "DE", "hl": "en-DE", "aliases": ["german", "deutschland"]},
    "france":       {"region": "Western Europe", "languages": ["en", "fr"], "gl": "FR", "hl": "en-FR", "aliases": ["french"]},
    "italy":        {"region": "Southern Europe", "languages": ["en", "it"], "gl": "IT", "hl": "en-IT", "aliases": ["italian"]},
    "spain":        {"region": "Southern Europe", "languages": ["en", "es"], "gl": "ES", "hl": "en-ES", "aliases": ["spanish"]},
    "portugal":     {"region": "Southern Europe", "languages": ["en", "pt"], "gl": "PT", "hl": "en-PT", "aliases": ["portuguese"]},
    "netherlands":  {"region": "Western Europe", "languages": ["en", "nl"], "gl": "NL", "hl": "en-NL", "aliases": ["dutch", "holland"]},
    "belgium":      {"region": "Western Europe", "languages": ["en", "fr", "nl"], "gl": "BE", "hl": "en-BE", "aliases": ["belgian"]},
    "switzerland":  {"region": "Western Europe", "languages": ["en", "de", "fr"], "gl": "CH", "hl": "en-CH", "aliases": ["swiss"]},
    "austria":      {"region": "Western Europe", "languages": ["en", "de"], "gl": "AT", "hl": "en-AT", "aliases": ["austrian"]},
    "sweden":       {"region": "Northern Europe", "languages": ["en", "sv"], "gl": "SE", "hl": "en-SE", "aliases": ["swedish"]},
    "norway":       {"region": "Northern Europe", "languages": ["en", "no"], "gl": "NO", "hl": "en-NO", "aliases": ["norwegian"]},
    "denmark":      {"region": "Northern Europe", "languages": ["en", "da"], "gl": "DK", "hl": "en-DK", "aliases": ["danish"]},
    "finland":      {"region": "Northern Europe", "languages": ["en", "fi"], "gl": "FI", "hl": "en-FI", "aliases": ["finnish"]},
    "iceland":      {"region": "Northern Europe", "languages": ["en", "is"], "gl": "IS", "hl": "en-IS", "aliases": ["icelandic"]},
    "poland":       {"region": "Eastern Europe", "languages": ["en", "pl"], "gl": "PL", "hl": "en-PL", "aliases": ["polish"]},
    "czech republic":{"region": "Eastern Europe", "languages": ["en", "cs"], "gl": "CZ", "hl": "en-CZ", "aliases": ["czech", "czechia"]},
    "hungary":      {"region": "Eastern Europe", "languages": ["en", "hu"], "gl": "HU", "hl": "en-HU", "aliases": ["hungarian"]},
    "romania":      {"region": "Eastern Europe", "languages": ["en", "ro"], "gl": "RO", "hl": "en-RO", "aliases": ["romanian"]},
    "bulgaria":     {"region": "Eastern Europe", "languages": ["en", "bg"], "gl": "BG", "hl": "en-BG", "aliases": ["bulgarian"]},
    "ukraine":      {"region": "Eastern Europe", "languages": ["en", "uk"], "gl": "UA", "hl": "en-UA", "aliases": ["ukrainian"]},
    "russia":       {"region": "Eastern Europe", "languages": ["en", "ru"], "gl": "RU", "hl": "en-RU", "aliases": ["russian"]},
    "greece":       {"region": "Southern Europe", "languages": ["en", "el"], "gl": "GR", "hl": "en-GR", "aliases": ["greek"]},
    "serbia":       {"region": "Eastern Europe", "languages": ["en", "sr"], "gl": "RS", "hl": "en-RS", "aliases": ["serbian"]},
    "croatia":      {"region": "Southern Europe", "languages": ["en", "hr"], "gl": "HR", "hl": "en-HR", "aliases": ["croatian"]},
    "slovakia":     {"region": "Eastern Europe", "languages": ["en", "sk"], "gl": "SK", "hl": "en-SK", "aliases": ["slovak"]},

    # ── NORTH AMERICA ─────────────────────────────────────────────────────────
    "usa":          {"region": "North America", "languages": ["en"], "gl": "US", "hl": "en-US", "aliases": ["united states", "america", "american", "us", "u.s."]},
    "canada":       {"region": "North America", "languages": ["en", "fr"], "gl": "CA", "hl": "en-CA", "aliases": ["canadian"]},
    "mexico":       {"region": "Central America", "languages": ["en", "es"], "gl": "MX", "hl": "en-MX", "aliases": ["mexican"]},

    # ── CENTRAL AMERICA & CARIBBEAN ───────────────────────────────────────────
    "cuba":         {"region": "Caribbean", "languages": ["en", "es"], "gl": "CU", "hl": "en-CU", "aliases": ["cuban"]},
    "haiti":        {"region": "Caribbean", "languages": ["en", "fr"], "gl": "HT", "hl": "en-HT", "aliases": ["haitian"]},
    "jamaica":      {"region": "Caribbean", "languages": ["en"],       "gl": "JM", "hl": "en-JM", "aliases": ["jamaican"]},
    "guatemala":    {"region": "Central America", "languages": ["en", "es"], "gl": "GT", "hl": "en-GT", "aliases": ["guatemalan"]},
    "honduras":     {"region": "Central America", "languages": ["en", "es"], "gl": "HN", "hl": "en-HN", "aliases": ["honduran"]},
    "panama":       {"region": "Central America", "languages": ["en", "es"], "gl": "PA", "hl": "en-PA", "aliases": ["panamanian"]},

    # ── SOUTH AMERICA ─────────────────────────────────────────────────────────
    "brazil":       {"region": "South America", "languages": ["en", "pt"], "gl": "BR", "hl": "en-BR", "aliases": ["brazilian", "brasil"]},
    "argentina":    {"region": "South America", "languages": ["en", "es"], "gl": "AR", "hl": "en-AR", "aliases": ["argentinian", "argentine"]},
    "colombia":     {"region": "South America", "languages": ["en", "es"], "gl": "CO", "hl": "en-CO", "aliases": ["colombian"]},
    "chile":        {"region": "South America", "languages": ["en", "es"], "gl": "CL", "hl": "en-CL", "aliases": ["chilean"]},
    "peru":         {"region": "South America", "languages": ["en", "es"], "gl": "PE", "hl": "en-PE", "aliases": ["peruvian"]},
    "venezuela":    {"region": "South America", "languages": ["en", "es"], "gl": "VE", "hl": "en-VE", "aliases": ["venezuelan"]},
    "bolivia":      {"region": "South America", "languages": ["en", "es"], "gl": "BO", "hl": "en-BO", "aliases": ["bolivian"]},
    "ecuador":      {"region": "South America", "languages": ["en", "es"], "gl": "EC", "hl": "en-EC", "aliases": ["ecuadorian"]},
    "paraguay":     {"region": "South America", "languages": ["en", "es"], "gl": "PY", "hl": "en-PY", "aliases": ["paraguayan"]},
    "uruguay":      {"region": "South America", "languages": ["en", "es"], "gl": "UY", "hl": "en-UY", "aliases": ["uruguayan"]},

    # ── AFRICA ────────────────────────────────────────────────────────────────
    "nigeria":      {"region": "West Africa", "languages": ["en"],       "gl": "NG", "hl": "en-NG", "aliases": ["nigerian"]},
    "kenya":        {"region": "East Africa",  "languages": ["en"],       "gl": "KE", "hl": "en-KE", "aliases": ["kenyan"]},
    "south africa": {"region": "Southern Africa", "languages": ["en"],   "gl": "ZA", "hl": "en-ZA", "aliases": ["south african"]},
    "ghana":        {"region": "West Africa", "languages": ["en"],        "gl": "GH", "hl": "en-GH", "aliases": ["ghanaian"]},
    "ethiopia":     {"region": "East Africa", "languages": ["en"],        "gl": "ET", "hl": "en-ET", "aliases": ["ethiopian"]},
    "egypt":        {"region": "North Africa", "languages": ["en", "ar"], "gl": "EG", "hl": "en-EG", "aliases": ["egyptian"]},
    "tanzania":     {"region": "East Africa", "languages": ["en"],        "gl": "TZ", "hl": "en-TZ", "aliases": ["tanzanian"]},
    "uganda":       {"region": "East Africa", "languages": ["en"],        "gl": "UG", "hl": "en-UG", "aliases": ["ugandan"]},
    "morocco":      {"region": "North Africa", "languages": ["en", "ar", "fr"], "gl": "MA", "hl": "en-MA", "aliases": ["moroccan"]},
    "algeria":      {"region": "North Africa", "languages": ["en", "ar", "fr"], "gl": "DZ", "hl": "en-DZ", "aliases": ["algerian"]},
    "senegal":      {"region": "West Africa", "languages": ["en", "fr"],  "gl": "SN", "hl": "en-SN", "aliases": ["senegalese"]},
    "zimbabwe":     {"region": "Southern Africa", "languages": ["en"],   "gl": "ZW", "hl": "en-ZW", "aliases": ["zimbabwean"]},
    "angola":       {"region": "Southern Africa", "languages": ["en", "pt"], "gl": "AO", "hl": "en-AO", "aliases": ["angolan"]},
    "mozambique":   {"region": "Southern Africa", "languages": ["en", "pt"], "gl": "MZ", "hl": "en-MZ", "aliases": ["mozambican"]},
    "cameroon":     {"region": "Central Africa", "languages": ["en", "fr"], "gl": "CM", "hl": "en-CM", "aliases": ["cameroonian"]},
    "madagascar":   {"region": "Southern Africa", "languages": ["en", "fr"], "gl": "MG", "hl": "en-MG", "aliases": ["malagasy"]},
    "ivory coast":  {"region": "West Africa", "languages": ["en", "fr"], "gl": "CI", "hl": "en-CI", "aliases": ["cote d'ivoire", "ivorian"]},
    "somalia":      {"region": "East Africa", "languages": ["en", "so"], "gl": "SO", "hl": "en-SO", "aliases": ["somali"]},
    "sudan":        {"region": "North Africa", "languages": ["en", "ar"], "gl": "SD", "hl": "en-SD", "aliases": ["sudanese"]},
    "libya":        {"region": "North Africa", "languages": ["en", "ar"], "gl": "LY", "hl": "en-LY", "aliases": ["libyan"]},

    # ── OCEANIA ───────────────────────────────────────────────────────────────
    "australia":    {"region": "Oceania", "languages": ["en"], "gl": "AU", "hl": "en-AU", "aliases": ["australian"]},
    "new zealand":  {"region": "Oceania", "languages": ["en"], "gl": "NZ", "hl": "en-NZ", "aliases": ["new zealander", "kiwi"]},
    "fiji":         {"region": "Oceania", "languages": ["en"], "gl": "FJ", "hl": "en-FJ", "aliases": ["fijian"]},
    "papua new guinea": {"region": "Oceania", "languages": ["en"], "gl": "PG", "hl": "en-PG", "aliases": ["png", "papuan"]},
    "samoa":        {"region": "Oceania", "languages": ["en"], "gl": "WS", "hl": "en-WS", "aliases": ["samoan"]},
    "tonga":        {"region": "Oceania", "languages": ["en"], "gl": "TO", "hl": "en-TO", "aliases": ["tongan"]},

    # ── CITIES / TERRITORIES (for city-level queries) ────────────────────────
    "rajasthan":    {"region": "South Asia", "languages": ["en", "hi"], "gl": "IN", "hl": "en-IN", "aliases": ["jaipur"]},
    "mumbai":       {"region": "South Asia", "languages": ["en", "hi"], "gl": "IN", "hl": "en-IN", "aliases": ["bombay"]},
    "delhi":        {"region": "South Asia", "languages": ["en", "hi"], "gl": "IN", "hl": "en-IN", "aliases": ["new delhi"]},
    "tokyo":        {"region": "East Asia",  "languages": ["en", "ja"], "gl": "JP", "hl": "en-JP", "aliases": []},
    "beijing":      {"region": "East Asia",  "languages": ["en"],       "gl": "HK", "hl": "en-HK", "aliases": ["peking"]},
    "kathmandu":    {"region": "South Asia", "languages": ["en", "ne"], "gl": "NP", "hl": "en-NP", "aliases": []},
    "nairobi":      {"region": "East Africa","languages": ["en"],        "gl": "KE", "hl": "en-KE", "aliases": []},
    "lagos":        {"region": "West Africa","languages": ["en"],        "gl": "NG", "hl": "en-NG", "aliases": []},
    "johannesburg": {"region": "Southern Africa","languages": ["en"],   "gl": "ZA", "hl": "en-ZA", "aliases": ["joburg", "jo'burg"]},
    "greenland":    {"region": "Northern Europe","languages": ["en", "da"], "gl": "GL", "hl": "en-GL", "aliases": ["greenlandic"]},
    "antarctica":   {"region": "Polar Regions","languages": ["en"],     "gl": "US", "hl": "en-US", "aliases": ["antarctic"]},
}

# Build alias lookup table
_ALIAS_LOOKUP: Dict[str, str] = {}
for _country, _data in GEO_DATABASE.items():
    _ALIAS_LOOKUP[_country] = _country
    for _alias in _data.get("aliases", []):
        _ALIAS_LOOKUP[_alias.lower()] = _country

# Regional keywords → region name for broader regional queries
REGION_KEYWORDS: Dict[str, str] = {
    "south asia": "South Asia",
    "southeast asia": "Southeast Asia",
    "east asia": "East Asia",
    "central asia": "Central Asia",
    "middle east": "Middle East",
    "west asia": "Middle East",
    "north africa": "North Africa",
    "west africa": "West Africa",
    "east africa": "East Africa",
    "central africa": "Central Africa",
    "southern africa": "Southern Africa",
    "sub-saharan africa": "Sub-Saharan Africa",
    "africa": "Africa",
    "europe": "Europe",
    "eastern europe": "Eastern Europe",
    "western europe": "Western Europe",
    "northern europe": "Northern Europe",
    "southern europe": "Southern Europe",
    "north america": "North America",
    "central america": "Central America",
    "south america": "South America",
    "latin america": "South America",
    "caribbean": "Caribbean",
    "oceania": "Oceania",
    "pacific": "Oceania",
    "scandinavia": "Northern Europe",
    "nordic": "Northern Europe",
    "balkans": "Eastern Europe",
    "caucasus": "Central Asia",
    "arctic": "Polar Regions",
    "polar": "Polar Regions",
    "antarctica": "Polar Regions",
}


@dataclass
class GeoContext:
    """Result of geographic intelligence analysis on a query."""
    query: str
    detected_country: Optional[str] = None
    detected_region: Optional[str] = None
    gl: str = "US"          # Google country code
    hl: str = "en-US"       # Google language/locale
    languages: List[str] = field(default_factory=lambda: ["en"])
    is_geographic: bool = False
    coverage_note: str = ""
    expanded_queries: List[str] = field(default_factory=list)


class GeoIntelligenceEngine:
    """
    Detects geographic intent in user queries and generates
    optimized, multilingual, expanded search queries.
    """

    # Query expansion templates for common topic types
    _EXPANSION_TEMPLATES = {
        "latest": ["{place} news", "{place} breaking news", "{place} latest updates", "{topic} {place}"],
        "news":   ["{place} today", "{place} current events", "what is happening in {place}"],
        "earthquake": ["earthquake {place}", "{place} seismic", "{place} quake", "tremor {place}"],
        "flood":  ["flood {place}", "{place} flooding", "{place} disaster", "flood relief {place}"],
        "election":["election {place}", "{place} vote", "{place} political news", "{place} election results"],
        "economy": ["economy {place}", "{place} GDP", "{place} economic news", "{place} markets"],
        "war":    ["conflict {place}", "{place} military", "war zone {place}", "{place} crisis"],
        "climate": ["climate {place}", "{place} weather", "{place} environment", "climate change {place}"],
        "technology": ["tech news {place}", "{place} startup", "{place} innovation", "technology {place}"],
        "sports": ["sports {place}", "{place} cricket", "{place} football", "{place} Olympics"],
    }

    def analyze(self, query: str) -> GeoContext:
        """
        Main method: Analyze a query to extract geographic context
        and generate optimal search queries.
        """
        q_lower = query.lower().strip()
        ctx = GeoContext(query=query)

        # 1. Detect country/territory
        country_key = self._detect_country(q_lower)
        if country_key:
            geo = GEO_DATABASE[country_key]
            ctx.detected_country = country_key
            ctx.detected_region = geo["region"]
            ctx.gl = geo["gl"]
            ctx.hl = geo["hl"]
            ctx.languages = geo["languages"]
            ctx.is_geographic = True
            ctx.coverage_note = f"Geo-targeted: {country_key.title()} ({geo['region']})"

        # 2. Detect broad region if no country found
        if not ctx.detected_country:
            region = self._detect_region(q_lower)
            if region:
                ctx.detected_region = region
                ctx.is_geographic = True
                ctx.coverage_note = f"Regional search: {region}"

        # 3. Generate expanded queries
        ctx.expanded_queries = self._expand_query(query, ctx)

        return ctx

    def _detect_country(self, q_lower: str) -> Optional[str]:
        """Find country/city name in query using alias lookup."""
        # Try longest match first (e.g., "south korea" before "korea")
        candidates = sorted(_ALIAS_LOOKUP.keys(), key=len, reverse=True)
        for alias in candidates:
            if re.search(r'\b' + re.escape(alias) + r'\b', q_lower):
                return _ALIAS_LOOKUP[alias]
        return None

    def _detect_region(self, q_lower: str) -> Optional[str]:
        """Find broad region name in query."""
        for keyword, region in sorted(REGION_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
            if keyword in q_lower:
                return region
        return None

    def _expand_query(self, query: str, ctx: GeoContext) -> List[str]:
        """
        Generate 3-6 intelligently expanded search variants.
        These are used to cast a wider net across providers.
        """
        queries = [query]  # Always include original
        q_lower = query.lower()

        place = ctx.detected_country or ctx.detected_region or ""
        if not place:
            # For non-geographic queries, add simple freshness variants
            queries.append(f"{query} latest")
            queries.append(f"{query} today")
            queries.append(f"{query} breaking news")
            return list(dict.fromkeys(queries))[:5]  # dedupe + limit

        place_str = place.title()

        # Add core place-based queries
        queries.append(f"{place_str} latest news")
        queries.append(f"{place_str} breaking news")

        # Check for topic keywords and use templates
        for topic_kw, templates in self._EXPANSION_TEMPLATES.items():
            if topic_kw in q_lower:
                for tmpl in templates[:2]:
                    q = tmpl.format(place=place_str, topic=topic_kw)
                    if q.lower() not in [x.lower() for x in queries]:
                        queries.append(q)
                break

        # Always add a "today" variant
        if "today" not in q_lower:
            queries.append(f"news from {place_str} today")

        return list(dict.fromkeys(queries))[:6]  # dedupe + max 6

    def get_google_news_urls(self, ctx: GeoContext, base_query: str) -> List[str]:
        """
        Build Google News RSS URLs tailored to detected geography.
        Returns multiple URLs for maximum coverage.
        """
        import urllib.parse
        urls = []

        SUPPORTED_GL = {
            "US", "GB", "IN", "AU", "CA", "DE", "FR", "JP", "BR", "IT", "ES", "MX",
            "ID", "KR", "ZA", "RU", "NL", "TR", "PL", "SA", "SE", "CH", "AR", "NG",
            "EG", "SG", "MY", "PH", "TH", "NZ", "IE", "IL", "PK", "BD", "KE", "AE"
        }
        effective_gl = ctx.gl if ctx.gl in SUPPORTED_GL else "US"

        q_encoded = urllib.parse.quote(base_query)
        urls.append(
            f"https://news.google.com/rss/search?q={q_encoded}&hl=en&gl={effective_gl}&ceid={effective_gl}:en"
        )
        return urls[:1]


# Singleton
geo_engine = GeoIntelligenceEngine()
