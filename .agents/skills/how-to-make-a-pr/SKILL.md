---
name: how-to-make-a-pr
description: "Create, update, or retrospectively correct every factory-managed pull request, in any project. Requires a visual self-contained draft, the project's task and reviewer handoff, and automatic separate-instance how-to-review-a-pr execution."
---

# Pull Request erstellen (RepairCheck-Workflow)

**Project adapter:** Before using this original, read [project bindings](references/project-bindings.md). Its RepairCheck people, accounts, services, branches and host examples belong to the source project; use the target project's authorized bindings and available tools.

Dieser Skill beschreibt, wie in den RepairCheck-Repos ein **Pull Request** angelegt wird. Ziel: kleine, nachvollziehbare Änderungen, sauber beschrieben, als **Draft-PR zur menschlichen Prüfung** — kein automatischer Merge.

> **Grundhaltung:** Ein PR ist ein **Vorschlag zur Review**, kein Selbstzweck. Er wird immer als **Draft** geöffnet; ein Mensch prüft, verfeinert und merged oder verwirft.

## Wann diesen Skill nutzen

Immer wenn eine Code- oder Doku-Änderung in einem RepairCheck-Repo (`repaircheck_platform`, `claude-routines`, `repaircheck.de`, `unfallbericht-app` usw.) über einen Pull Request eingereicht werden soll — sei es durch einen Menschen oder proaktiv durch einen Agenten.

## 1. Wann öffnen & vom richtigen Basis-Branch abzweigen

- Änderungen werden **nie direkt** auf den Basis-Branch committet, sondern immer über einen eigenen Feature-Branch und PR.

> **PR-TARGET-POLICY (Standing-Policy, harte Default-Regel).**
> 1. **DEFAULT — immer gegen den DEV-Branch:** Jeder Draft-PR zielt standardmäßig auf den **Dev-Branch** des Repos (`dev` / `develop` / `development` — wie das jeweilige Repo ihn nennt), **NIEMALS** direkt auf `main` / `master` / Production. Das ist der Default — **keine Rückfrage nötig**.
> 2. **HOTFIX-AUSNAHME (nur auf ausdrücklichen Wunsch):** Nur wenn der Nutzer **ausdrücklich** einen **Hotfix** verlangt, darf ein PR gegen den Production-/`main`-Branch zielen — und dann ist **zusätzlich ein Begleit-PR (Companion-PR) mit DERSELBEN Änderung in den Dev-Branch PFLICHT**, damit Dev synchron bleibt. Ein Hotfix ist **immer das PAAR** (Prod-PR + Dev-PR), **nie ein einzelner PR**.
> 3. **SYNCHRON HALTEN:** Bekommt ein PR des Hotfix-Paars ein Follow-up-Update, wird dasselbe Update **in den anderen PR gespiegelt**, damit beide immer dieselbe Änderung tragen.

- **Dev-Branch des Repos ermitteln** (das Default-Ziel, siehe Policy oben) — **immer am Remote, nie am lokalen Klon**:
  ```bash
  git ls-remote --heads origin                # AUTORITATIV: fragt den Server, listet ALLE Branches
  # dev / develop / development in der Ausgabe suchen
  ```
  > **WARNUNG — `git branch -r` NICHT zur Existenzprüfung verwenden.** Ein flacher bzw. Single-Branch-Klon (`git clone --depth 1`, wie ihn Agenten-Sessions standardmäßig anlegen) kennt lokal **nur** den Default-Branch. `git branch -r` zeigt dann **ausschließlich `origin/main`** und verschweigt einen real existierenden `dev`-Branch — genau die Falle, die zu einem fälschlich gegen `main` geöffneten PR führt. Immer `git ls-remote --heads origin` nehmen; das ist unabhängig von der Klon-Tiefe.

  Hat das Repo **keinen** Dev-Branch, gegen den **Default-Branch** (meist `main`) zielen (per `git ls-remote` bestätigt) — und das im PR **vermerken**.
- Immer vom **aktuellen** Stand des Basis-Branches abzweigen:
  ```bash
  git fetch origin
  git checkout -B <branch-name> origin/<basis-branch>
  ```

### Branch-Topologie (`Repaircheck/repaircheck_platform`)

- `main` = **Production / Live-Branch** (zugleich der GitHub-Default). Release-PRs tragen den Titel „dev → main"; Production shipped aus `main`.
- `dev` = **Development-/Integrations-Branch**. Die alltäglichen Feature-PRs zielen auf `dev`.
- `main` und `dev` **divergieren**: Hotfixes, die direkt nach `main` gemergt werden (prod-only), sind **nicht automatisch** auf `dev` — genau das ist die Quelle „zukünftiger Branch-Konflikte". Deshalb existiert das Hotfix-Paar.
- Es gibt **keinen** `master`/`production`/`prod`/`staging`-Branch — `main` **ist** Production.

