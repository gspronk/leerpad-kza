---
name: run
description: Start de KZA Leerpad Streamlit app lokaal
---

# Run — KZA Leerpad

Start de app vanuit de `kza_leerpad/` map:

```powershell
cd "C:\Users\GSpronk\OneDrive - KZA B.V\KZA\Leerpaden\kza_leerpad"
streamlit run app.py
```

De app draait op http://localhost:8501.

## Vereisten

- `.streamlit/secrets.toml` moet aanwezig zijn (zie CLAUDE.md voor vereiste keys)
- Wachtwoord staat in `secrets.toml` onder `PASSWORD`

## Stoppen

```powershell
netstat -ano | findstr ":8501"
Stop-Process -Id <PID> -Force
```

Of sluit het terminalvenster waarin de app draait.
