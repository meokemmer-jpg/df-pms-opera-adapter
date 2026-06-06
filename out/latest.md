# df-pms-opera-adapter — Output [CRUX-MK]
*Autonom aktiviert 2026-06-05T15:51:57.949979+00:00 | ollama-local/qwen2.5:14b-instruct*

# Dokumentation des df-pms-opera-adapter [CRUX-MK]

## Allgemeine Informationen

**Name:** df-pms-opera-adapter  
**Tier:** SKELETON-CONDITIONAL  
**Status:** Welle-36 Mosaic-Layer: Oracle Opera PMS Adapter (Premium Segmen
Segment, Chain Hotels)  
**Pflichtmodule:**
- `OperaConnector`
- `OperaAuth`
- `OperaAdapterOrchestrator`
- `AuditLogger`

## Architektur

### Modulebeschreibung

1. **OperaConnector**: Ein Wrapper für den OXI-API-Call (Oracle Xchange Int
Interface).
2. **OperaAuth**: OAuth2 Client-Credentials Flow zur Token-Service-URL.
3. **OperaAdapterOrchestrator**: LaunchAgent Entry Point und das Hauptprogr
Hauptprogramm.
4. **AuditLogger**: HMAC-SHA256 JSONL für Audit Zwecke.

## Opera-Spezifika

Oracle Opera verwendet ein Token Service Pattern, welches den OAuth2 Client
Client-Credentials Flow einschließt:

- **Token-Service-Pattern**:
  - OAuth2 Client-Credentials Flow zur Token-Service-URL.
  - Bearer-Token für OXI-API-Calls.
  - Hotel-ID per X-HotelId Header.
  - Token Refresh ~1h Lifetime.

## Umgebungsvariablen (ENV-Vars)

| Umgebungsvariable | Standardwert | Pflichtig bei Real | Beschreibung |
|-------------------|--------------|--------------------|-------------|
| `DF_PMS_OPERA_REAL_ENABLED` | false | nein | Aktiviert die Real API. |
| `OPERA_CLIENT_ID` | "" | ja bei Real | OAuth2 Client-ID. |
| `OPERA_CLIENT_SECRET` | "" | ja bei Real | OAuth2 Client-Secret. |
| `OPERA_TOKEN_URL` | "" | ja bei Real | Token-Service-Endpoint. |
| `OPERA_HOTEL_ID` | "" | ja bei Real | Property ID (OXI). |
| `DF_PMS_OPERA_PHRONESIS_TICKET` | "" | ja bei Real Booking | K17-PAV. |
| `DF_PMS_OPERA_HMAC_SECRET` | "" | nein | Audit-Secret. |

## Installation

Die Konfiguration und das Laden des LaunchAgents erfolgen wie folgt:

```bash
cp scripts/com.kemmer.df-pms-opera-adapter.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.kemmer.df-pms-opera-adapter.plist
~/Library/LaunchAgents/com.kemmer.df-pms-opera-adapter.plist
```

## Tests

Um die Funktionalität zu überprüfen, führen Sie folgenden Befehl aus:

```bash
python3 -m pytest tests/ -v
```

Diese Dokumentation dient als Leitfaden und Schnittstelle für die Arbeit mi
mit dem df-pms-opera-adapter. Sie deckt alle wichtigen Module, Umgebungsvar
Umgebungsvariablen sowie den Installationsprozess ab.