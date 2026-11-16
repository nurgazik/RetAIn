import SwiftUI

/// Every stat the server works out for a word (D74), as a plain list at the end of its card, so the founder
/// can see real numbers before the stats screens are designed. Labels say what each number counts.
struct WordStatsView: View {
    let wordId: Int
    @State private var stats: WordStats?
    @State private var failed = false

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Word stats").font(.headline)
            if let s = stats {
                ForEach(rows(s), id: \.0) { label, value in
                    HStack(alignment: .firstTextBaseline) {
                        Text(label).foregroundStyle(.secondary)
                        Spacer(minLength: 12)
                        Text(value).multilineTextAlignment(.trailing)
                    }
                    .font(.footnote)
                    Divider()
                }
            } else if failed {
                Text("Couldn't load stats.").font(.footnote).foregroundStyle(.secondary)
            } else {
                ProgressView()
            }
        }
        .accessibilityIdentifier("word-stats")
        .task(id: wordId) {
            do { stats = try await RetAInClient.shared.wordStats(wordId) } catch { failed = true }
        }
    }

    /// (label, value) in reading order: exposure, recall, practice, timeline, look-ups.
    nonisolated func rows(_ s: WordStats) -> [(String, String)] {
        let dash = "—"
        func list(_ d: [String: Int]) -> String { d.sorted { $0.key < $1.key }.map { "\($0.value) \($0.key)" }.joined(separator: ", ") }
        var r: [(String, String)] = [
            ("Added", s.added),
            ("Box", "\(s.box) of 4"),
            ("Shown in reading", "\(s.shown.reader)"),
            ("Shown in practice", "\(s.shown.practice)"),
            ("Placed in reads (engine)", "\(s.placedInReads)"),
            ("Taps in reading", "\(s.taps)"),
            ("Tap rate", s.tapRate.map { "\(Int(($0 * 100).rounded()))%" } ?? dash),
            ("Lapses", "\(s.lapses)"),
        ]
        for (kind, counts) in s.answers.sorted(by: { $0.key < $1.key }) {
            r.append(("Answers: \(kind)", list(counts)))
        }
        for (kind, f) in s.firstTry.sorted(by: { $0.key < $1.key }) {
            r.append(("First try clean: \(kind)", "\(f.clean) of \(f.tries)"))
        }
        r += [
            ("Confused with", s.confusedWith.isEmpty ? dash : s.confusedWith.map { "\($0.answer) ×\($0.times)" }.joined(separator: ", ")),
            ("Hints", s.fillDays == 0 ? dash : "\(s.hintDays) of \(s.fillDays) fill-in days"),
            ("Median time", s.medianSeconds.isEmpty ? dash
                : s.medianSeconds.sorted { $0.key < $1.key }.map { "\($0.key) \(Int($0.value.rounded())) s" }.joined(separator: ", ")),
            ("Sentence verdicts", s.sentences.isEmpty ? dash : s.sentences.map { $0.verdict ?? "?" }.joined(separator: " → ")),
            ("First practised", s.firstPractised ?? dash),
            ("Last practised", s.lastPractised ?? dash),
            ("Last seen", s.lastSeen.map { d in "\(d)" + (s.daysSinceSeen.map { " (\($0) days ago)" } ?? "") } ?? dash),
            ("Retained on", s.retainedOn ?? dash),
            ("Days to retain", s.daysToRetain.map(String.init) ?? dash),
            ("Times relearned", "\(s.timesRelearned)"),
            ("Card opens", "\(s.cardOpens)"),
            ("Pronunciation plays", "\(s.listens)"),
            ("Read in", s.readIn.isEmpty ? dash : s.readIn.map { $0.title ?? $0.pieceId }.joined(separator: "\n")),
            ("Changes", s.changes.map { "\($0.day) \($0.kind)" }.joined(separator: "\n")),
            ("Answer history", s.history.isEmpty ? dash : s.history.suffix(15).map { a in
                let box = a.boxBefore.map { " · box \($0)→\(a.boxAfter.map(String.init) ?? "?")" } ?? ""
                return "\(a.day) \(a.kind) \(a.result)\(box)"
            }.joined(separator: "\n")),
        ]
        return r
    }
}