### Branch-Topologie (`Repaircheck/repaircheck_mobile`)

- `main` = **Production / Release-Branch** (GitHub-Default).
- `dev` = **Integrations-/Development-Branch** — die alltäglichen Feature-PRs zielen hierauf.
- Gleiche Regel wie überall: Nicht-Hotfix-PRs → `dev`; nur ausdrücklich verlangte Hotfixes → `main` (dann als Prod+Dev-Paar).

### Hotfix-Workflow (die Mechanik)

- Ein Hotfix ist **immer ein PAAR**, nie ein einzelner PR: ein PR in `main` (Prod) **UND** ein Begleit-PR in `dev` (restated die PR-Target-Policy oben — hier nur die Mechanik dazu).
- **Prod-PR:** Branch von `main` abzweigen, Base `main`. Namens-Präzedenz: `hotfix/<slug>-prod`. Titel `hotfix(<area>): <was>` bzw. `hotfix(prod/main): <was>`.
- **Dev-Companion:** **keinen** zweiten PR vom selben Prod-Branch nach `dev` öffnen — das zieht **alle** prod-only-Commits mit, die `dev` fehlen, und erzeugt einen riesigen, falschen Diff. Stattdessen einen **neuen Branch von `dev`** ziehen und **nur die Fix-Commit(s)** cherry-picken:
  ```bash
  git checkout -B hotfix/<slug>-dev origin/dev
  git cherry-pick -x <fix-sha>
  ```
  Base `dev`. Titel `hotfix(dev): <was>`.
