# Doppie citazioni da applicare (T11, seconda parte)

Elenco prodotto il 21/10/2026 sulle righe di develop @ 0f8ba21. **Le righe sono cambiate con i temi T1-T8 e T13: ricercare i frammenti con `git grep`, non usare i numeri di riga.** Applicare solo le corrispondenze confermate in `mappa-nuovo-tuir.md`. Molte sono già state inserite dai temi T1, T3, T13 (controllare prima).

Due correzioni da fare in ogni caso:
- `aliquote-12-5-26.md`: il 48,08% va attribuito all'art. 3 c. 5 DL 66/2014 e all'art. 5 c. 2 / art. 6 c. 1 D.Lgs. 461/1997 (dal 2027 artt. 304 c. 1, 306 c. 1, 307 c. 4 D.Lgs. 117/2026), non all'art. 68 c. 6 TUIR (T1 dovrebbe averlo già corretto).
- `it-tax-optimization/SKILL.md`: «art. 59 dell'All. 1 al D.Lgs. 33/2025» → «art. 59 del testo unico versamenti e riscossione (D.Lgs. 33/2025)»: l'allegato non ha numero.
- `criptovalute-casi-speciali.md`: «art. 6 c. 6 D.Lgs. 461/1997» → + «dal 2027 art. 306 c. 7 D.Lgs. 117/2026».

Per file (frammento → aggiunta):
- **it-tax-optimization/SKILL.md**: art. 67 lett. c-bis, c-ter → dal 2027 art. 76 c. 1 lett. e, f; art. 44 → art. 46; c-sexies → art. 76 c. 1 lett. i; art. 110 → art. 119 c. 5.
- **criptovalute.md**: c-sexies → art. 76 c. 1 lett. i; art. 44 → 46; art. 67 c-bis…c-quinquies → art. 76 lett. e…h; art. 68 c. 9-bis → art. 77 c. 11; art. 6 c. 1-bis D.Lgs. 461/97 → art. 306 c. 2.
- **criptovalute-avanzate.md**: art. 67 c-sexies + art. 68 c. 9-bis → art. 76 c. 1 lett. i e art. 77 c. 11; «il testo unico sanzioni» → «art. 14 del testo unico sanzioni»; art. 5 c. 2 DL 167/1990 → art. 67 c. 2 D.Lgs. 173/2024; art. 5 D.Lgs. 74/2000 → art. 77 D.Lgs. 173/2024; art. 4 → art. 76.
- **criptovalute-casi-speciali.md**: art. 68 c. 9-bis → art. 77 c. 11; c-sexies → art. 76 c. 1 lett. i; art. 110 → c. 3-bis, art. 119 c. 5; art. 24-bis → art. 246; L. 232/2016 c. 158 → art. 88 D.Lgs. 123/2025 (il c. 153 resta); art. 7 D.Lgs. 346/1990 → art. 93 D.Lgs. 123/2025; art. 57 → art. 134; aggiornare anche il marcatore finale.
- **etf-trap-redditi-capitale.md**: c-ter → art. 76 c. 1 lett. f; art. 44 lett. g → art. 46 c. 1 lett. h; art. 10-ter → art. 59 D.Lgs. 33/2025; artt. 44-45 e 68 c. 7 → artt. 46-47 e 77 c. 8.
- **regime-dichiarativo.md**: art. 4 DL 167/1990 → art. 58 D.Lgs. 141/2026; sanzioni → art. 67 D.Lgs. 173/2024; IVAFE → art. 168 D.Lgs. 123/2025.
- **it-pianificazione/SKILL.md**: art. 16-ter c. 5-bis → art. 18 c. 6; c. 3-bis → art. 13 c. 4; tassazione 15%→9% → art. 258 c. 1 (RITA) / c. 4 (prestazioni); art. 11 c. 6 D.Lgs. 252/2005 → art. 258 c. 4.
- **netto-pensione.py**: art. 11 c. 6 → art. 258 c. 4; art. 13 c. 3 e c. 1 (stesso numero).
- **ponte-pensione.py**: tassazione RITA → art. 258 c. 1.
- **previdenza-obbligatoria.md**: art. 13 c. 3 (stesso numero), c. 3-bis → art. 13 c. 4.
- **it-pianificazione-autonomi**: art. 10 lett. e-bis → lett. h; art. 10 lett. e → lett. f; L. 190/2014 c. 54-89 → artt. 232-243 (c. 64 → art. 235 c. 1); art. 11 c. 6 D.Lgs. 252/2005 → art. 258 c. 4.
- **asset-location.md**: art. 12 lett. c D.Lgs. 346/1990 → art. 97 lett. c D.Lgs. 123/2025.
- **it-rebalance/SKILL.md**: artt. 42 ss. → artt. 42-50 (491→42, 492→43, 493→44, 494→45).
- **genera-ips.py** (commento sopra POLICY_FISCALITA): art. 44 c. 1 lett. g → art. 46 c. 1 lett. h; art. 17 D.Lgs. 252/2005 e L. 190/2014 c. 622 → art. 257 c. 1 e 10; art. 68 c. 5 → art. 77 c. 6.

Utile anche: un test di igiene che, nei file normativi, ogni citazione di una norma abrogata dal 1/1/2027 nomini anche il successore (T1 ha già `t_t1_doppie_citazioni` per il D.Lgs. 461 e l'art. 10-ter: estenderlo).
