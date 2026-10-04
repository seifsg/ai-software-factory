---
name: how-to-make-a-pr
description: "Create, update, or correct a factory-managed pull request. Prepare a visual, self-contained draft with task links, human handoff and remote/cloud PR review."
---

# Pull Request erstellen

Vor dem Start: [Projekt-Bindings](references/project-bindings.md) und [PR-Adapter](../../../docs/pr-workflow.md) lesen. Tatsächliches Repo, Branches, Regeln, Tools und Berechtigungen ermitteln. Keine fremden Konten, Dienste oder Projektannahmen übernehmen. PR-Review ausschließlich durch separaten Remote-/Cloud-Agenten mit frischem Kontext und exakt geprüftem Remote-Stand; lokale Subagenten ersetzen sie nicht.

Alle Tests erst nach fertiger Implementierung: zuerst manuelle/User-QA, danach automatisierte Tests. Keine frühen Playtests, manuellen Reproduktionen oder Walkthroughs; Quelltextprüfung und vorhandene Logs bleiben erlaubt.

Ziel: kleine, nachvollziehbare Änderungen, sauber beschrieben, als **Draft-PR zur menschlichen Prüfung**.

> **Grundhaltung:** Ein PR ist ein **Vorschlag zur Review**, kein Selbstzweck. Als **Draft** öffnen; ein Mensch prüft, verfeinert und merged oder verwirft. Explizite Nutzerfreigaben gelten weiter. Aus diesem Skill entsteht keine Merge-, Release- oder Benachrichtigungsfreigabe.

## Wann diesen Skill nutzen

Bei jedem autorisierten Code-, Dokumentations- oder Skill-PR: neu anlegen, aktualisieren oder nachträglich korrigieren. Bei reiner Analyse/Review keine späteren Schreibschritte vorziehen.

## 1. Wann öffnen & vom richtigen Basis-Branch abzweigen