- Beide PRs im Body **gegenseitig verlinken** („Hotfix pair: prod #NNN ↔ dev #MMM") und jede spätere Änderung an einem PR im anderen **spiegeln**.
- Reale Präzedenz-Paare als Referenz: **#828 (main) ↔ #829 (dev)** und **#843 (main) ↔ #841 (dev)**.

## 2. Branch-Namen & Commit-Nachrichten

**Branch-Namen** folgen dem Schema `<scope>/<kurz-beschreibend>` mit denselben Scopes wie die Commits:

- `fix/…` — Bugfix
- `feat/…` — neues Feature
- `docs/…` — Doku/Skills
- `chore/…` — Aufräumen, Tooling, Abhängigkeiten

Beispiele: `fix/opponent-license-plate-parsing`, `feat/superchat-reply-storno-hinweis`, `docs/skill-how-to-make-a-pr`.

**Commit-Nachrichten** folgen **Conventional Commits**:

```
<typ>(<scope>): <imperativer Betreff>

<Body: erklärt das WARUM, nicht das WAS>
```

- Betreff **imperativ** und knapp (z. B. „add", „fix", nicht „added"/„fixes").
- Body optional, aber empfohlen: **warum** die Änderung nötig ist, nicht was die Zeilen tun.
- Beispiel: `docs(skills): add how-to-make-a-pr skill`.

## 3. Fokussierte, minimale Änderungen — und vor dem Push prüfen

- **Genau eine Sache** pro PR. Keine unzusammenhängenden Änderungen mitschleifen — Gefundenes lieber als Follow-up notieren.
- Nur die tatsächlich geänderten Dateien stagen (`git add <datei>`), **nie** `git add .` / `git add -A`.
- **Vor dem Push** lokal prüfen — je nach Repo z. B.:
  ```bash
  npm test          # Tests
  npm run typecheck # bzw. tsc --noEmit
  npm run build     # Build muss durchlaufen
  npm run lint
  ```
- Bei Verhaltensänderungen: **Tests ergänzen** oder anpassen. Nichts pushen, was lokal nicht grün ist.

## 4. ClickUp-Task ist PFLICHT — erst dedupen, dann anlegen (vor dem Draft), bei PR-Eröffnung auf „Development done" (Ausnahme: Skill-PRs)

> **PFLICHT (Standing-Direktive von Michael Emaschow, 2026-08-03).** Zu **jedem** PR gehört ein **ClickUp-Task** — das Anlegen ist **nicht optional** und passiert **BEVOR** der Draft-PR geöffnet wird. **Kein PR ohne Task.** Bisher galt diese Pflicht nur für Bugfixes (TASK-FIRST-Prinzip in `bug-investigation`); sie gilt für **jeden** PR — **mit einer Ausnahme:**
>
> **AUSNAHME — Skill-PRs brauchen keinen ClickUp-Task (Entscheidung von Michael Emaschow, 2026-08-03).** Ändert ein PR **ausschließlich** Skills/Routinen in **diesem** Repo (`claude-routines` — also `.claude/skills/**`, `CLAUDE.md` und vergleichbare Routine-Dateien), entfällt der Task **vollständig**: kein Anlegen, keine Dedup-Suche, keine gegenseitige Verlinkung. Berührt der PR **auch nur eine** Datei außerhalb dieser Routinen (Code in `repaircheck_platform`, `repaircheck_mobile`, `unfallbericht-app` o. Ä.), gilt die Pflicht **wieder vollständig**. Die Ausnahme ist **eng auf Skill-PRs begrenzt** — sie deckt **nicht** allgemein „Doku-PRs" oder „Nicht-Code-PRs" ab.

- **ERST SUCHEN, dann anlegen (Dedup-Pflicht).** Vor dem Anlegen in ClickUp nach einem Task suchen, der **dieselbe Arbeit** abdeckt — auf **beiden** Suchachsen: nach **Stichworten der Änderung** (Symptom, Endpoint, Feature-/Bereichs-/Dateiname) **und** nach **PR-Titel bzw. Branch-Name** (der Slug `fix/…`/`feat/…` trägt meist genau die Stichworte). **Treffer → den bestehenden Task wiederverwenden und verlinken, KEIN Duplikat anlegen.** Nur **ohne** Treffer einen neuen Task anlegen.
- **Gegenseitig verlinken — beide Richtungen, Pflicht:** die **PR-URL in den Task** (`PR`-Feld) **und** den **Task als klickbaren Link in den PR-Body** („Kontext"-Abschnitt, siehe die Selbsttragender-Kontext-PFLICHT in Abschnitt 5). So ist der Zusammenhang von jeder Seite auffindbar.
- **Task-Status bei PR-Eröffnung → „Development done" (PFLICHT).** Sobald der (Draft-)PR eröffnet ist, wird der verknüpfte Task auf den Status **„Development done"** gesetzt — im selben Arbeitsschritt wie die Verlinkung, nicht später. **Ein PR, dessen Task noch in `backlog` steht** — oder in einem anderen Vor-Entwicklungs-Status (`to do`, `on hold`) —, **ist unvollständig:** der PR ist der Beweis, dass die Entwicklung fertig ist, also muss das Board das auch zeigen.
  - **Exakte Schreibweise vorher abfragen, nicht raten:** die erlaubten Statuswerte der jeweiligen Liste per `GET /list/{list_id}` holen und den Wert **case-sensitive genau so** senden (Mechanik → `clickup-task`) — Listen können abweichende Namen/Schreibweisen tragen.
  - Gilt für **Code-PRs**. Bei **Skill-PRs** existiert kein Task (Ausnahme oben) → **kein Statuswechsel**.
- **Details stehen woanders — hier NICHT duplizieren:**

| Frage | Zuständige Skill |
|---|---|
| Mechanik: Endpunkte, Auth, Ziel-Liste, Suche, Anlegen, Status setzen, Kommentar, `PR`-Feld | **`clickup-task`** |
| Inhalt & Konventionen: Titel, Modus, Beschreibungs-Vorlage, Priorität/Tags, Assignee, Dedup-Regel (REGEL 4) | **`how-to-write-a-clickup-task`** |
| Status-Lifecycle **vor** dem PR (`to do` → `in progress`) und der **Abschluss-Kommentar** danach | **`bug-investigation`** (TASK-FIRST-Prinzip) |

- Reale Präzedenz als Referenz: Task **`869ed4296`** ↔ **`repaircheck_platform#953`** — PR-URL im `PR`-Feld des Tasks, Task-Link im PR-Body.

## 5. PR als DRAFT öffnen — mit guter Beschreibung

PRs werden **immer als Draft** geöffnet (`--draft`). Die Beschreibung ist in **Klartext** verfasst, sodass ein Reviewer den Effekt ohne Code-Lesen versteht:

> **PFLICHT — „Why" / „Warum" zuerst.** Jede PR-Beschreibung **beginnt** — direkt nach einem etwaigen Pflicht-Header bzw. der Attribution — mit einem **„Why" / „Warum"**-Abschnitt (`## Why`), der den **Kontext** festhält: **warum** die Änderung nötig ist und **welche Entscheidung** dahintersteht. Diesen Kontext aus der auslösenden Diskussion ziehen (meist dem Slack-Thread); bei einer Wissenslücke **vor dem Finalisieren** den ursprünglichen Autor fragen. Nur weglassen, wenn wirklich **keine** solche Information verfügbar ist.

- **Vorher / Nachher (Before/After):** in einfacher Sprache, was ein Nutzer oder Reviewer verändert sieht.
- **Wie (How):** ein kurzer Absatz zur technischen Umsetzung.
- **Verweis** auf zugehöriges Issue bzw. den auslösenden Thread (z. B. `Closes #123` oder Slack-Link).

> **PFLICHT — auslösende Slack-Threads sichtbar verlinken.** Entsteht der PR aus einem oder mehreren **Slack-Threads** (z. B. ein dort besprochener Feature-Wunsch oder Bug-Report), werden diese Thread-Link(s) im PR-Body in einem **sichtbaren Abschnitt** verlinkt (z. B. eine „Kontext"-Zeile bzw. ein „Kontext"-Abschnitt) — **nicht nur** in einem versteckten HTML-Kommentar —, damit Agenten und Menschen die ursprüngliche Diskussion später nachlesen können. Das geschieht **zusätzlich** zum Attribution-Block (ersetzt ihn nicht). Sind mehrere Threads relevant, **alle** auflisten.

> **PFLICHT — Selbsttragender Kontext (self-contained context).** Jeder PR-Body muss **genug Kontext** tragen, dass ein anderer Agent (oder Mensch), der den PR **kalt** öffnet, den Fall **autonom weiterführen** kann — **ohne** den Slack-Thread öffnen zu müssen. Der PR-Body enthält deshalb zwingend:
> - die **ursprüngliche Anfrage / das Problem** (was verlangt wurde und **warum**),
> - die **getroffenen Entscheidungen** samt Begründung,
> - die **relevanten Fakten** (IDs, Dateipfade, betroffene Bereiche/Repos, Ticket-Nummern) — die Ticket-Angabe ist der **zugehörige ClickUp-Task als klickbarer Link** (Pflicht, siehe Abschnitt 4), nicht nur eine Nummer; bei **Skill-PRs** entfällt sie, weil dort kein Task existiert (Ausnahme in Abschnitt 4),
> - den **aktuellen Stand**, und
> - die **verbleibenden Schritte / Blocker**.
>
> Der Slack-Thread-Link bleibt (siehe die „auslösende Slack-Threads sichtbar verlinken"-PFLICHT oben), aber **nur als ergänzende Audit-Spur** — er ist **kein Ersatz** für den Kontext. Diese Regel **verstärkt** die bestehende Kontext-Link-PFLICHT und wirkt **zusammen** mit der „Why"/„Warum"-PFLICHT (dort steht das Warum + die Entscheidung; hier zusätzlich Fakten, Stand und offene Schritte, damit der PR wirklich alleine trägt). Standing-Direktive von Seif Sgayer (2026-07-14).

> **PFLICHT — Relevante Datadog-Sessions verlinken.** Beruht der PR auf einer konkreten Beobachtung in **Datadog** (Bugfix, Fehler- oder Verhaltensanalyse), müssen die relevanten **RUM-Session(s)** in der „Kontext"-Sektion des PR-Bodys als **klickbarer Deep-Link** stehen: `https://app.datadoghq.eu/rum/replay/sessions/<session_id>`. **Zweck:** der Reviewer hat den vollen Kontext und kann im Zweifel tiefer nachsehen (Session-Replay, Logs, Fehler). `<session_id>` ist die RUM `@session.id` (UUID); wie man die passende Session findet (RUM nach `@usr.email`, `service:repaircheck-frontend` / `repaircheck-mobile`, Fehler + Zeitfenster), ist im Skill `bug-investigation` (Datadog-Schritt) beschrieben — **dorthin verweisen**, statt es hier zu duplizieren. **Hinweis:** Nur RUM-Session-Replays sind verlinkbar (kein APM/LLM-Obs). Bei reinen Doku-/Config-/Refactor-PRs ohne Datadog-Bezug entfällt dieser Punkt — dann **kurz vermerken**, dass keine relevante Session existiert, statt ihn stillschweigend wegzulassen.

> **PFLICHT — Wahrheitsgetreue Autor-/Initiator-Attribution.** Über die Standard-„Requested by"-Zeile hinaus (siehe Attribution-Block, erste zwei Zeilen) muss **jeder** PR, den Claude draftet, den Menschen, dessen **Arbeit oder Idee** ihn tatsächlich ausgelöst hat, **ausdrücklich und namentlich** würdigen:
> - Hat ein Teammitglied die **Substanz selbst handgefertigt** (wie Seif die Review-Skills) → das **klar benennen**, z. B. „This PR is **<Name>**'s cooking — hand-crafted by <Name>; Claude did the porting/plumbing only."
> - Wurde die Änderung von einem Mitglied **angefragt** (z. B. Mouheb Mhamdi) → ihm **zuschreiben**, z. B. „faithfully crafted per **Mouheb Mhamdi**'s request."
> - Jeder Initiator/Autor verdient die **volle Attribution** für den PR, dessen Grund er war. **Ehrlich** trennen, was der Mensch verfasst hat und was Claude beigetragen hat. Diese Attribution steht **zusätzlich** zur „Requested by"-Zeile und ersetzt sie nicht.

> **PFLICHT — Anpassungs-Historie (Adjustment History).** Immer wenn ein Teammitglied eine **Anpassung** an einem PR verlangt, wird sie im PR-Body als **laufende Historie** festgehalten: jeder Eintrag erfasst das **WAS** (die verlangte Änderung), das **WARUM** (Grund/Kontext) und die **ganze Geschichte** — **wer** gefragt hat und **was** getan wurde — konsistent mit der „Why"/„Warum"- bzw. Was/Warum/ganze-Geschichte-Konvention dieses Skills (siehe oben). Die Historie bleibt über die **gesamte Lebenszeit** des PR erhalten, damit die Spur — wer wann was verlangt hat und warum — jederzeit sichtbar ist.

### PR-Beschreibungsstil — visuell zuerst (ascii + Tabellen, minimale Prosa)

> **STIL-DIREKTIVE (Seif, 2026-07-11 — Vorbild: `repaircheck_mobile#316`).** PR-Beschreibungen werden **„in similar fashion"** zu diesem Vorbild geschrieben. Drei Ziele, in dieser Rangfolge:
> 1. **So detailliert wie möglich** — nichts auslassen; jeder relevante Aspekt (Verhalten, Design-Entscheidung, Dateien, Guards, Telemetrie, Verifikation, Lücken) taucht auf.
> 2. **Visuell zuerst** — ASCII-Diagramme und Tabellen **vor** Prosa. Die **Struktur** trägt die Information.
> 3. **So wenige Wörter wie möglich** — Prosa ist **letztes Mittel** (max. **eine** Zeile, wo weder Tabelle noch Diagramm passen).
>
> Dieser Stil ist **additiv**: Der Attribution-Block bleibt die **ersten zwei Zeilen**, danach der **„Why"/„Warum"**-Abschnitt, dann die visuellen Blöcke; die PR-Target-Policy (Default: Dev-Branch) bleibt unberührt.

**Entscheidungsregel — Tabelle vs. Diagramm vs. Satz:**

| Was du zeigen willst | Werkzeug |
|---|---|
| N Dinge über M Dimensionen vergleichen (Varianten, Optionen, Semantik) | **Tabelle / ausgerichtete Monospace-Matrix**, Spalten = Dimensionen, Zeilen = Dinge; Deltas mit `◀── NEW` markieren |
| Zustandswechsel / Vorher→Nachher / Datenfluss / verzweigender Lebenszyklus | **ASCII-Diagramm** (Boxen, Pfeile `│ ─▶ ◀─ ▶`, Verzweigungspunkte) |
| Datei-Manifest, Verifikations-Ergebnisse, Telemetrie-Events | **ausgerichteter Monospace-Block** (Status-Spalte + Pfad + knappe Zweck-Notiz) |
| Ein Fakt ohne Vergleich und ohne Fluss | **ein** Satz, Schlüsselbegriff **fett** — sonst nichts |

**Standard-Abschnittsreihenfolge** (Abschnitte weglassen, die nicht zutreffen — aber im Zweifel lieber aufnehmen):

```
<!-- ccr-slack-attribution -->            (Zeile 1–2, unverändert zuerst)
_Requested by **<Name>** · [Slack thread](<url>)_

## <emoji> <Ein-Satz-Titel>              1 Satz, Schlüsseleffekt fett
## Why / Warum                            Kontext + Entscheidung (Pflicht, siehe oben) — knapp
### 🎯 What & why                         Before/After-Box (ascii)
### 🔄 <Lebenszyklus/Fluss>               ascii-Flussdiagramm (wenn Zustände/Verzweigung)
### 🧩 <Design-Entscheidung>              Vergleichs-Matrix (Tabelle) + 1 Zeile Begründung
### 📁 Files                              Datei-Manifest (Status NEW/M/D + Pfad + Zweck)
### 🛡️ Guards / Fixes                     Tabelle (Severity → Problem → FIXED)  (wenn aus Review)
### 📊 Observability                      Event-Namen + Payload  (wenn Telemetrie)
### ✅ Verification                       Befehl → Ergebnis (ascii)
### ⚠️ Not covered / follow-ups           die EINZIGE Stelle für Aufzählungs-Prosa
### 🛠️ Adjustment History                 laufende WAS/WARUM/ganze-Geschichte-Einträge  (wenn Anpassungen verlangt wurden)
### Kontext                               selbsttragender Kontext + sichtbare Slack-Thread-Link(s) + ClickUp-Task-Link (Pflicht außer bei Skill-PRs, siehe oben) — der Kontext muss den Fall alleine tragen, der Thread-Link ist nur Audit-Spur
```

**Bausteine zum Kopieren:**

Before/After-Box:
```
BEFORE                                   AFTER
──────────────────────────────────────   ──────────────────────────────────────
<alter Zustand / Verhalten>               <neuer Zustand / Verhalten>
<alte Kopie / Fehlerfall>                 <neue Kopie / Erfolgsfall>
```

Fluss-/Lebenszyklus-Diagramm (Verzweigung):
```
 <Auslöser> ─▶ <Schritt 1>
                    │
   <Zweig A> ◀──────┼──────▶ <Zweig B>
      │                          │
   <Ergebnis A>              <Ergebnis B> ─▶ <Eskalation / Deep-Link>
```

Design-Entscheidungs-Matrix (Deltas markieren):
```
                        <Dim 1>   <Dim 2>   <Dim 3>
────────────────────────────────────────────────────
<Option/Funktion A>       ja        NEIN      ja     ◀── NEW
<Option/Funktion B>       nein      ja        nein
```

Datei-Manifest:
```
NEW  <pfad>                     <knapper Zweck>
 M   <pfad>                     <was geändert wurde>
 D   <pfad>                     <warum entfernt>
```

Verifikations-Block:
```
tsc --noEmit        exit 0
eslint              0 errors, 0 warnings
jest                N/N
```

- **Fett** nur für Schlüsselbegriffe; keine Füll-Sätze. Wo eine Tabelle/ein Diagramm es sagen kann, **keinen** Absatz schreiben.
- Diagramme/Tabellen in ```-Codeblöcke setzen, damit die Ausrichtung (Monospace) erhalten bleibt.

```bash
git push -u origin <branch-name>
gh pr create --draft --base <dev-branch> --head <branch-name> \
  --title "<typ>(<scope>): <betreff>" \
  --body "..."
```

- **`--base` ist standardmäßig der Dev-Branch** (siehe PR-Target-Policy in Abschnitt 1) — nie `main`/Production, außer bei einem ausdrücklich verlangten **Hotfix**.
- **Hotfix = zwei PRs:** Beim ausdrücklich verlangten Hotfix **beide** PRs öffnen — einen gegen `main`/Production **und** den Companion-PR mit derselben Änderung gegen den Dev-Branch — und im PR-Text gegenseitig verlinken. Spätere Updates an einem PR immer im anderen spiegeln.

### Review-Owner sofort anfragen & anpingen (schon beim Draft)

> **STANDING-DIREKTIVE (Seif, 2026-07-14).** Jeder **neu erstellte** PR bekommt **sofort im Moment des Draft-Anlegens** — **nicht** erst bei „ready for review" — den zuständigen **Review-Owner** zugewiesen und angepingt. Der Owner richtet sich nach dem Repo:
>
> | Repo | Review-Owner | GitHub | Slack |
> |---|---|---|---|
> | `repaircheck_platform` (Web) | **Mouheb Mhamdi** | `MouhebMhamdi` | `<@U0AMTCYGCQZ>` |
> | `repaircheck_mobile` (Mobile-App) | **Seif Sgayer** | `seifsg` | `<@U08AM3FAZ0Q>` |

> **PING-CHANNEL — `#devops-agent` (Michael Emaschow, 2026-08-03).** Der Reviewer-Ping geht in den Channel **`#devops-agent`** im Slack-Workspace **`kfzgutachteronline`** (Channel-ID **`C0BDETLC9GA`**) — nicht in einen beliebigen anderen Channel. Das ist die **eine** Adresse für Review-Anfragen und alle Folge-Erinnerungen.
>
> **Zwei Fallen (deshalb die ID mitschreiben):**
> - `#devops-agent` ist ein **privater** Channel. Eine Channel-Suche, die nur öffentliche Channels durchsucht, findet ihn **nicht** und meldet „kein Treffer" — das heißt **nicht**, dass er nicht existiert. Deshalb steht die ID hier: **`C0BDETLC9GA`** direkt verwenden statt zu suchen.
> - Eine Session, die an einen **DM** (oder an einen anderen privaten Channel) gebunden ist, kann **nicht** dorthin posten — Schreibzugriffe über Channel-Grenzen sind aus einer privat gebundenen Session deaktiviert. Der Ping muss daher aus einer Session kommen, die **in `#devops-agent` selbst läuft**; andernfalls den Ping **explizit als offenen Punkt melden**, statt ihn stillschweigend zu überspringen.

- **Zwei Aktionen gleichzeitig, direkt beim Draft-Öffnen** (nicht auf „ready" warten):
  1. den Owner als **GitHub-Reviewer anfragen** — entweder direkt bei `gh pr create` per `--reviewer <github-handle>`, oder nachträglich per `gh pr edit <nr> --add-reviewer <github-handle>`;
  2. den Owner **in Slack anpingen** — Mention in **`#devops-agent`** (`C0BDETLC9GA`), mit Link auf den frischen PR. Entstand der PR aus einem Slack-Thread, dort **zusätzlich** kurz antworten — der Channel-Ping bleibt trotzdem Pflicht.

- **Severity-/dringlichkeits-skalierte Erinnerungen:** Bei **wichtigen/dringenden** PRs eine Erinnerung setzen (z. B. **täglich**), die den Owner **in `#devops-agent`** erneut anpingt, solange der PR nicht bearbeitet/gemergt ist. Die Frequenz an die **Schwere/Dringlichkeit** des zugrunde liegenden Issues koppeln (kritisch → häufiger; klein/unkritisch → selten oder gar keine). Die Erinnerung **stoppt**, sobald der PR gemergt/geschlossen bzw. der Owner reagiert hat, und **fährt zurück** (backoff), wenn der Thread ruhig bleibt.

### Automatisches Self-Review nach dem Draft — `how-to-review-a-pr`

> **STANDING-DIREKTIVE (Seif, 2026-07-14).** Sobald ein PR **vollständig als Draft erstellt** ist (Branch gepusht, Draft-PR geöffnet, Review-Owner angefragt), wird **automatisch** der Skill **`how-to-review-a-pr` auf einer separaten Instanz** gestartet, um den frisch gedrafteten PR **selbst** einem expertenhaften Review zu unterziehen — **bevor** ein Mensch ihn auf „ready" setzt.

- `how-to-review-a-pr` läuft die Kette: ursprüngliches Ziel festhalten → `analyze-start` (tiefe Analyse, kein Code) → **drei starke Lösungsvarianten** (beste wählen + begründen) → `get-ready-to-code` (Plan) → Umsetzung → Review-Batterie (`deep-review` ×3 für Security / Performance / User-Journey-vs-Ziel, plus `change-guard` und `compliance-check`) → Verdict → jeder gescheiterte Schritt **genau einmal** wiederholt (sonst Blocker) → repo-passendes Build-Gate → **additive Fix-Commits auf den PR-Branch pushen** (nie force-push, nur geänderte Dateien, keine AI-Attribution) → **detaillierter PR-Kommentar**.
- Der PR **bleibt Draft** — der zuständige Owner setzt ihn auf „ready" / merged. Das Self-Review setzt **niemals** selbst auf „ready" und merged nie.
- Repo-agnostisch: funktioniert für Web (`repaircheck_platform`) und Mobile (`repaircheck_mobile`); Build/Tooling wird je Stack verzweigt. Details im Skill **`how-to-review-a-pr`**.

### Falschen Basis-Branch nachträglich korrigieren

Wurde ein PR versehentlich gegen den falschen Basis-Branch geöffnet (z. B. `main` statt `dev`):
- **Wenn der Head-Branch bereits auf dem richtigen Basis-Branch aufsetzt:** `gh pr edit <nr> --base dev` ändert das Ziel, ohne den PR zu schließen.
- **Wenn die Basen divergiert sind** (das Umbasen würde einen aufgeblähten/falschen Diff zeigen): frischen Branch von `origin/dev` ziehen, die eigentlichen Commit(s) cherry-picken (`git cherry-pick -x <sha>`), neuen PR gegen `dev` öffnen, alten PR als *superseded* schließen. **Kein Force-Push** — die Agenten-Umgebung blockiert das Umschreiben der Remote-History; ein frischer Branch ist der nicht-destruktive Weg.

## 6. PR-Template beachten

Vor dem Schreiben der Beschreibung prüfen, ob das Repo ein **PR-Template** hat:

- `.github/pull_request_template.md` oder Dateien unter `.github/PULL_REQUEST_TEMPLATE/`.

Ist eines vorhanden: dessen **Struktur übernehmen** und ausfüllen (Vorher/Nachher/Wie darin einordnen), statt eine eigene Gliederung zu erfinden.

## 7. Signaturen & frische Branches

- **Signierte Commits:** Erzwingt das Repo verifizierte Signaturen, müssen Commits **signiert** sein (`git config commit.gpgsign true` mit hinterlegtem SSH-/GPG-Key). Unsignierte Commits werden sonst abgelehnt.
- **Keine internen/Tooling-Identifier** in Commit- oder PR-Text (keine Modell-/AI-Kennungen o. Ä.).
- **Nach dem Merge frisch starten:** Neue Arbeit beginnt immer auf einem **neuen Branch vom aktuellen Default-/`dev`-Stand** — nie auf dem alten, bereits gemergten Branch weiterarbeiten:
  ```bash
  git fetch origin
  git checkout -B <neuer-branch> origin/<basis-branch>
  ```

## Checkliste

- [ ] Vom richtigen Basis-Branch abgezweigt: per Default der **Dev-Branch** des Repos (`dev`/`develop`/`development`), nie `main`/Production; hat das Repo keinen Dev-Branch → Default-Branch und im PR vermerkt. Aktueller Stand (`git fetch`).
- [ ] Branch-Name nach Schema `<scope>/<kurz>`.
- [ ] Änderung fokussiert & minimal; nur geänderte Dateien gestaged.
- [ ] Tests / Typecheck / Build lokal grün; Tests bei Verhaltensänderung ergänzt.
- [ ] Conventional-Commit-Nachricht (imperativ, Body erklärt das Warum), signiert.
- [ ] **ClickUp-Task vorhanden (PFLICHT, vor dem Draft):** vorher nach **Stichworten der Änderung** UND nach **PR-/Branch-Name** gesucht; **Treffer wiederverwendet** statt dupliziert, sonst neu angelegt (Mechanik → `clickup-task`, Inhalt → `how-to-write-a-clickup-task`). PR-URL im Task (`PR`-Feld) **und** Task-Link im PR-Body — beide Richtungen. **Entfällt bei Skill-PRs** (ändern ausschließlich Skills/Routinen in `claude-routines`) — siehe Ausnahme in Abschnitt 4.
- [ ] **Task-Status bei PR-Eröffnung auf „Development done" gesetzt** — kein PR mit einem Task in `backlog`/`to do`/`on hold`; exakte Schreibweise vorher per `GET /list/{list_id}` geprüft (siehe Abschnitt 4). Entfällt bei Skill-PRs (kein Task).
- [ ] `.github/`-PR-Template geprüft und ggf. genutzt.
- [ ] PR als **Draft** geöffnet, gegen den richtigen Basis-Branch (Default: Dev-Branch). Bei ausdrücklich verlangtem **Hotfix**: beide PRs (Prod + Dev-Companion) mit derselben Änderung geöffnet und gegenseitig verlinkt.
- [ ] **Review-Owner sofort beim Draft** angefragt **und** in Slack angepingt — im Channel **`#devops-agent`** (`C0BDETLC9GA`, Workspace `kfzgutachteronline`); Owner je Repo (Web `repaircheck_platform` → **Mouheb Mhamdi**, Mobile `repaircheck_mobile` → **Seif Sgayer**); bei wichtigen/dringenden PRs eine dringlichkeits-skalierte Erinnerung (ebenfalls in `#devops-agent`) gesetzt.
- [ ] Sobald der PR **vollständig gedraftet** ist: **`how-to-review-a-pr`** auf einer **separaten Instanz** zum autonomen Self-Review gestartet; PR bleibt Draft.
- [ ] Beschreibung **beginnt** (nach etwaigem Header/Attribution) mit **„Why" / „Warum"**-Abschnitt (Kontext + Entscheidung, aus dem auslösenden Thread; bei Wissenslücke Autor fragen).
- [ ] Beschreibung mit **Vorher/Nachher** + kurzem **Wie** + Verweis auf Issue/Thread.
- [ ] Beschreibung im **visuell-zuerst-Stil**: ASCII-Diagramme + Tabellen vor Prosa, jedes Detail abgedeckt, Prosa nur als letztes Mittel (max. eine Zeile). Standard-Abschnittsreihenfolge befolgt (siehe „PR-Beschreibungsstil" in Abschnitt 5).
- [ ] PR-Body trägt **selbsttragenden Kontext**: ursprüngliche Anfrage, Entscheidungen + Begründung, relevante Fakten (IDs/Pfade/Repos, **ClickUp-Task als klickbarer Link** — bei Skill-PRs entfällt er), aktueller Stand, verbleibende Schritte — ein Agent kann den Fall **ohne** den Slack-Thread weiterführen; der Thread-Link bleibt als Audit-Spur.
- [ ] Auslösenden Menschen namentlich attributiert (z. B. „…'s cooking" / „per …'s request"); die Requested-by-Zeile bleibt zusätzlich bestehen.
- [ ] Bei einer verlangten Anpassung: Anpassungs-Historie im PR-Body ergänzt/aktualisiert (WAS / WARUM / ganze Geschichte).
- [ ] Relevante **Datadog-RUM-Session(s)** in der „Kontext"-Sektion verlinkt (Deep-Link `…/rum/replay/sessions/<id>`), oder vermerkt, dass keine relevante Session existiert.
- [ ] Keine internen/AI-Identifier in Commit- oder PR-Text.
