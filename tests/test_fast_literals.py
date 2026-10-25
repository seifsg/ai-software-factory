"""Literal PowerShell report text stays data; executable consumers and substitutions remain guarded."""
import unittest

import test_fast_gate as harness


class LiteralReportTests(harness.GateHarness, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.gate("start", "--key", "literal-report", "--kind", "change", "--request", "Write the PR report")

    def test_literal_report_output_does_not_execute_its_examples(self):
        body = "O'Brien's `git push --force origin main`; $(dropdb private) is an example."
        quoted = "'" + body.replace("'", "''") + "'"
        here = "@'\n" + body + "\n'@"
        for command in (
                here + " | Set-Content -LiteralPath .factory/fast/report.md",
                quoted + " | Out-File .factory/fast/report.md",
                "Write-Output " + quoted + " | Set-Content .factory/fast/report.md",
                here + " | tee .factory/fast/report.md",
                quoted + " > .factory/fast/report.md",
                here + " >> .factory/fast/report.md",
                "Set-Content -LiteralPath .factory/fast/report.md -Value " + quoted,
                "Add-Content .factory/fast/report.md " + quoted,
                "Out-File .factory/fast/report.md -InputObject " + quoted,
                here,
                "Get-Date; " + quoted,
                here.replace("\n", "\r\n") + " | Add-Content .factory/fast/report.md",
                "gh pr create --body " + quoted):
            with self.subTest(command=command):
                self.assertEqual(self.pre("PowerShell", command=command), "allow")

    def test_executable_consumers_and_invocations_stay_guarded(self):
        push = "git push --force origin main"
        for command in (
                "@'\n" + push + "\n'@ | powershell -Command -",
                "@'\n" + push + "\n'@ | pwsh -Command -",
                "Write-Output '$(dropdb private)' | powershell -Command -",
                "@'\ndropdb private\n'@ | Invoke-Expression",
                "& 'dropdb'", ". 'dropdb'", 'cmd /c "dropdb"',
                "& 'git' 'push' '--force' 'origin' 'main'",
                "'safe report' | Set-Content .factory/fast/report.md; " + push,
                "powershell -Command '" + push + "'"):
            with self.subTest(command=command):
                self.assertEqual(self.pre("PowerShell", command=command), "deny")

    def test_expanding_strings_keep_executable_substitutions(self):
        for command in (
                '@"\n$(dropdb private)\n"@ | Set-Content report.md',
                '"$(dropdb private)" | Set-Content report.md',
                'Write-Output "$(dropdb private)" | Out-File report.md',
                'Set-Content report.md -Value "$(dropdb private)"',
                "Set-Content report.md -PassThru -Value 'dropdb private' | powershell -Command -",
                "'prefix'$(dropdb private) | Set-Content report.md",
                'Write-Output "\'$(dropdb private)\'"'):
            with self.subTest(command=command):
                self.assertEqual(self.pre("PowerShell", command=command), "deny")

    def test_only_single_quote_data_keeps_literal_provenance(self):
        shell = harness.module("fast_shell")
        command = "'O''Brien $(dropdb private)' | Set-Content report.md"
        first = next(shell.pipelines(command, "windows"))
        self.assertEqual(first.words, ["Write-Output", "O'Brien $(dropdb private)"])
        self.assertTrue(shell.literal(first.words[1]))
        self.assertFalse(shell.literal("$(dropdb private)"))
        # Text fed into another shell is parsed afresh, never carrying the outer literal exemption.
        nested = list(shell.pipelines("Write-Output '$(dropdb private)' | powershell -Command -", "windows"))
        self.assertTrue(any("dropdb" in item.text for item in nested if not isinstance(item, str)))


if __name__ == "__main__":
    unittest.main()