Vor Änderungen [Vorher/Nachher-Belege](../../../docs/pr-workflow.md#beforeafter-proof) sichern: bei UI ein gezieltes Screenshot-Paar; sonst vergleichbare Ergebnisse. Nachher-Beleg und optionale Journey-Aufnahme erst in finaler manueller QA. Belege im PR zugänglich einbetten/verlinken; fehlende Belege offen nennen.

- Änderungen über einen eigenen Feature-Branch und PR; nicht direkt auf den Basis-Branch committen.
- Ziel anhand tatsächlicher Branch-/Release-Policy bestimmen. Vorhandenen Integrations-/Dev-Branch standardmäßig nutzen; ohne solchen Branch den bestätigten Default-Branch. Abweichungen im PR nennen.
- **Remote prüfen**, nicht die lokale Branch-Liste:
  ```bash
  git ls-remote --heads origin
  git ls-remote --symref origin HEAD
  ```
  Ein flacher/Single-Branch-Klon kann reale Remote-Branches lokal verbergen. `git branch -r` beweist ihre Abwesenheit nicht.
- Aktuellen Basisstand holen. Bestehende Arbeit schützen; neuen, unbenutzten Branch oder isolierten Checkout verwenden:
  ```bash
  git fetch origin
  git switch -c <neuer-branch> origin/<basis-branch>
  ```

### Hotfix-Workflow

> **HOTFIX nur auf ausdrücklichen Wunsch.** Bei getrennten Production- und Integrations-Branches ist ein Hotfix **immer ein PAAR**: Production-PR plus Begleit-PR mit **derselben Änderung** in den Integrations-Branch. Beide synchron halten.

- Prod-Branch vom aktuellen Production-Stand abzweigen.
- Companion von der aktuellen Integrations-Basis abzweigen; **nur die Fix-Commits** übernehmen:
  ```bash
  git switch -c hotfix/<slug>-integration origin/<integration-branch>
  git cherry-pick -x <fix-sha>
  ```
- **Keinen** zweiten PR vom Prod-Branch gegen Integration öffnen: das könnte fremde prod-only Commits einschleppen.
- Beide PRs gegenseitig verlinken; jedes Follow-up in beide spiegeln.
- Bei nur einem Release-Zweig kein künstliches Branch-Paar erfinden. Tatsächliche Release-Policy dokumentieren.

## 2. Branch-Namen & Commit-Nachrichten

**Branch:** `<scope>/<kurz-beschreibend>`, etwa `fix/save-state`, `feat/search`, `docs/review-method`.
Scopes: `fix`, `feat`, `docs`, `chore`; tatsächliche Projektkonvention beachten.

**Conventional Commit:**

```
<typ>(<scope>): <imperativer Betreff>

<Warum die Änderung nötig ist>
```

Betreff knapp und imperativ. Optionaler Body erklärt **warum**, nicht die einzelnen Codezeilen.

## 3. Fokussierte, minimale Änderungen — und vor dem Push prüfen

- **Genau eine Sache** pro PR. Unabhängige Funde als Follow-up festhalten.
- Nur eigene geänderte Dateien stagen: `git add <datei>`. Nie blind `git add .` / `git add -A`.
- Reale Prüfungen aus Regeln, Manifesten und CI ermitteln: Build/Compile, Typen, Lint, Tests, Abhängigkeiten und relevante Plattform-/Laufzeitchecks.
- Erst Implementierung und sinnvolle Verbesserungen abschließen, dann das echte Verhalten durch manuelle Aktionen prüfen. Erst danach, ganz am Ende vor dem PR: notwendige Tests schreiben/anpassen, sauber ausarbeiten und ausführen. Während der Entwicklung keine Tests schreiben, ändern oder starten. Bei Produktionsfehlern: chirurgisch korrigieren, manuell nachprüfen, dann finale Tests wiederholen. Siehe [Reihenfolge](../../../docs/current-decisions.md#finish-work-use-it-then-automate-tests). Keine Tests, die nur die Implementierung nacherzählen.
- Vor dem Push erforderliche Gates grün. Fehlende Prüfung ist **unverifiziert**, kein PASS. Bei Small Change gelten ausgewählte fokussierte Checks und echte geschützte Gates; keine künstliche Volltestpflicht.

## 4. Task zuerst — dedupen, verlinken, Status setzen

> **PFLICHT:** Jeder PR gehört zu einem Task im tatsächlich ausgewählten Tracker. Task **vor** dem Draft anlegen oder wiederverwenden. Kein Task-System erfinden.
>
> **Enge Ausnahme:** Nur wenn das Projekt eine Routine-/Skill-Ausnahme festgelegt hat und der **gesamte Diff** in deren erlaubten Pfaden liegt, entfällt der Task. Nicht pauschal für Dokumentation oder Nicht-Code.

- **ERST SUCHEN:** nach Symptomen/Feature/Bereich/Dateien **und** nach PR-Titel/Branch-Slug. Gleiche Arbeit gefunden → bestehenden Task nutzen. Sonst autorisiert anlegen.
- **Beide Richtungen:** PR-URL in den Task, klickbarer Task-Link in den sichtbaren PR-Kontext.
- Bei PR-Eröffnung den ausgewählten **awaiting-review / development-done**-Status setzen. Erlaubte Statuswerte vorher abfragen; genaue Schreibweise verwenden, nicht raten.
- Benötigte Tracker-Mechanik aus vorhandenen Projektregeln und autorisierten Tools lesen. Fehlende Bindings/Zugriffe als offenen abhängigen Schritt melden; lokale Arbeit fortsetzen.
- Task-Befreiung prüfen und begründen; nur dann Suche, Anlage, Verlinkung und Statuswechsel überspringen.

## 5. PR als DRAFT öffnen — mit guter Beschreibung

**Immer als Draft öffnen.** Der Reviewer muss Wirkung und Grund ohne Code-Lesen verstehen.

> **PFLICHT — Why zuerst.** Nach einem erforderlichen Header/Attribution-Block folgt **Why / Warum**: ursprüngliches Problem, Kontext und Entscheidung. Vorhandene Diskussion lesen; wesentliche Lücken klären. Ist der Grund nicht verfügbar, die Lücke benennen statt erfinden.

- **Vorher / Nachher:** sichtbare Verhaltensänderung in einfacher Sprache.
- **Wie:** kurze technische Erklärung.
- **Kontext-Links:** Issue/Task und alle relevanten auslösenden Diskussionen sichtbar verlinken, nicht im versteckten Kommentar.

> **PFLICHT — selbsttragender Kontext.** Ein Mensch oder Agent muss den Fall **kalt weiterführen** können, ohne die Quelldiskussion zu öffnen:
> - ursprüngliche Anfrage und **warum**;
> - Entscheidungen samt Begründung;
> - relevante Fakten: IDs, Pfade, Bereiche, Repos, klickbarer Task-Link oder bestätigte Ausnahme;
> - aktueller Stand;
> - verbleibende Schritte und Blocker.
>
> Quellenlinks bleiben als Audit-Spur. Sie ersetzen diesen Kontext **nicht**.

**Beobachtung belegen:** Relevante autorisiert teilbare Logs, Traces, Replays, Screenshots oder Messungen verlinken. Tatsächliche Quelle und Grenzen nennen. Keine fremden Session-IDs kopieren, keine privaten Daten/Secrets veröffentlichen; fehlende Beobachtung offen benennen.

**Attribution:** Auftraggeber, Entscheidungsträger und tatsächlichen menschlichen Autor der Substanz wahrheitsgemäß nennen. Autorenbeitrag ausdrücklich würdigen, **zusätzlich** zu Requested-by; Originalarbeit von Portierung/Anpassung unterscheiden. Bestehende Attribution-Struktur erhalten. Keine erfundene Autorenschaft, Testleistung oder AI-/Tool-Trailer. Tatsächliche Projektvorgaben beachten.

> **PFLICHT — Anpassungs-Historie.** Bei verlangten Änderungen im PR-Body fortlaufend **WAS**, **WARUM**, **WER** und **was getan wurde** festhalten. Ganze Geschichte über die Lebenszeit des PR erhalten.

### PR-Beschreibungsstil — visuell zuerst

Drei Ziele, in dieser Reihenfolge:

1. **So detailliert wie möglich — nichts auslassen:** jeden relevanten Aspekt abdecken — Verhalten, Entscheidungen, Dateien, Guards, Telemetrie, Verifikation und Lücken.
2. **Visuell zuerst:** ASCII-Diagramme und Tabellen vor Prosa. Struktur trägt die Information.
3. **So wenige Wörter wie möglich:** Prosa als letztes Mittel; maximal eine Zeile, wo Tabelle/Diagramm nicht passen.

| Inhalt | Form |
|---|---|
| Varianten über mehrere Dimensionen vergleichen | Tabelle/Matrix; Änderungen markieren |
| Zustände, Datenfluss, Vorher/Nachher, Verzweigungen | ASCII-Diagramm |
| Dateien, Checks, Events | ausgerichteter Monospace-Block |
| Einzelner Fakt | ein Satz; Schlüsselbegriff fett |

**Standard-Reihenfolge:** Erst tatsächliches PR-Template erfüllen. Unzutreffende Abschnitte weglassen, relevante Details erhalten.

```
<erforderlicher Header / wahrheitsgemäße Attribution>
## Why / Warum                 Kontext + Entscheidung
### What & why                 Before/After
### Flow                       Zustände / Verzweigungen
### Design                     Optionen + Begründung
### Files                      NEW/M/D + Pfad + Zweck
### Guards / Fixes             Severity → Problem → Status
### Observability              relevante Events + sichere Payload-Felder
### Verification               tatsächlicher Befehl → Ergebnis
### Not covered / follow-ups   Lücken, Grenzen, nächste Schritte
### Adjustment History         WAS / WARUM / WER / Ergebnis
### Kontext                    selbsttragender Stand + sichtbare Quellen/Task-Links
```

**Bausteine:**

```
BEFORE                         AFTER
──────────────────────────     ──────────────────────────
<alter Zustand>                 <neuer Zustand>
<Fehlerfall>                    <Erfolgsfall>

<Auslöser> ─▶ <Schritt> ─┬─▶ <Ergebnis A>
                        └─▶ <Ergebnis B / Eskalation>

                  <Dimension 1>  <Dimension 2>
<Option A>        <Wert>          <Wert>  ◀── NEW
<Option B>        <Wert>          <Wert>

NEW <pfad>       <Zweck>
 M  <pfad>       <Änderung>
 D  <pfad>       <Entfernungsgrund>

<Prüfbefehl>     <tatsächliches Ergebnis>
```

**Keine Füll-Sätze.** Fett nur für Schlüsselbegriffe. Monospace-Diagramme in Codeblöcke setzen.
Behauptete Ergebnisse nie aus einer Vorlage übernehmen.

Beschreibung in Datei schreiben; Shell-Escaping vermeiden:

```bash
git push -u origin <branch-name>
gh pr create --draft --base <basis-branch> --head <branch-name> \
  --title "<typ>(<scope>): <betreff>" --body-file <beschreibung-datei>
```

**Basis nochmals prüfen.** Beim Hotfix-Paar beide PRs öffnen, verlinken und synchron halten.

### Review-Owner sofort beim Draft anfragen

- Tatsächlichen Owner aus Projektregeln/Ownership ermitteln. Unterstützte, autorisierte Review-Anfrage beim Draft stellen; nicht erst bei „ready“.
- Benachrichtigung nur an den **ausgewählten und autorisierten** Empfänger/Kanal. Bei freigegebenem Workflow den Ursprungsthread zusätzlich aktualisieren.
- Private Ziele können in öffentlicher Suche fehlen. Vorhandene verifizierte ID nutzen; Zugriffsbeschränkungen nicht umgehen. Fehlende Zustellung als offen melden.
- Erinnerungen nur bei tatsächlicher Beauftragung: Dringlichkeit, Frequenz, Stop bei Reaktion/Merge/Schließen und Backoff festlegen. Keine automatische neue Dauererlaubnis.

### Automatisches Self-Review nach dem Draft — separate Cloud-Instanz

Sobald der Draft vollständig vorbereitet ist: [How to Review a PR](../how-to-review-a-pr/SKILL.md) auf einer **separaten Remote-/Cloud-Instanz mit frischem Kontext** ausführen. Tatsächliche Ausführung, Task-ID, Base/Head und Ergebnis festhalten. Lokale Controller-Review bleibt separat; fehlender Cloud-Zugriff ist eine offene Review, kein lokaler Ersatz.

- Tatsächliche Kette lesen: Claim → Analyse ohne Code → vier Themen → Synthese/Compliance → Fragen → autorisierte Fixes → manuelle QA → finale Tests/Projektchecks → autorisierter Push/Kommentar.
- Für Small Change gilt der ausgewählte fokussierte Modus aus dem [PR-Adapter](../../../docs/pr-workflow.md#small-direct-changes).
- Repariert der Reviewer Code, braucht der neue Stand eine **frische unabhängige Bewertung**.
- Keine erfundenen Retry-Limits; sinnvolle autorisierte Korrekturen fortsetzen. Echte Zugriffsgrenzen und Owner-Stops beachten.
- **PR bleibt Draft.** Review ersetzt keine Merge-/Release-Freigabe. Fehlende unabhängige Review offen melden.

### Falschen Basis-Branch korrigieren

- Head basiert bereits auf dem richtigen Stand → PR-Base autorisiert korrigieren: `gh pr edit <nr> --base <basis>`.
- Basen divergieren → frischen Branch von richtiger Basis anlegen, nur relevante Commits cherry-picken, Ersatz-PR erstellen; alten PR nach entsprechender Freigabe als superseded schließen.
- **Kein Force-Push.** Fremde Historie und unrelated Änderungen erhalten.

## 6. PR-Template beachten

Vor dem Schreiben `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE/` oder Host-Äquivalent prüfen.
Vorhandene Struktur ausfüllen; Why, Vorher/Nachher, Kontext und Nachweise darin unterbringen.

## 7. Signaturen & frische Branches

- Verlangte Commit-Signaturen mit vorhandener autorisierter Identität erfüllen. Keine Identität erfinden.
- Keine internen Tool-/AI-Identifier in Commit- oder PR-Text; tatsächliche Attribution-Regeln beachten.
- Nach Merge neue Arbeit auf **frischem Branch vom aktuellen richtigen Basisstand** beginnen.
- Signierung, Berechtigungen und geschützte Gates nicht umgehen.

## Checkliste

- [ ] Richtige Remote-Basis geprüft; aktueller Stand; fremde/dirty Arbeit geschützt.
- [ ] Eigener sinnvoll benannter Branch; fokussierter Diff; nur eigene Dateien gestaged.
- [ ] Relevante Checks grün; fehlende Nachweise benannt; echte geschützte Gates erfüllt.
- [ ] Conventional Commit; erforderliche Signatur; wahrheitsgemäße Attribution.
- [ ] Tracker auf beiden Suchachsen dedupliziert; Task vor Draft; beidseitige Links; genauer Review-Status. Oder bestätigte enge Routine-Ausnahme.
- [ ] Projekt-Template verwendet; Draft auf richtiger Basis. Hotfix-Paar vollständig, verlinkt, synchron.
- [ ] Tatsächlicher Review-Owner angefragt; autorisierte Benachrichtigung zugestellt oder offen gemeldet. Keine unbestellte Erinnerung.
- [ ] Separate Review ausgeführt; unabhängige Bewertung nach Review-Reparaturen; PR bleibt Draft.
- [ ] Why zuerst; Vorher/Nachher/Wie; visuelle Darstellung; alle relevanten Details.
- [ ] Selbsttragender Kontext: Anfrage, Entscheidungen, Fakten/Links, Stand, offene Schritte.
- [ ] Auftraggeber und tatsächlichen Autor zusätzlich zu Requested-by gewürdigt; Original/Anpassung unterschieden; Anpassungs-Historie und sichere Beobachtungsnachweise erhalten.
- [ ] Keine erfundenen Ergebnisse, AI-Trailer, fremden Konten oder stillen Merge-/Release-Aktionen.
