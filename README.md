# STEG – ren hovedversjon

Dette erstatter patch-kjeden. Behold denne mappen som eneste master.

Innhold:
- index.html / STEG.html: samme komplette nettside.
- data.json: normaliserte aktiviteter.
- server.py + START-LOKALT.cmd: lokal Garmin-synk.
- fetch_online.py + .github/workflows/pages.yml: GitHub Pages/Actions.

Funksjoner:
- Fungerende venstremeny med fire visninger.
- Alle/person-filter.
- Seks highlights. På Alle vises vinnernavn; på person vises egne tall uten navn. Korteste økt er fjernet.
- Tre sammenligningsgrafer med felles skala, uke/måned.
- Siste økt for alle tre.
- Søk i aktiviteter.
- Automatisk aktivitetsbaserte rekorder, ingen manuell registrering.
- EQ Timing-lenke/nettsøk.
- VO2 maks vises ikke automatisk fordi feltet ikke ble funnet i testede Garmin Personal API-svar.

Bilder (endelig mapping etter byttet): Halvor=4719, Tore=4675, Kjetil=5281.

Viktig:
- Rekorder er beste komplette aktiviteter nær distansen, ikke Garmin offisielle rekorder eller delsegmenter.
- Ikke legg Garmin-nøkler i HTML eller Git. Bruk .private lokalt og GitHub Secrets offentlig.
- GitHub Pages er offentlig. data.json og portretter blir offentlige.
- Tidligere delte API-nøkler bør roteres.
- Ingen offentlig side eller GitHub Secret opprettes av denne ZIP-filen alene.
